#!/usr/bin/env python3

# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import ast

from copy import deepcopy

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

import pyqgl2.importer

from pyqgl2.ast_util import NodeError
from pyqgl2.ast_util import NodeTransformerWithFname
from pyqgl2.ast_util import NodeVisitorWithFname
from pyqgl2.check_symtab import CheckSymtab
from pyqgl2.check_waveforms import CheckWaveforms
from pyqgl2.lang import QGL2

class FuncParam(object):

    def __init__(self, name):
        self.name = name
        self.value = None

class QuantumFuncParam(FuncParam):
    pass

class ClassicalFuncParam(FuncParam):
    pass

class CheckType(NodeTransformerWithFname):

    def __init__(self, fname, importer=None):
        super(CheckType, self).__init__()

        # for each qbit, track where it is created
        #
        # the key is the qbit number, and the val is the name
        # and where it's created
        #
        self.qbit_origins = dict()

        # a list of scope tuples: (name, qbit?, context)
        #
        # We begin with the global scope, initially empty
        #
        self.scope = list(list())
        self.local = list(list())

        self.func_defs = dict()

        self.func_level = 0

        self.waveforms = dict()

        # Reference to the main function, if any
        #
        self.qglmain = None

        self.qgl_call_stack = list()

        self.importer = importer

    def _push_scope(self, qbit_scope):
        self.scope.append(qbit_scope)

    def _pop_scope(self):
        self.scope = self.scope[:-1]

    def _qbit_scope(self):
        return self.scope[-1]

    def _extend_scope(self, name):
        self.scope[-1].append(name)

    def _push_local(self, qbit_local):
        self.local.append(qbit_local)

    def _pop_local(self):
        self.local = self.local[:-1]

    def _qbit_local(self):
        return self.local[-1]

    def _extend_local(self, name):
        self.local[-1].append(name)

    def _qbit_decl(self, node):

        q_args = list()
        q_return = None

        if type(node) != ast.FunctionDef:
            return None

        if node.returns:
            ret = node.returns

            # It would be nice to be able to return a qbit
            # tuple, maybe.
            #
            if ((type(ret) == ast.Str) and (ret.s == 'qbit')):
                q_return = 'qbit'
            elif ((type(ret) == ast.Str) and (ret.s == 'classical')):
                q_return = 'classical'

            # The symbols 'qbit' and 'classical' are deprecated
            # because they are not valid Python3, but I haven't
            # decided whether to remove them yet
            #
            elif ((type(ret) == ast.Name) and (ret.id == 'qbit')):
                self.warning_msg(node,
                        'use of \'qbit\' symbol is deprecated')
                q_return = 'qbit'
            elif ((type(ret) == ast.Name) and (ret.id == 'classical')):
                self.warning_msg(node,
                        'use of \'classical\' symbol is deprecated')
                q_return = 'classical'

            else:
                # There are other annotations; we treat them all as
                # classical.  (we used to treat them as errors)
                #
                # self.error_msg(node,
                #         'unsupported return annotation [%s]' % ast.dump(ret))
                q_return = 'classical'

        if node.args.args:
            for arg in node.args.args:
                # print('>> %s' % ast.dump(arg))

                name = arg.arg
                annotation = arg.annotation
                if not annotation:
                    q_args.append('%s:classical' % name)
                    continue

                print('ANNO %s' % ast.dump(annotation))

                if type(annotation) == ast.Name:
                    if annotation.id == 'qbit':
                        q_args.append('%s:qbit' % name)
                    elif annotation.id == 'classical':
                        q_args.append('%s:classical' % name)
                    else:
                        self.error_msg(node,
                                'unsupported parameter annotation [%s]' %
                                annotation.id)
                elif type(annotation) == ast.Str:
                    if annotation.s == 'qbit':
                        q_args.append('%s:qbit' % name)
                    elif annotation.s == 'classical':
                        q_args.append('%s:classical' % name)
                    else:
                        self.error_msg(node,
                                'unsupported parameter annotation [%s]' %
                                annotation.s)
                else:
                    self.error_msg(node,
                            'unsupported parameter annotation [%s]' %
                            ast.dump(annotation))

        node.q_args = q_args
        node.q_return = q_return

        return q_args

    def assign_simple(self, node):

        target = node.targets[0]
        value = node.value

        if type(target) != ast.Name:
            return node

        # print('AS SCOPE %s' % str(self._qbit_scope()))

        if target.id in self._qbit_local():
            msg = 'reassignment of qbit \'%s\' forbidden' % target.id
            self.error_msg(node,
                    ('reassignment of local qbit \'%s\' forbidden' %
                        target.id))
            return node

        if (target.id + ':qbit') in self._qbit_scope():
            self.error_msg(node,
                    ('reassignment of qbit parameter \'%s\' forbidden' %
                        target.id))
            return node

        print('NNN RHS %s' % ast.dump(value))
        print('NNN Collapse [%s]' % pyqgl2.importer.collapse_name(value.func))

        func_name = pyqgl2.importer.collapse_name(value.func)
        func_def = self.importer.resolve_sym(value.qgl_fname, func_name)

        print('NNN FuncDef %s' % ast.dump(func_def))

        if type(value) == ast.Call:
            print('NNN CALL [%s]' % func_name)

        # When we're figuring out whether something is a call to
        # the Qbit assignment function, we look at the name of the
        # function as it is defined (i.e, as func_def), not as it
        # is imported (i.e., as func_name).
        #
        # This makes the assumption that ANYTHING named 'Qbit'
        # is a Qbit assignment function, which is lame and should
        # be more carefully parameterized.  Things to think about:
        # looking more deeply at its signature and making certain
        # that it looks like the 'right' function and not something
        # someone mistakenly named 'Qbit' in an unrelated context.
        #
        if isinstance(value, ast.Call) and (func_def.name == 'Qbit'):
            self._extend_local(target.id)
        elif isinstance(value, ast.Name):
            # print('CHECKING %s' % str(self._qbit_scope()))
            if (value.id + ':qbit') in self._qbit_scope():
                self.warning_msg(node,
                        'aliasing qbit parameter \'%s\' as \'%s\'' %
                        (value.id, target.id))
            elif value.id in self._qbit_local():
                self.warning_msg(node,
                        'aliasing local qbit \'%s\' as \'%s\'' %
                        (value.id, target.id))
            self._extend_local(target.id)
        else:
            return node

        # print('qbit scope %s' % str(self._qbit_scope()))

        return node

    def visit_Assign(self, node):

        # We only do singleton assignments, not tuples,
        # and not expressions

        if type(node.targets[0]) == ast.Name:
            self.assign_simple(node)

        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node):

        # print('>>> %s' % ast.dump(node))

        # Initialize the called functions list for this
        # definition, and then push this context onto
        # the call stack.  The call stack is a stack of
        # call lists, with the top of the stack being
        # the current function at the top and bottom
        # of each function definition.
        #
        # We do this for all functions, not just QGL functions,
        # because we might want to be able to analyze non-QGL
        # functions
        #
        self.qgl_call_stack.append(list())

        qglmain = False
        qglfunc = False
        other_decorator = False

        if node.decorator_list:
            for dec in node.decorator_list:

                # qglmain implies qglfunc, but it's permitted to
                # have both
                #
                if (type(dec) == ast.Name) and (dec.id == QGL2.QMAIN):
                    qglmain = True
                    qglfunc = True
                elif (type(dec) == ast.Name) and (dec.id == QGL2.QDECL):
                    qglfunc = True
                else:
                    other_decorator = True

            if qglmain and other_decorator:
                self.error_msg(node,
                        'unrecognized decorator with %s' % QGL2.QMAIN)
            elif qglfunc and other_decorator:
                self.error_msg(node,
                        'unrecognized decorator with %s' % QGL2.QDECL)

        if qglmain:
            if self.qglmain:
                omain = self.qglmain
                self.error_msg(node, 'more than one %s function' % QGL2.QMAIN)
                self.error_msg(node,
                        'previously defined %s:%d:%d' %
                        (omain.fname, omain.lineno, omain.col_offset))
                self._pop_scope()
                self.qgl_call_stack.pop()
                return node
            else:
                self.diag_msg(node,
                        '%s declared as %s' % (node.name, QGL2.QMAIN))
                self.qglmain = node

        if self.func_level > 0:
            self.error_msg(node, '%s functions cannot be nested' % QGL2.QDECL)

        # So far so good: now actually begin to process this node

        if hasattr(node, 'qgl_args'):
            decls = node.qgl_args
        else:
            decls = list()

        # diagnostic only
        self.diag_msg(
                node, '%s declares qbits %s' % (node.name, str(decls)))
        self._push_scope(decls)
        self._push_local(list())

        self.func_level += 1
        self.generic_visit(node)
        self.func_level -= 1

        # make a copy of this node and its qbit scope

        node.qgl_call_list = self.qgl_call_stack.pop()

        # print('DECLS: %s %s' % (node.name, str(decls)))
        self.func_defs[node.name] = (decls, deepcopy(node))

        self._pop_scope()
        self._pop_local()

        self.diag_msg(node,
                'call list %s: %s' %
                (node.name, str(', '.join([
                    pyqgl2.importer.collapse_name(call.func)
                        for call in node.qgl_call_list]))))
        return node

    def visit_Call(self, node):

        # We can only check functions referenced by name, not arbitrary
        # expressions that return a function
        #
        # The way that we test whether something is referenced purely
        # by name is clunky: we try to collapse reference the AST for
        # the function reference back to a name, and if that works,
        # then we think it's a name.
        #

        if not pyqgl2.importer.collapse_name(node.func):
            self.error_msg(node, 'function not referenced by name')
            return node

        node.qgl_scope = self._qbit_scope()[:]
        node.qgl_local = self._qbit_local()[:]

        self.qgl_call_stack[-1].append(node)

        return node

class CompileQGLFunctions(ast.NodeTransformer):

    LEVEL = 0

    def __init__(self, *args, **kwargs):
        super(CompileQGLFunctions, self).__init__(*args, **kwargs)

        self.concur_finder = FindConcurBlocks()

    def visit_FunctionDef(self, node):
        qglmain = False
        qglfunc = False
        other_decorator = False

        # print('>>> %s' % ast.dump(node))

        if node.decorator_list:
            # print('HAS DECO')
            for dec in node.decorator_list:
                # print('HAS DECO %s' % str(dec))

                # qglmain implies qglfunc, but it's permitted to
                # have both
                #
                if (type(dec) == ast.Name) and (dec.id == QGL2.QMAIN):
                    qglmain = True
                    qglfunc = True
                elif (type(dec) == ast.Name) and (dec.id == QGL2.QDECL):
                    qglfunc = True
                else:
                    other_decorator = True

            if qglmain and other_decorator:
                self.error_msg(node,
                        'unrecognized decorator with %s' % QGL2.QMAIN)
            elif qglfunc and other_decorator:
                self.error_msg(node,
                        'unrecognized decorator with %s' % QGL2.QDECL)

        if not qglfunc:
            return node

        if qglmain:
            print('%s detected' % QGL2.QDECL)
            if self.qglmain:
                omain = self.qglmain
                self.error_msg(node, 'more than one %s function' % QGL2.QMAIN)
                self.error_msg(node,
                        'previous %s %s:%d:%d' %
                        (QGL2.QMAIN,
                            omain.fname, omain.lineno, omain.col_offset))
                return node
            else:
                node.fname = self.fname
                self.qglmain = node

        if self.LEVEL > 0:
            self.error_msg(node, 'QGL mode functions cannot be nested')

        self.LEVEL += 1
        # check for nested qglfunc functions
        self.generic_visit(node)
        self.LEVEL -= 1

        # First, find and check all the concur blocks

        body = node.body
        for ind in range(len(body)):
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
        for ind in range(len(body)):
            stmnt = body[ind]
            find_ref = FindQbitReferences()
            find_ref.generic_visit(stmnt)
            self.qbit_sets[ind] = find_ref.qbit_refs

            self.visit(stmnt)

        self.LEVEL -= 1

        # check_conflicts will halt the program if it detects an error
        #
        qbits_referenced = self.check_conflicts(node.lineno)
        print('qbits in concur block (line: %d): %s' % (
                node.lineno, str(qbits_referenced)))

        for ind in range(len(body)):
            stmnt = body[ind]
            find_waveforms = FindWaveforms()
            find_waveforms.generic_visit(stmnt)

            for waveform in find_waveforms.seq:
                print('concur %d: WAVEFORM: %s' % (stmnt.lineno, waveform))

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

    from pyqgl2.importer import Importer

    def preprocess(fname):

        importer = Importer(fname)
        ptree = importer.path2ast[importer.base_fname]

        type_check = CheckType(fname)

        nptree = type_check.visit(ptree)

        for func_def in sorted(type_check.func_defs.keys()):
            types, node = type_check.func_defs[func_def]
            call_list = node.qgl_call_list

        if type_check.max_err_level >= NodeError.NODE_ERROR_ERROR:
            print('bailing out 1')
            sys.exit(1)

        sym_check = CheckSymtab(fname, type_check.func_defs)
        nptree2 = sym_check.visit(nptree)

        if sym_check.max_err_level >= NodeError.NODE_ERROR_ERROR:
            print('bailing out 2')
            sys.exit(1)

        wav_check = CheckWaveforms(fname, type_check.func_defs)
        nptree3 = sym_check.visit(nptree2)

        if wav_check.max_err_level >= NodeError.NODE_ERROR_ERROR:
            print('bailing out 3')
            sys.exit(1)

    preprocess(sys.argv[1])
