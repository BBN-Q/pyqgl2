#!/usr/bin/env python3

# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved.

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

class FuncParam(object):

    def __init__(self, name):
        self.name = name
        self.value = None

class QuantumFuncParam(FuncParam):
    pass

class ClassicalFuncParam(FuncParam):
    pass

class FindTypes(NodeVisitor):
    """
    Mechanism for finding the type bindings of variables
    within the context of a function invocation.

    Because Python functions do not have (enforced) type
    signatures, the type bindings of two different invocations
    of the same function may be different.  For example, if
    we have function:

    def foo(x):
        y = x
        return y

    Then if we call "foo(12)" then the local variable y within
    foo will have a type of int, but if we call "foo('hello')"
    then y will have a type of str.  For this reason, we do
    not try to do type inference on functions when they are
    initially parsed, but instead defer this until we know
    how they will be called.  For the same reason, the type
    bindings are not stored with the function definitions,
    but instead must be computed for each call (or stored
    in some other way).

    Because Python functions may be difficult/impossible to
    analyze with respect to type (and we might not have access
    to their source), there are many circumstances in which
    we cannot infer anything useful about variables types.
    Fortunately, we only really care about whether variables
    are quantum, classical, or have an unknown type (which
    we assume is some sort of classical type).

    Along the way, we also check whether type declarations
    are violated.  For example, if we had:

    def bar(x: qbit):
        pass # do something

    and we invoked this as "bar(13)", this would contradict
    the declared type because 13 is not a qbit.

    We assume that variables do not change types (at least
    not with respect to classical vs quantum) so the following
    code would be considered an error:

    x = Qbit(1)     # x is a reference to a qbit
    x = 14          # reassigning x to a classical value--error!

    We also treat the reassignment of references to quantum
    values as errors:

    x = Qbit(1)     # x is a reference to a qbit
    x = Qbit(2)     # reassignment of x--error!

    There are several ways that variables come into existance:
    explicit assignment, implicit assignment (keyword arguments),
    as statement variable (loop variables, exception variables,
    or with variables).

    TODO: we do not handle "local" and "global" statements yet.

    Each variable has one of the following types: 'classical',
    'qbit', or 'unknown'.  There will be more types in the future.
    """

    def __init__(self, importer):

        self.importer = importer

        # dictionaries of all local symbols (parameters or locally-created
        # variables).
        #
        self.parameter_names = dict()
        self.local_names = dict()

    @staticmethod
    def find_lscope(importer, func_def, call=None, call_scope=None):

        worker = FindTypes(importer)

        val_bindings, type_bindings = worker.process_params(
                func_def, call=call, call_scope=call_scope)

        worker.parameter_names = type_bindings

        worker.visit(func_def)

        name = func_def.name
        print('%s PARAM: %s' % (name, str(worker.parameter_names)))
        print('%s LOCAL: %s' % (name, str(worker.local_names)))

        return worker

    def process_params(self, func_def, call=None, call_scope=None):

        # The formal parameters are an AST object.
        # The way they are represented is a little awkward;
        # all parameters (positional and keyword) are in a
        # positional list (because Python can handle keyword
        # parameters as positional parameters) and then the
        # keyword default values are in a separate positional
        # list.)

        type_bindings = dict()
        val_bindings = dict()
        all_arg_names = list()

        # First, pretend all the parameters are positional
        #
        for arg in func_def.args.args:
            arg_name = arg.arg
            arg_type = arg.annotation
            if arg_type and isinstance(arg_type, ast.Name):
                arg_type_name = arg_type.id
            else:
                arg_type_name = 'unknown'

            if arg_name in all_arg_names:
                NodeError.error_msg(arg,
                        'repeated parameter name \'%s\'' % arg_name)

#            if arg_type_name not in [QGL2.CLASSICAL, QGL2.QBIT, 'unknown', QGL2.CONTROL, QGL2.PULSE, QGL2.SEQUENCE, QGL2.QBIT_LIST]:
            if arg_type_name not in [QGL2.CLASSICAL, QGL2.QBIT, 'unknown']:
                NodeError.warning_msg(arg,
                        ('parameter type \'%s\' is not supported' %
                            arg_type_name))

            all_arg_names.append(arg_name)

            type_bindings[arg_name] = arg_type_name
            val_bindings[arg_name] = None

        # Then process any defaults that were provided
        #
        default_vals = func_def.args.defaults
        if default_vals:
            default_names = all_arg_names[:-len(default_vals)]
            
            for ind in range(len(default_vals)):
                val_bindings[default_names[ind]] = default_vals[ind]

                # TODO: we need to make sure that the default
                # values actually match the declared type, if any
                #
                # NOTE that the default value is an AST, which could be
                # almost any expression.  Many expressions are going to
                # be a headache for us, so maybe we should disallow
                # many of them.

        # Now replace the default values with whatever is in the
        # actuals, if any actuals are provided.

        if call:
            seen_args = set()
            print('CALL %s' % ast.dump(call))
            if call.args:
                for ind in range(len(call.args)):
                    seen_args.add(all_arg_names[ind])
                    val_bindings[all_arg_names[ind]] = call.args[ind]

            # TODO: If there were fewer args than required, then
            # gripe. TODO: if there were unexpected arguments, gripe

            for kwarg in call.keywords:
                name = kwarg.arg

                if name in seen_args:
                    NodeError(call,
                            'more than one value for parameter \'%s\'' % name)

                seen_args.add(name)
                val_bindings[name] = kwarg.value

            print('CALL %s' % str(val_bindings))

        # TODO: if provided a surrounding scope and a call, then try to
        # infer types from actual parameters.  For example, if one of
        # the actual parameters is 'x', and we know the type of 'x', then
        # propogate it.
        #
        # Right now we don't try to statically determine values.
        #
        #
        # TODO: this is incomplete

        if call and call_scope:

            # Create a dictionary of known types from the given
            # call_scope.  Note that we are only interested in
            # known types, so omit any "unknown" types
            #
            scope_types = dict()
            for name in call_scope.parameter_names:
                name_type = call_scope.parameter_names[name]
                if name_type != 'unknown':
                    scope_types[name] = name_type

            for name in call_scope.local_names:
                name_type = call_scope.local_names[name]
                if name_type != 'unknown':
                    scope_types[name] = name_type

            # Now look at each actual parameter, and try
            # to infer what type it has.  If it's a number or
            # string, it's classical.  If it's the value of
            # a variable, look in scope_types to see what we
            # know about that variable (if anything).  If it's
            # a method call, look at the definition of the
            # method to see whether it has a declared type.
            #
            for name in type_bindings:
                actual_val = val_bindings[name]

                if isinstance(actual_val, ast.Num):
                    type_bindings[name] = QGL2.CLASSICAL

                elif isinstance(actual_val, ast.Str):
                    type_bindings[name] = QGL2.CLASSICAL

                elif isinstance(actual_val, ast.NameConstant):
                    type_bindings[name] = QGL2.CLASSICAL

                elif isinstance(actual_val, ast.Name):
                    if actual_val.id in scope_types:
                        type_bindings[name] = scope_types[actual_val.id]

                elif isinstance(actual_val, ast.Call):
                    called_func_name = pyqgl2.importer.collapse_name(
                            actual_val.func)
                    called_func = self.importer.resolve_sym(
                            actual_val.qgl_fname, func_name)

                    if not called_func:
                        NodeError.warning_msg(value,
                                'function [%s] not found' % called_func_name)
                        continue
                    elif called_func.returns:
                        rtype = called_func_def.returns
                        if isinstance(rtype, ast.Name):
                            rtype_name = rtype.id

#                            if rtype_name not in [QGL2.CLASSICAL, QGL2.QBIT, 'unknown', QGL2.SEQUENCE, QGL2.PULSE, QGL2.CONTROL, QGL2.QBIT_LIST]:
                            if rtype_name not in [QGL2.CLASSICAL, QGL2.QBIT, 'unknown']:
                                NodeError.warning_msg(arg,
                                        ('parameter type \'%s\' is not supported' %
                                    arg_type_name))

                        type_bindings[name] = rtype_name

        return val_bindings, type_bindings

    def name_is_in_lscope(self, name):
        """
        Return True if the name has been bound to the local scope,
        False otherwise.
        
        The name is assumed to be a string that
        may represent a lexically-local variable: no indirection
        permitted. TODO: this is not checked.

        This only considers the local scope, and not the surrounding
        scopes (class, module, global).
        """

        return (name in self.parameter_names) or (name in self.local_names)

    def add_type_binding(self, node, name, name_type):
        """
        Add a binding between a name and a type, in the local context.

        Gripe and do nothing if there is already a binding for this
        name in either the parameter or local scope, and it disagrees
        with the requested binding.

        The node parameter is used only to generate error messages
        that can be traced back to the original code, since the node
        contains the file and line number of the code prior to
        any transformation
        """

        if name in self.parameter_names:
            old_type = self.parameter_names[name]
            if old_type != name_type:
                NodeError.error_msg(node,
                        ('parameter type changed %s -> %s' %
                            (old_type, name_type)))
        elif name in self.local_names:
            old_type = self.local_names[name]
            if old_type != name_type:
                NodeError.error_msg(node,
                        'type changed %s -> %s' % (old_type, name_type))
        else:
            NodeError.diag_msg(node,
                    'add type %s -> %s' % (name, name_type))
            self.local_names[name] = name_type

    def is_qbit_parameter(self, name):
        if name not in self.parameter_names:
            return False
        if self.parameter_names[name] != QGL2.QBIT:
            return False
        else:
            return True

    def is_qbit_local(self, name):
        if name not in self.local_names:
            return False
        elif self.local_names[name] != QGL2.QBIT:
            return False
        return True

    def is_qbit(self, name):
        return self.is_qbit_parameter(name) or self.is_qbit_local(name)

    def visit_body(self, body):
        """
        Visit all the items in a "body", which is a list
        of statements
        """

        for stmnt in body:
            self.visit(stmnt)

    def visit_Assign(self, node):

        # FIXME: can't handle nested tuples properly
        # For now we're not even going to try.

        if not isinstance(node.targets[0], ast.Name):
            NodeError.warning_msg(node, 'tuple returns not supported yet')
            self.generic_visit(node)
            return node

        target = node.targets[0]

        print('VA target0: %s' % ast.dump(target))

        value = node.value
        name = target.id

        if not isinstance(target, ast.Name):
            # should this be considered an error?
            # it's not an error in Python, but it's hard for us to handle.
            return node

        if self.is_qbit_parameter(name):
            msg = 'reassignment of qbit parameter \'%s\' forbidden' % name
            NodeError.error_msg(node, msg)
            return node

        if self.is_qbit_local(name):
            msg = 'reassignment of qbit \'%s\' forbidden' % name
            NodeError.error_msg(node, msg)
            return node

        if isinstance(value, ast.Name):
            if not self.name_is_in_lscope(value.id):
                NodeError.error_msg(node,
                        'unknown symbol \'%s\'' % value.id)
                return node

            if self.is_qbit_parameter(name):
                self.warning_msg(node,
                        'aliasing qbit parameter \'%s\' as \'%s\'' %
                        (value.id, name))
                self.add_type_binding(value, name, QGL2.QBIT)
                target.qgl_is_qbit = True
            elif self.is_qbit_local(name):
                self.warning_msg(node,
                        'aliasing local qbit \'%s\' as \'%s\'' %
                        (value.id, name))
                self.add_type_binding(value, name, QGL2.QBIT)
                target.qgl_is_qbit = True
            else:
                self.add_type_binding(value, name, QGL2.CLASSICAL)
                target.qgl_is_qbit = False

        elif isinstance(value, ast.Call):

            func_name = pyqgl2.importer.collapse_name(value.func)
            func_def = self.importer.resolve_sym(value.qgl_fname, func_name)

            # FIXME: for debugging only!
            new_scope = FindTypes.find_lscope(
                    self.importer, func_def, value, self)
            # FIXME: end debugging

            # If we can't find the function definition, or it's not declared
            # to be QGL, then we can't handle it.  Return immediately.
            #
            if not func_def:
                NodeError.warning_msg(
                        value, 'function [%s] not found' % func_name)
                self.add_type_binding(value, name, 'unknown')
                return node

            if func_def.returns:
                rtype = func_def.returns
                if (isinstance(rtype, ast.Name) and rtype.id == QGL2.QBIT):
                    # Not sure what happens if we get here: we might
                    # have a wandering variable that we know is a qbit,
                    # but we never know which one.
                    #
                    print('XX EXTENDING LOCAL (%s)' % name)
                    self.add_type_binding(value, name, QGL2.QBIT)
                    target.qgl_is_qbit = True

            if not func_def.qgl_func:
                # TODO: this seems bogus.  We should be able to call
                # out to non-QGL functions
                #
                NodeError.error_msg(
                        value, 'function [%s] not declared to be QGL2' %
                            func_name)
                return node

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
            if isinstance(value, ast.Call) and (func_def.name == QGL2.QBIT_ALLOC):
                self.add_type_binding(value, name, QGL2.QBIT)

        return node

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
                self.add_type_binding(subnode, name, QGL2.CLASSICAL)

        self.visit_body(node.body)
        self.visit_body(node.orelse)

    def visit_ExceptHandler(self, node):
        name = node.name
        if self.name_is_in_lscope(name):
            NodeError.warn_msg(node,
                    ('exception var [%s] hides sym in outer scope' % name))

            # assume all exceptions are classical
            self.add_type_binding(subnode, subnode.id, QGL2.CLASSICAL)
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
            # This makes the assumption that ANYTHING named 'Qbit'
            # is a Qbit assignment function, which is lame and should
            # be more carefully parameterized.  Things to think about:
            # looking more deeply at its signature and making certain
            # that it looks like the 'right' function and not something
            # someone mistakenly named 'Qbit' in an unrelated context.
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

        qbit1 = Qbit(1) # Create a new qbit; qbit1 is marked
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
