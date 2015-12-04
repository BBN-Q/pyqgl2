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

    def assign_simple(self, node):

        target = node.targets[0]
        value = node.value

        if not isinstance(target, ast.Name):
            return node

        if target.id in self._qbit_local():
            msg = 'reassignment of qbit \'%s\' forbidden' % target.id
            self.error_msg(node, msg)
            return node

        if (target.id + ':qbit') in self._qbit_scope():
            msg = 'reassignment of qbit parameter \'%s\' forbidden' % target.id
            self.error_msg(node, msg)
            return node

        func_name = pyqgl2.importer.collapse_name(value.func)
        func_def = self.importer.resolve_sym(value.qgl_fname, func_name)

        # If we can't find the function definition, or it's not declared
        # to be QGL, then we can't handle it.  Return immediately.
        #
        if not func_def:
            NodeError.error_msg(
                    value, 'function [%s] not defined' % func_name)
            return node
        elif not func_def.qgl_func:
            NodeError.error_msg(
                    value, 'function [%s] not declared to be QGL2' % func_name)
            return node

        print('NNN lookup [%s] got %s' % (func_name, str(func_def)))

        print('NNN FuncDef %s' % ast.dump(func_def))

        if isinstance(value, ast.Call):
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

        if isinstance(node.targets[0], ast.Name):
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
        self.namespace = None # must be set later

    def set_namespace(self, namespace):
        self.namespace = namespace

    def visit_Call(self, node):

        # This is just a sketch

        # find the name of the function being called,
        # and then resolve it in the context of the local
        # namespace, and see if it returns a pulse
        #
        localname = node.func.id
        localfilename = node.qgl_fname

        if self.namespace.returns_pulse(localfilename, localname):
            print('GOT PULSE [%s:%s]' % (localfilename, localname))

        return node


class FindConcurBlocks(ast.NodeTransformer):

    LEVEL = 0

    def __init__(self, *args, **kwargs):
        super(FindConcurBlocks, self).__init__(*args, **kwargs)

        self.concur_stmnts = set()
        self.qbit_sets = dict()

    def visit_With(self, node):
        if (not isinstance(node.context_expr, ast.Name) or
                (node.context_expr.id != QGL2.QCONCUR)):
            return node


        if self.LEVEL > 0:
            # need to fix this so we can squash multiple levels of concurs
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

    from pyqgl2.importer import NameSpaces

    def preprocess(fname):

        importer = NameSpaces(fname)
        ptree = importer.path2ast[importer.base_fname]

        type_check = CheckType(fname, importer=importer)

        nptree = type_check.visit(ptree)

        for func_def in sorted(type_check.func_defs.keys()):
            types, node = type_check.func_defs[func_def]
            call_list = node.qgl_call_list

        if NodeError.MAX_ERR_LEVEL >= NodeError.NODE_ERROR_ERROR:
            print('bailing out 1')
            sys.exit(1)

        sym_check = CheckSymtab(fname, type_check.func_defs, importer)
        nptree2 = sym_check.visit(nptree)

        if NodeError.MAX_ERR_LEVEL >= NodeError.NODE_ERROR_ERROR:
            print('bailing out 2')
            sys.exit(1)

        wav_check = CheckWaveforms(fname, type_check.func_defs)
        nptree3 = wav_check.visit(nptree2)

        if NodeError.MAX_ERR_LEVEL >= NodeError.NODE_ERROR_ERROR:
            print('bailing out 3')
            sys.exit(1)

    preprocess(sys.argv[1])
