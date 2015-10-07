# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import ast

# For testing only
if __name__ == '__main__':
    import os
    import sys

    # Find the directory that this executable lives in;
    # munge the path to look within the parent module
    #
    DIRNAME = os.path.normpath(
            os.path.abspath(os.path.dirname(sys.argv[0]) or '.')) 
    sys.path.append(os.path.normpath(os.path.join(DIRNAME, '..')))

from pyqgl2.ast_util import NodeTransformerWithFname
from pyqgl2.ast_util import NodeVisitorWithFname

# This is just a smattering of possible waveforms.
# (I'm not sure whether these are even correct, or
# meaningful, but they're good enough for test cases)
#
UNI_WAVEFORMS = set(['MEAS', 'Y90', 'Y180', 'X90', 'X180', 'Z90', 'Z180'])

# Like UNI_WAVEFORMS, BI_OPS is fictitious
# 
BI_OPS = set(['SWAP'])

class CheckType(NodeTransformerWithFname):

    def __init__(self, fname):
        super(CheckType, self).__init__(fname)

        # for each qbit, track where it is created
        #
        # the key is the qbit number, and the val is the name
        # and where it's created
        #
        self.qbit_origins = dict()

        # a list of scope tuples: (name, qbit?, context)
        #
        self.scope = list()

        self.class_defs = dict()

        self.func_level = 0

    def _push_scope(self, qbit_scope):
        self.scope.append(qbit_scope)

    def _pop_scope(self):
        self.scope = self.scope[:-1]

    def _curr_scope(self):
        return self.scope[-1]

    def _extend_scope(self, name):
        self.scope[-1].append(name)

    @staticmethod
    def _qbit_decl(node):

        if type(node) != ast.FunctionDef:
            return None

        if not node.decorator_list:
            return None

        decls = None
        for dec in node.decorator_list:
            if (type(dec) == ast.Call) and (dec.func.id == 'qtypes'):
                decls = dec.args
                break

        if not decls:
            return None

        params = list()

        for decl in decls:
            if type(decl) == ast.Str:
                params.append(decl.s)
            elif type(decl) == ast.Tuple:
                params.append(decl.elts[0].s)

        return params

    def assign_simple(self, node):

        target = node.targets[0]
        value = node.value

        if type(target) != ast.Name:
            return node

        if target.id in self._curr_scope():
            msg = 'reassignment of qbit \'%s\' forbidden' % target.id
            print msg
            self.error_msg(node,
                    ('reassignment of qbit \'%s\' forbidden' % target.id))

        if (type(value) == ast.Call) and (value.func.id == 'Qbit'):
            self._extend_scope(target.id)
        elif (type(value) == ast.Name) and value.id in self._curr_scope():
            self.warning_msg(node, 'alias of qbit \'%s\' as \'%s\'' %
                    (value.id, target.id))
            self._extend_scope(target.id)
        else:
            return node

        print 'new scope %s' % str(self._curr_scope())

        return node

    def visit_Assign(self, node):

        # We only do singleton assignments, not tuples,
        # and not expressions

        if type(node.targets[0]) == ast.Name:
            self.assign_simple(node)

        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node):
        decls = self._qbit_decl(node)
        if decls is not None:
            # diagnostic only
            print 'DECL: %s qbits %s' % (node.name, str(decls))
            self._push_scope(decls)
            self.func_level += 1
            self.generic_visit(node)
            self.func_level -= 1
            self._pop_scope()

        return node

    def visit_Call(self, node):

        # We can only check functions referenced by name, not arbitrary
        # expressions that return a function
        #
        if type(node.func) != ast.Name:
            self.warning_msg(node, 'function not referenced by name')
            return node

        func_name = node.func.id

        def check_arg(arg, argpos):
            if type(arg) != ast.Name:
                self.error_msg(node, '%s param to %s must be a symbol' %
                        (argpos, func_name))
                return False

            if arg.id not in self._curr_scope():
                self.error_msg(node, '%s param to %s must be a qbit' %
                        (argpos, func_name))
                return False

            return True

        if func_name in UNI_WAVEFORMS:
            if len(node.args) < 1:
                self.error_msg(node,
                        '%s requires a qbit parameter' % func_name)
                return node

            first_arg = node.args[0]
            check_arg(first_arg, 'first')

        elif func_name in BI_OPS:
            if len(node.args) < 2:
                self.error_msg(node,
                        '%s requires two qbit parameters' % func_name)
                return node

            arg1 = node.args[0]
            arg2 = node.args[1]

            check_arg(arg1, 'first')
            check_arg(arg2, 'second')

        return node

class CompileQGLFunctions(ast.NodeTransformer):

    LEVEL = 0

    def __init__(self, *args, **kwargs):
        super(CompileQGLFunctions, self).__init__(*args, **kwargs)

        self.concur_finder = FindConcurBlocks()

    def visit_FunctionDef(self, node):
        qglmode = False
        found_other = False

        print '>>> %s' % ast.dump(node)

        if node.decorator_list:
            for dec in node.decorator_list:
                if (type(dec) == ast.Name) and (dec.id == 'qglmode'):
                    qglmode = True
                elif (type(dec) == ast.Call) and (dec.func.id == 'qtypes'):
                    print 'yahoo'
                else:
                    found_other = True

            if qglmode and found_other:
                self.error_msg(node, 'qtypes must be the sole decorator')

        if not qglmode:
            return node

        if self.LEVEL > 0:
            self.error_msg(node, 'QGL mode functions cannot be nested')

        self.LEVEL += 1
        # check for nested qglmode functions
        self.generic_visit(node)
        self.LEVEL -= 1

        # First, find and check all the concur blocks

        body = node.body
        for ind in xrange(len(body)):
            stmnt = body[ind]
            body[ind] = self.concur_finder.visit(stmnt)

class FindWaveforms(ast.NodeTransformer):

    def __init__(self, *args, **kwargs):
        super(FindWaveforms, self).__init__(*args, **kwargs)

        self.seq = list()

    def visit_Call(self, node):

        # This is just a sketch

        if node.func.id == 'MEAS':
            self.seq.append('MEAS ' + ast.dump(node))
        elif node.func.id == 'X90':
            self.seq.append('X90 ' + ast.dump(node))
        elif node.func.id == 'Y90':
            self.seq.append('Y90 ' + ast.dump(node))

        return node


class FindConcurBlocks(ast.NodeTransformer):

    LEVEL = 0

    def __init__(self, *args, **kwargs):
        super(FindConcurBlocks, self).__init__(*args, **kwargs)

        self.concur_stmnts = set()
        self.qbit_sets = dict()

    def visit_With(self, node):
        if ((type(node.context_expr) != ast.Name) or
                (node.context_expr.id != 'concur')):
            return node

        if self.LEVEL > 0:
            self.error_msg(node, 'nested concur blocks are not supported')

        self.LEVEL += 1

        body = node.body
        for ind in xrange(len(body)):
            stmnt = body[ind]
            find_ref = FindQbitReferences()
            find_ref.generic_visit(stmnt)
            self.qbit_sets[ind] = find_ref.qbit_refs

            self.visit(stmnt)

        self.LEVEL -= 1

        # check_conflicts will halt the program if it detects an error
        #
        qbits_referenced = self.check_conflicts(node.lineno)
        print 'qbits in concur block (line: %d): %s' % (
                node.lineno, str(qbits_referenced))

        for ind in xrange(len(body)):
            stmnt = body[ind]
            find_waveforms = FindWaveforms()
            find_waveforms.generic_visit(stmnt)

            for waveform in find_waveforms.seq:
                print 'concur %d: WAVEFORM: %s' % (stmnt.lineno, waveform)

    def check_conflicts(self, lineno):

        all_seen = set()

        for refs in self.qbit_sets.values():
            if not refs.isdisjoint(all_seen):
                conflict = refs.intersection(all_seen)
                self.error_msg(node,
                        '%s appear in multiple concurrent statements' %
                        str(', '.join(list(conflict))))

            all_seen.update(refs)

        return all_seen

class FindQbitReferences(ast.NodeTransformer):
    """
    Find all the references to qbits in a node

    Assumes that all qbits are referenced by variables with
    names that start with 'qbit', rather than arbitrary expressions

    For example, if you do something like

        arr[ind] = qbit1
        foo = arr[ind]

    Then "qbit1" will be detected as a reference to a qbit,
    but "arr[ind]" or "foo" will not, even though all three
    expressions evaluate to a reference to the same qbit.
    """

    def __init__(self, *args, **kwargs):
        super(FindQbitReferences, self).__init__(*args, **kwargs)

        self.qbit_refs = set()

    def visit_Name(self, node):
        if node.id.startswith('qbit'):
            self.qbit_refs.add(node.id)

        return node

if __name__ == '__main__':
    import sys

    def preprocess(fname):

        text = open(fname, 'r').read()

        ptree = ast.parse(text, mode='exec')
        nptree = CheckType(fname).visit(ptree)

    preprocess(sys.argv[1])
