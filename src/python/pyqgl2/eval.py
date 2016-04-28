#!/usr/bin/env python3

# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import ast

from ast import NodeTransformer
from copy import deepcopy

from pyqgl2.ast_util import NodeError
from pyqgl2.importer import NameSpaces

class SimpleEvaluator(NodeTransformer):

    def __init__(self, importer, local_context):

        self.importer = importer

        if not local_context:
            local_context = dict() # degenerate context

        assert isinstance(local_context, dict), 'local_context must be a dict'

        self.locals_stack = list()
        self.locals_stack += list(local_context)

    def push_context(self, values=None):

        if not values:
            values = dict() # degenerate local values

        assert isinstance(values, dict), 'values must be a dict'

        self.locals_stack += list(values)

    def pop_context(self):

        assert len(self.locals_stack) > 0, 'stack must not be empty'

        popped_context = self.locals_stack.pop()

        print('EV popped %s' % str(popped_context))

    def initial_context(self, args, kwargs, func_ast):
        """
        Create a local context for a function call.  The actual
        parameters are given in args (positional args) and kwargs
        (positional args), while the names of the formal parameters
        are taken from func_ast.

        Given the way that Python maps actuals to formals (with
        things like mixing positional and keyword parameters with
        default...) makes this more complicated than it would
        first appear.  We don't handle every possible case,
        such as concatenated *args.  (we don't believe that
        we'll see this case come up very often)

        TODO: current prototype assumes positional parameters ONLY.
        This isn't enough to handle any real programs, but it's
        a bootstrapping step.
        """

        # We could handle more general list- and dict-like objects,
        # but we don't right now.  TODO
        #
        assert (not args) or isinstance(args, list)
        assert (not kwargs) or isinstance(kwargs, dict)

        assert isinstance(func_ast, ast.FunctionDef), 'func_ast must be FunctionDef'

        arg_names = [arg.arg for arg in func_ast.args.args]

        context = dict()

        # FIXME this only handles positional parameters.
        # Needs to be extended to handle all the special cases
        # of kwargs (or detect and flag cases it doesn't handle)
        #
        for i in range(arg_names):
            arg_name = arg_names[i]
            arg_value = args[i]
            print('EV arg [%s] := %s' % (arg_name, args_value))

            context[arg_name] = arg_value

        return context

    def call_context(self, call_ast, func_ast):
        """
        Wrapper for initial_context

        FIXME: Only handles positional parameters
        """

        assert isinstance(func_ast, ast.Call), 'call_ast must be Call'
        assert isinstance(func_ast, ast.FunctionDef), 'func_ast must be FunctionDef'

        namespace = self.importer.path2namespace[call_ast.qgl_fname]

        args = list()
        for i in range(len(call_ast.args)):
            (success, value) = namespace.native_eval(call_ast.args[i])
            if not success:
                print('EV confusion at arg %d [%s]' % (i, call_ast))
                # TODO: need to handle this; we're dead
            else:
                args.append(value)

        return self.initial_context(args, dict(), func_ast)

    def visit_Assign(self, node):
        return node

        # figure out whether it's a call, or an expr.

    def do_call(self, call_node):

        funcname = pyqgl2.importer.collapse_name(call_node.func)
        func_ast = self.importer.resolve_sym(call_node.qgl_fname, funcname)
        if not func_ast:
            print('EV NO AST: ERROR')
            return node

        # if it's a stub, then leave it alone.
        if func_ast.qgl_stub:
            print('EV IS STUB: passing through')
            return node

        # if it's qgl2decl, then we're going to inline it; leave it alone
        # TODO: something is wrong here because we should never get
        # a value back from a qgl2decl function; they are called only
        # for effect.

        # otherwise, let's see if we can evaluate it.
        ...


if __name__ == '__main__':
 
    file_name = 'aaa.py'
    main_name = 't1'

    importer = NameSpaces(file_name, main_name)

    if not importer.qglmain:
        NodeError.fatal_msg(None, 'no qglmain function found')

    NodeError.halt_on_error()

    ptree = importer.qglmain

