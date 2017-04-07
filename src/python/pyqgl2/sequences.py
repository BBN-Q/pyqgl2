# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# See get_sequence_function (the main entrypoint), and
# for a sample usage, see main.py.

import ast
import os
import sys

from pyqgl2.ast_util import ast2str, NodeError
from pyqgl2.quickcopy import quickcopy
from pyqgl2.qreg import is_qbit_create

class SequenceExtractor(object):
    """
    Create QGL1 code from a modified AST

    This class has the logic to take the input QGL2 AST as modified by the compiler,
    and produce a QGL1 function reference suitable for execution.

    Note: this assumes that the AST is for one function
    definition that has already been inlined, successfully
    flattened, grouped, and sequenced already.
    """

    def __init__(self, importer, allocated_qregs):

        self.importer = importer
        self.allocated_qregs = allocated_qregs

        self.qbits = set()
        self.qbit_creates = list() # expressions that create Qubits
        self.sequence = []

        # the imports we need to make in order to satisfy the stubs
        #
        # the key is the name of the module (i.e. something like
        # 'QGL.PulsePrimitives') and the values are sets of import
        # clauses (i.e. 'foo' or 'foo as bar')
        #
        self.stub_imports = dict()

    def find_imports(self, node):
        '''Fill in self.stub_imports with all the per module imports needed'''

        default_namespace = node.qgl_fname

        for subnode in ast.walk(node):
            if (isinstance(subnode, ast.Call) and
                    isinstance(subnode.func, ast.Name)):
                funcname = subnode.func.id

                # QRegister calls will be stripped by find_sequences, so skip
                if funcname == 'QRegister':
                    continue

                # If we created a node without an qgl_fname,
                # then use the default namespace instead.
                # FIXME: This is a hack, but it will work for now.
                #
                if not hasattr(subnode, 'qgl_fname'):
                    namespace = default_namespace
                else:
                    namespace = subnode.qgl_fname

                if hasattr(subnode, 'qgl_implicit_import'):
                    (sym_name, module_name, orig_name) = \
                            subnode.qgl_implicit_import
                else:
                    fdef = self.importer.resolve_sym(namespace, funcname)

                    if not fdef:
                        NodeError.error_msg(subnode,
                                'cannot find import info for [%s]' % funcname)
                        return False
                    elif not fdef.qgl_stub_import:
                        NodeError.error_msg(subnode,
                                'not a stub: [%s]' % funcname)
                        return False

                    (sym_name, module_name, orig_name) = fdef.qgl_stub_import

                if orig_name:
                    import_str = '%s as %s' % (orig_name, sym_name)
                else:
                    import_str = sym_name

                if module_name not in self.stub_imports:
                    self.stub_imports[module_name] = set()

                self.stub_imports[module_name].add(import_str)

        return True

    def create_imports_list(self):
        '''Using the stub_imports created by find_imports,
        create a list of import statement strings to include in the function.'''

        import_list = list()

        for module_name in sorted(self.stub_imports.keys()):
            for sym_name in sorted(self.stub_imports[module_name]):
                import_list.append(
                        'from %s import %s' % (module_name, sym_name))

        return import_list

    def qbits_from_qregs(self, allocated_qregs):
        qbits = set()
        for qreg in allocated_qregs.values():
            qbits.update(qreg.qubits)
        return qbits

    def expand_qreg_call(self, node):
        new_stmnts = []
        for ct, arg in enumerate(node.value.args):
            if isinstance(arg, ast.Name) and arg.id in self.allocated_qregs:
                qreg = self.allocated_qregs[arg.id]
                for n in range(len(qreg)):
                    stmnt = quickcopy(node)
                    stmnt.value.args[ct].id = qreg.use_name(n)
                    new_stmnts.append(stmnt)
            elif (isinstance(arg, ast.Subscript) and
                    arg.value.id in self.allocated_qregs):
                qreg = self.allocated_qregs[arg.value.id]
                if not isinstance(arg.slice.value, ast.Num):
                    NodeError(node,
                        "Non-literal slice of a QRegister [%s]" % ast2str(node))
                n = arg.slice.value.n
                stmnt = quickcopy(node)
                stmnt.value.args[ct] = ast.Name(id=qreg.use_name(n),
                                                ctx=ast.Load())
                new_stmnts.append(stmnt)
        return new_stmnts

    def find_sequences(self, node):
        '''
        Input AST node is the main function definition.
        Strips out QRegister creation statements and builds
        a list of corresponding Qubit creation statements.
        Converts calls on QRegisters into calls on Qubits.'''

        if not isinstance(node, ast.FunctionDef):
            NodeError.fatal_msg(node, 'not a function definition')
            return False

        self.qbits = self.qbits_from_qregs(self.allocated_qregs)
        for q in self.qbits:
            stmnt = ast.parse("QBIT_{0} = QubitFactory('q{0}')".format(q))
            self.qbit_creates.append(stmnt)

        lineNo = -1
        while lineNo+1 < len(node.body):
            lineNo += 1
            # print("Line %d of %d" % (lineNo+1, len(node.body)))
            stmnt = node.body[lineNo]
            # print("Looking at stmnt %s" % stmnt)
            if is_qbit_create(stmnt):
                # drop it
                continue

            elif isinstance(stmnt, ast.Expr):
                # expand calls on QRegisters into calls on Qubits
                if (hasattr(stmnt, 'qgl2_type') and
                        (stmnt.qgl2_type == 'stub' or stmnt.qgl2_type == 'measurement')):
                    new_stmnts = self.expand_qreg_call(stmnt)
                    self.sequence.extend(new_stmnts)
                else:
                    self.sequence.append(stmnt)
            else:
                NodeError.error_msg(stmnt,
                                    'orphan statement %s' % ast.dump(stmnt))

        # print("Seqs: %s" % self.sequences)
        if not self.sequence:
            NodeError.warning_msg(node, "No qubit operations discovered")
            return False

        return True

    def emit_function(self, func_name='qgl1_main', setup=None):
        """
        Create a function that, when run, creates the context
        in which the sequence is evaluated, and evaluate it.

        Assumes find_imports and find_sequences have already
        been called.

        func_name is the name for the function, if provided.
        I'm not certain that the name has any significance
        or whether this function will be, for all practical
        purposes, a lambda.
        """

        # assumes a standard 4-space indent; if the surrounding
        # context uses some other indentation scheme, the interpreter
        # may gripe, and pep8 certainly will
        #
        indent = '    '

        # FIXME: Ugliness
        # In the proper namespace we need to import all the QGL1 functions
        # that this method is using / might use.
        # Here we include the imports matching stuff in qgl2.qgl1.py
        # as required by create_imports_list(), plus
        # extras as required.

        base_imports = indent + 'from QGL import QubitFactory\n'

        found_imports = ('\n' + indent).join(self.create_imports_list())

        # define the method preamble
        preamble = 'def %s():\n' % func_name
        preamble += base_imports
        preamble += indent + found_imports
        preamble += '\n\n'

        # FIXME: In below block, calls to ast2str are the slowest part
        # (78%) of calling get_sequence_function. Fixable?

        for node in self.qbit_creates:
            preamble += indent + ast2str(node).strip() + '\n'

        if setup:
            for setup_stmnt in setup:
                preamble += indent + ('%s\n' % ast2str(setup_stmnt).strip())

        sequence = [ast2str(item).strip() for item in self.sequence]

        # TODO there must be a more elegant way to indent this properly
        seq_str = indent + 'seq = [\n' + 2 * indent
        seq_str += (',\n' + 2 * indent).join(sequence)
        seq_str += '\n' + indent + ']\n'

        postamble = indent + 'return seq\n'

        res =  preamble + seq_str + postamble
        return res

def get_sequence_function(node, func_name, importer, allocated_qregs,
        intermediate_fout=None, saveOutput=False, filename=None,
        setup=None):
    """
    Create a function that encapsulates the QGL code
    from the given AST node, which is presumed to already
    be fully pre-processed.

    TODO: we don't test that the node is fully pre-processed.
    TODO: each step of the preprocessor should mark the nodes
    so that we know whether or not they've been processed.
    """

    builder = SequenceExtractor(importer, allocated_qregs)

    builder.find_sequences(node)
    builder.find_imports(node)
    code = builder.emit_function(func_name, setup)
    if intermediate_fout:
        print(('#start function\n%s\n#end function' % code),
              file=intermediate_fout, flush=True)
    if saveOutput and filename:
        newf = os.path.abspath(filename[:-3] + "qgl1.py")
        with open(newf, 'w') as compiledFile:
            compiledFile.write(code)
        print("Saved compiled code to %s" % newf)

    NodeError.diag_msg(
            node, 'generated code:\n#start\n%s\n#end code' % code)

    # TODO: we might want to pass in elements of the local scope
    scratch_scope = dict()
    eval(compile(code, '<none>', mode='exec'), globals(), scratch_scope)
    NodeError.halt_on_error()

    return scratch_scope[func_name]
