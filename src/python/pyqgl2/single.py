# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import ast
import os
import sys

from copy import deepcopy

from pyqgl2.ast_util import ast2str, NodeError
from pyqgl2.concur_unroll import is_concur, is_seq, find_all_channels
from pyqgl2.importer import collapse_name
from pyqgl2.lang import QGL2
from pyqgl2.substitute import getChanLabel

class SingleSequence(object):
    """
    Create a sequence list for a single QBIT

    Note: this assumes that the AST is for one function
    definition that has already been inlined, successfully
    flattened, grouped, and sequenced already.
    """

    def __init__(self, importer):

        self.importer = importer

        self.qbits = set()
        self.qbit_creates = list()
        self.sequence = list()

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
        if node.value.func.id != QGL2.QBIT_ALLOC:
            return False

        chanLabel = getChanLabel(node)
        if not chanLabel:
            NodeError.warning_msg(node, 'failed to find chanLabel')

        # HACK FIXME: assumes old-style Qbit allocation
        sym_name = node.targets[0].id
        use_name = 'QBIT_%s' % chanLabel
        return (sym_name, use_name, node)

    def find_imports(self, node):

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

                fdef = self.importer.resolve_sym(namespace, funcname)
                if not fdef:
                    NodeError.error_msg(subnode,
                            'cannot find import info for [%s]' % funcname)
                elif not fdef.qgl_stub_import:
                    NodeError.error_msg(subnode,
                            'not a stub: [%s]' % funcname)
                else:
                    # print('FI AST %s' % ast.dump(fdef))
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

        import_list = list()

        for module_name in sorted(self.stub_imports.keys()):
            for sym_name in sorted(self.stub_imports[module_name]):
                import_list.append(
                        'from %s import %s' % (module_name, sym_name))

        return import_list

    def find_sequence(self, node):

        if not isinstance(node, ast.FunctionDef):
            NodeError.fatal_msg(node, 'not a function definition')
            return False

        self.qbits = find_all_channels(node)

        if len(self.qbits) == 0:
            NodeError.error_msg(node, 'no channels found')
            return False
        elif len(self.qbits) > 1:
            NodeError.error_msg(node, 'more than one channel found')
            return False

        for stmnt in node.body:
            assignment = self.is_qbit_create(stmnt)
            if assignment:
                self.qbit_creates.append(assignment)
                continue
            elif is_concur(stmnt):
                if is_seq(stmnt.body[0]):
                    self.sequence += stmnt.body[0].body
                else:
                    NodeError.diag_msg(stmnt.body[0], 'expected seq?')
            elif isinstance(stmnt, ast.Expr):
                self.sequence.append(stmnt)
            else:
                NodeError.error_msg(stmnt, 'orphan statement')

        return True

    def emit_function(self, func_name='qgl1_main'):
        """
        Create a function that, when run, creates the context
        in which the sequence is evaluated, and evaluate it.

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
        # that this method is using / might use
        # Here we include the imports matching stuff in qgl2.qgl1.py
        # Can we perhaps annotate all the stubs with the proper
        # import statement and use that to figure out what to include here?
        base_imports = """    from QGL.Compiler import compile_to_hardware
    from QGL.PulseSequencePlotter import plot_pulse_files
"""

        found_imports = ('\n' + indent).join(self.create_imports_list())

        # allow QBIT parameters to be overridden
        #
        preamble = 'def %s(**kwargs):\n' % func_name
        preamble += base_imports
        preamble += indent + found_imports
        preamble += '\n\n'

        for (sym_name, _use_name, node) in self.qbit_creates:
            preamble += indent + 'if \'' + sym_name + '\' in kwargs:\n'
            preamble += (2 * indent) + sym_name
            preamble += ' = kwargs[\'%s\']\n' % sym_name
            preamble += indent + 'else:\n'
            preamble += (2 * indent) + ast2str(node).strip() + '\n'

        for (sym_name, use_name, _node) in self.qbit_creates:
            preamble += indent + '%s = %s\n' % (use_name, sym_name)

        sequence = [ast2str(item).strip() for item in self.sequence]

        # TODO there must be a more elegant way to indent this properly
        seq_str = indent + 'seq = [\n' + 2 * indent
        seq_str += (',\n' + 2 * indent).join(sequence)
        seq_str += '\n' + indent + ']\n'

        # That was a single sequence. We want a list of sequences
        # FIXME: Really, we want a new sequence every time the source code used Init()
        seqs_str = indent + 'seqs = [seq]\n'

        postamble = indent + 'return seqs\n'

        res =  preamble + seq_str + seqs_str + postamble
        return res

def single_sequence(node, func_name, importer):
    """
    Create a function that encapsulates the QGL code (for a single
    sequence) from the given AST node, which is presumed to already
    be fully pre-processed.

    TODO: we don't test that the node is fully pre-processed.
    TODO: each step of the preprocessor should mark the nodes
    so that we know whether or not they've been processed.
    """

    builder = SingleSequence(importer)

    if builder.find_sequence(node) and builder.find_imports(node):
        code = builder.emit_function(func_name)

        NodeError.diag_msg(
                node, 'generated code:\n#start\n%s\n#end code' % code)

        # TODO: we might want to pass in elements of the local scope
        scratch_scope = dict()
        eval(compile(code, '<none>', mode='exec'), globals(), scratch_scope)

        return scratch_scope[func_name]
    else:
        NodeError.fatal_msg(
                node, 'find_sequence failed: not a single sequence')
        return None

