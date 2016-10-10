# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# See get_sequence_function (the main entrypoint), and
# for a sample usage, see main.py.

import ast
import os
import sys

from copy import deepcopy

from pyqgl2.ast_qgl2 import is_seq, is_with_label
from pyqgl2.ast_util import ast2str, NodeError
from pyqgl2.find_channels import find_all_channels
from pyqgl2.find_labels import getChanLabel
from pyqgl2.importer import collapse_name
from pyqgl2.lang import QGL2

class SequenceExtractor(object):
    """
    Create QGL1 code from a modified AST

    This class has the logic to take the input QGL2 AST as modified by the compiler,
    and produce a QGL1 function reference suitable for execution.

    Note: this assumes that the AST is for one function
    definition that has already been inlined, successfully
    flattened, grouped, and sequenced already.
    """

    def __init__(self, importer):

        self.importer = importer

        self.qbits = set()  # from find_all_channels
        self.qbit_creates = list() # of sym_name, use_name, node tuples
        self.sequences = dict() # From channel to list of pulses

        # the imports we need to make in order to satisfy the stubs
        #
        # the key is the name of the module (i.e. something like
        # 'QGL.PulsePrimitives') and the values are sets of import
        # clauses (i.e. 'foo' or 'foo as bar')
        #
        self.stub_imports = dict()

    def is_qbit_create(self, node):
        """
        If the node does not represent a qbit creation and assignment,
        return False.  Otherwise, return a triple (sym_name, use_name,
        node) where sym_name is the symbolic name, use_name is the
        name used by the preprocessor to substitute for this qbit
        reference, and node is the node parameter (i.e. the root
        of the ast for the assignment.

        There are several sloppy assumptions here.
        """

        if not isinstance(node, ast.Assign):
            return False

        # Only handles simple assignments; not tuples
        # TODO: handle tuples
        if len(node.targets) != 1:
            return False

        if not isinstance(node.value, ast.Call):
            return False

        if not isinstance(node.value.func, ast.Name):
            return False

        # This is the old name, and needs to be updated
        # TODO: update to new name/signature
        if node.value.func.id != QGL2.QBIT_ALLOC and \
           node.value.func.id != QGL2.QBIT_ALLOC2:
            return False

        chanLabel = getChanLabel(node)
        if not chanLabel:
            NodeError.warning_msg(node, 'failed to find chanLabel')

        # HACK FIXME: assumes old-style Qbit allocation
        sym_name = node.targets[0].id
        use_name = 'QBIT_%s' % chanLabel
        return (sym_name, use_name, node)

    def find_imports(self, node):
        '''Fill in self.stub_imports with all the per module imports needed'''

        default_namespace = node.qgl_fname

        for subnode in ast.walk(node):
            if (isinstance(subnode, ast.Call) and
                    isinstance(subnode.func, ast.Name)):
                funcname = subnode.func.id

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

    def find_sequences(self, node):
        '''
        Input AST node is the main function definition.
        Use is_qbit_create to get qbit creation statements,
        and walk the AST to find sequence elements to create the sequences
        on the object.'''

        if not isinstance(node, ast.FunctionDef):
            NodeError.fatal_msg(node, 'not a function definition')
            return False

        self.qbits = find_all_channels(node)

        if len(self.qbits) == 0:
            NodeError.error_msg(node, 'no channels found')
            return False
        else:
            NodeError.diag_msg(node, "Found channels %s" % self.qbits)

        lineNo = -1
        while lineNo+1 < len(node.body):
            lineNo += 1
            # print("Line %d of %d" % (lineNo+1, len(node.body)))
            stmnt = node.body[lineNo]
            # print("Looking at stmnt %s" % stmnt)
            assignment = self.is_qbit_create(stmnt)
            if assignment:
                self.qbit_creates.append(assignment)
                continue
            elif is_with_label(stmnt, 'grouped'):
                # print("Found concur at line %d: %s" % (lineNo+1,stmnt))
                for s in stmnt.body:
                    if is_seq(s):
                        chan_name = '_'.join(sorted(s.qgl_chan_list))

                        # print("Found with seq for qbits %s: %s" % (s.qgl_chan_list, ast2str(s)))
                        #print("With seq next at line %d: %s" % (lineNo+1,s))
                        if chan_name not in self.sequences:
                            self.sequences[chan_name] = list()
                        thisSeq = self.sequences[chan_name]
                        # print("Append body %s" % s.body)
                        # for s2 in s.body:
                        #     print(ast2str(s2))
                        thisSeq += s.body
                        #print("lineNo now %d" % lineNo)
                    else:
                        NodeError.error_msg(s, "Not seq next at line %d: %s" % (lineNo+1,s))
            elif isinstance(stmnt, ast.Expr):
                if len(self.qbits) == 1:
                    # print("Append expr %s to sequence for %s" % (ast2str(stmnt), self.qbits))
                    if len(self.sequences) == 0:
                        self.sequences[list(self.qbits)[0]] = list()
                    self.sequences[list(self.qbits)[0]].append(stmnt)
                else:
                    chan_list = list(find_all_channels(stmnt))
                    if len(chan_list) != 1:
                        NodeError.error_msg(stmnt,
                                            'orphan expression %s' % ast.dump(stmnt))
                    if len(self.sequences) == 0 or str(chan_list) not in self.sequences:
                        self.sequences[str(chan_list)] = list()
                    thisSeq = self.sequences[str(chan_list)]
                    thisSeq.append(stmnt)
                    # print("Added %s to seq for %s" % (ast2str(stmnt), chan_list))
                    # print("Have sequences: %s" % (self.sequences.keys()))
            else:
                chan_list = list(find_all_channels(stmnt))
                if len(chan_list) != 1:
                    NodeError.error_msg(stmnt,
                                        'orphan statement %s' % ast.dump(stmnt))
                if len(self.sequences) == 0 or str(chan_list) not in self.sequences:
                    self.sequences[str(chan_list)] = list()
                thisSeq = self.sequences[str(chan_list)]
                thisSeq.append(stmnt)
                # print("Added %s to seq for %s" % (ast2str(stmnt), chan_list))

        # print("Seqs: %s" % self.sequences)
        if not self.sequences:
            NodeError.warning_msg(node, "No per Qubit operations discovered")
            return False
        # FIXME: Is this a requirement?
        # if not self.qbit_creates:
        #     NodeError.error_msg(node, "No qbit creation statements found")
        #     return False
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
#        base_imports = """    from QGL.PulseSequencePlotter import plot_pulse_files
#"""
        base_imports = ''

        found_imports = ('\n' + indent).join(self.create_imports_list())

        # allow QBIT parameters to be overridden
        #
        preamble = 'def %s():\n' % func_name
        preamble += base_imports
        preamble += indent + found_imports
        preamble += '\n\n'

        # FIXME: In below block, calls to ast2str are the slowest part
        # (78%) of calling get_sequence_function. Fixable?

        for (_sym_name, _use_name, node) in self.qbit_creates:
            preamble += indent + ast2str(node).strip() + '\n'

        if setup:
            for setup_stmnt in setup:
                preamble += indent + ('%s\n' % ast2str(setup_stmnt).strip())

        seqs_def = indent + 'seqs = list()\n'
        seqs_str = ''
        seq_strs = list()

        for chan_name in sorted(self.sequences.keys()):
            seq = self.sequences[chan_name]

            #print("Looking at seq %s" % seq)
            sequence = [ast2str(item).strip() for item in seq]
            #print ("It is %s" % sequence)
            # TODO: check that this is always OK.
            #
            # HACK ALERT: this might not always be the right thing to do
            # but right now extraneous calls to Sync at the start of
            # program appear to cause a problem, and they don't serve
            # any known purpose, so skip them.
            #
            while sequence[0] == 'Sync()':
                sequence = sequence[1:]

            # TODO there must be a more elegant way to indent this properly
            seq_str = indent + ('seq_%s = [\n' % chan_name) + 2 * indent
            seq_str += (',\n' + 2 * indent).join(sequence)
            seq_str += '\n' + indent + ']\n'
            seq_str += indent + 'seqs += [seq_%s]\n' % chan_name
            seq_strs.append(seq_str)

        for seq_str in seq_strs:
            seqs_str += seq_str

        postamble = indent + 'return seqs\n'

        res =  preamble + seqs_def + seqs_str + postamble
        return res

def get_sequence_function(node, func_name, importer,
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

    builder = SequenceExtractor(importer)

    if builder.find_sequences(node) and builder.find_imports(node):
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
    else:
        NodeError.warning_msg(
                node, 'no per-Qubit sequences discovered')
        return None
