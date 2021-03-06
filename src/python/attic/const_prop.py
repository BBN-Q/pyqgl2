#!/usr/bin/env python3

# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import ast

from ast import NodeVisitor
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

class MutableValue(object):
    """
    A degenerate class whose purpose is to serve as a sentinel;
    it can never appear in a valid QGL2 or QGL program, and therefore
    it can be used to mark values that are outside the domain of any
    constant in a QGL2 or QGL program: a constant can never have a
    value that is an instance of MutableValue.
    """

    def __init__(self):
        pass


class FindConstants(NodeVisitor):

    def __init__(self, node):

        self.root = node

        # map from name to value for constants
        #
        # The first time we see a name, we assess whether it might
        # be a constant or might be mutable.  If mutable, we give
        # it the special value of MutableValue().  Each time we
        # encounter the name again, we update our assessment.
        # If the name survives until the end of the process
        # with a single immutable value, then consider it a constant.
        #
        # Note that Python makes it challenging to identify
        # immutable values.  There are many sneaky ways to change
        # bindings.
        #
        self.constants = dict()

        self.find_constants()

    def find_constants(self):

        self.constants = dict()
        self.visit(node)

        # Remove any names that don't appear to be bound to
        # constants
        #
        # iterate over a copy of the keys of the constants table,
        # so we can do surgery on the table without breaking the
        # iteration
        #
        for item in list(self.constants.keys()):
            if isinstance(self.constants[item], MutableValue):
                del self.constants[item]

        return self.constants

    def visit_Assign(self, node):

        # FIXME: can't handle nested tuples properly
        # For now we're not even going to try.

        if not isinstance(node.targets[0], ast.Name):
            NodeError.warning_msg(node, 'tuple returns not supported yet')
            self.generic_visit(node)
            return

        target = node.targets[0]

        print('CP target0: %s' % ast.dump(target))

        value = node.value
        name = target.id

        # TODO: what if the lval is an array or dict expression?
        # Need to sort out what's referenced by the lval.

        if isinstance(value, ast.Str):
            print('CP looks like a str assignment %s' % ast.dump(node))
        elif isinstance(value, ast.Num):
            print('CP looks like a num assignment %s' % ast.dump(node))
        elif isinstance(value, ast.List):
            print('CP looks like a list assignment %s' % ast.dump(node))

        elif isinstance(value, ast.Call):
            print('CP looks like a call assignment %s' % ast.dump(node))

        self.generic_visit(node)

    def visit_For(self, node):
        """
        Discover loop variables.

        TODO: this is incomplete; we just assume that loop variables
        are all classical.  We don't attempt to infer anything about the
        iterator.
        """

        for subnode in ast.walk(node.target):
            if isinstance(subnode, ast.Attribute):
                # This is a fatal error and we don't want to confuse
                # ourselves by trying to process the ast.Name
                # nodes beneath
                #
                name_text = pyqgl2.importer.collapse_name(subnode)
                NodeError.fatal_msg(subnode,
                        ('loop var [%s] is not local' % name_text))

            elif isinstance(subnode, ast.Name):
                name = subnode.id

                # Warn the user if they're doing something that's
                # likely to provoke an error
                #
                if self.name_is_in_lscope(name):
                    NodeError.warning_msg(subnode,
                            ('loop var [%s] hides sym in outer scope' % 
                                name))

                print('FOR %s' % name)
                self.constants[name] = MutableValue()

        self.visit_body(node.body)
        self.visit_body(node.orelse)

    def visit_ExceptHandler(self, node):
        name = node.name
        if name in self.constants:
            self.constants[name] = MutableValue()
        pass

    def visit_With(self, node):
        """
        TODO: this is incomplete; we just assume that with-as variables
        are all classical.  We don't attempt to infer anything about their
        type.  (This is likely to be true in most cases, however)
        """

        for item in node.items:
            if not item.optional_vars:
                continue

            for subnode in ast.walk(item.optional_vars):
                if isinstance(subnode, ast.Attribute):
                    # This is a fatal error and we don't want to confuse
                    # ourselves by trying to process the ast.Name
                    # nodes beneath
                    #
                    name_text = pyqgl2.importer.collapse_name(subnode)
                    NodeError.fatal_msg(subnode,
                            ('with-as var [%s] is not local' % name_text))

                elif isinstance(subnode, ast.Name):
                    name = subnode.id

                    print('GOT WITH %s' % name)

                    # Warn the user if they're doing something that's
                    # likely to provoke an error
                    #
                    if self.name_is_in_lscope(name):
                        NodeError.warn_msg(subnode,
                                ('with-as var [%s] hides sym in outer scope' % 
                                    name))
                    self.add_type_binding(subnode, subnode.id, QGL2.CLASSICAL)

        self.visit_body(node.body)



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

        print('XX qbit_scope %s %s' % (str(self._qbit_scope()), ast.dump(node)))
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

        print('XX qbit_scope %s %s' % (str(self._qbit_scope()), ast.dump(node)))

        if isinstance(value, ast.Name):
            # print('CHECKING %s' % str(self._qbit_scope()))
            if (value.id + ':qbit') in self._qbit_scope():
                self.warning_msg(node,
                        'aliasing qbit parameter \'%s\' as \'%s\'' %
                        (value.id, target.id))
                self._extend_local(target.id)
            elif value.id in self._qbit_local():
                self.warning_msg(node,
                        'aliasing local qbit \'%s\' as \'%s\'' %
                        (value.id, target.id))
                self._extend_local(target.id)

        elif isinstance(value, ast.Call):
            func_name = pyqgl2.importer.collapse_name(value.func)
            func_def = self.importer.resolve_sym(value.qgl_fname, func_name)

            # If we can't find the function definition, or it's not declared
            # to be QGL, then we can't handle it.  Return immediately.
            #
            if not func_def:
                NodeError.error_msg(
                        value, 'function [%s] not defined' % func_name)
                return node

            if func_def.returns:
                rtype = func_def.returns
                if (isinstance(rtype, ast.Name) and rtype.id == QGL2.QBIT):
                    # Not sure what happens if we get here: we might
                    # have a wandering variable that we know is a qbit,
                    # but we never know which one.
                    #
                    print('XX EXTENDING LOCAL (%s)' % target.id)
                    self._extend_local(target.id)
                    target.qgl_is_qbit = True

            if not func_def.qgl_func:
                # TODO: this seems bogus.  We should be able to call
                # out to non-QGL functions
                #
                NodeError.error_msg(
                        value, 'function [%s] not declared to be QGL2' %
                            func_name)
                return node

            print('NNN lookup [%s] got %s' % (func_name, str(func_def)))
            print('NNN FuncDef %s' % ast.dump(func_def))
            print('NNN CALL [%s]' % func_name)

            # When we're figuring out whether something is a call to
            # the Qbit assignment function, we look at the name of the
            # function as it is defined (i.e, as func_def), not as it
            # is imported (i.e., as func_name).
            #
            # This makes the assumption that ANYTHING named 'Qubit'
            # is a Qbit assignment function, which is lame and should
            # be more carefully parameterized.  Things to think about:
            # looking more deeply at its signature and making certain
            # that it looks like the 'right' function and not something
            # someone mistakenly named 'Qubit' in an unrelated context.
            #
            if isinstance(value, ast.Call) and (func_def.name == QGL2.QBIT_ALLOC):
                self._extend_local(target.id)
                print('XX EXTENDED to include %s %s' %
                        (target.id, str(self._qbit_local())))

        return node

    def visit_Assign(self, node):

        # We only do singleton assignments, not tuples,
        # and not expressions
        #
        # TODO: fix this to handle arbitrary assignments

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

        item = node.items[0]
        print('WITH %s' % ast.dump(node))
        if (not isinstance(item.context_expr, ast.Name) or
                (item.context_expr.id != QGL2.QCONCUR)):
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
        qbits_referenced = self.check_conflicts(node)
        print('qbits in concur block (line: %d): %s' % (
                node.lineno, str(qbits_referenced)))

        """
        # TO BE REPLACED
        for ind in range(len(body)):
            stmnt = body[ind]
            find_waveforms = FindWaveforms()
            find_waveforms.generic_visit(stmnt)

            for waveform in find_waveforms.seq:
                print('concur %d: WAVEFORM: %s' % (stmnt.lineno, waveform))
        """

        return node

    def check_conflicts(self, node):

        all_seen = set()

        for refs in self.qbit_sets.values():
            if not refs.isdisjoint(all_seen):
                conflict = refs.intersection(all_seen)
                NodeError.error_msg(node,
                        '%s appear in multiple concurrent statements' %
                        str(', '.join(list(conflict))))

            all_seen.update(refs)

        return all_seen

class FindQbitReferences(ast.NodeTransformer):
    """
    Find all the references to qbits in a node

    Assumes that all qbits are referenced by variables that
    have been marked as being qbits rather than arbitrary expressions

    For example, if you do something like

        qbit1 = Qubit("1") # Create a new qbit; qbit1 is marked
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
        print('XXY ')

        if node.id in self.qbit_refs:
            print('XX GOT qbit already %s' % node.id)
            node.qgl_is_qbit = True
        elif hasattr(node, 'qgl_is_qbit') and node.qgl_is_qbit:
            print('XX GOT qbit %s' % node.id)
            self.qbit_refs.add(node.id)
        else:
            print('XX NOT qbit %s' % node.id)

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

        wav_check = CheckWaveforms(type_check.func_defs, importer)
        nptree3 = wav_check.visit(nptree2)

        if NodeError.MAX_ERR_LEVEL >= NodeError.NODE_ERROR_ERROR:
            print('bailing out 3')
            sys.exit(1)

    def new_lscope(fname):

        importer = NameSpaces(fname)
        ptree = importer.qglmain
        print(ast.dump(ptree))

        zz_def = importer.resolve_sym(ptree.qgl_fname, 'zz')

        main_scope = FindTypes.find_lscope(importer, ptree, None)
        # zz_scope = FindTypes.find_lscope(importer, zz_def, main_scope)


    new_lscope(sys.argv[1])
    preprocess(sys.argv[1])
