#!/usr/bin/env python3

# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import ast

from ast import NodeTransformer
from copy import deepcopy

from pyqgl2.ast_util import NodeError, ast2str
from pyqgl2.importer import NameSpaces
from pyqgl2.single import is_qbit_create

def insert_keyword(kwargs, key, value):

    if not isinstance(key, str):
        return 'key is not a string'
    elif key in kwargs:
        return 'key [%s] already defined' % key
    else:
        kwargs[key] = value
        return None

def compute_actuals(call_ast, importer, local_variables=None):
    """
    """

    # If this fails, we're off to a rocky start.  We could have
    # a degenerate environment for simple mathematical expressions,
    # but even those are fraught with ambiguity in Python
    #
    # TODO: some defensive programming here
    #
    namespace = importer.path2namespace[call_ast.qgl_fname]

    pos_args = list()
    kw_args = dict()

    for i in range(len(call_ast.args)):
        arg = call_ast.args[i]

        # If the argument is starred, then we need to find the list
        # that this expression evaluates to, and then append this
        # to the list of positional args
        #
        if isinstance(arg, ast.Starred):

            (success, value) = namespace.native_eval(arg.value,
                    local_variables=local_variables)

            if not success:
                print('EV confusion at arg %d [%s]' % (i, call_ast))
                # TODO: need to handle this; we're dead
                return None, None

            # Coerce any list-like thing to be a real list.
            # If anything goes wrong, it should throw a TypeError.
            #
            try:
                value = list(value)
            except TypeError as exc:
                print('EV confusion: %s' % str(exc))
                return None, None

            # If the resulting list is empty, then DON'T add the empty
            # list to the args.  Empty starred actuals are discarded.
            #
            if len(value) > 0:
                pos_args += value
        else:
            (success, value) = namespace.native_eval(arg,
                    local_variables=local_variables)

            if not success:
                print('EV confusion at arg %d [%s]' % (i, call_ast))
                # TODO: need to handle this; we're dead
                return None, None

            pos_args.append(value)

        # TODO: is there anything else it could be, besides Starred and "Normal"?

    for i in range(len(call_ast.keywords)):
        arg = call_ast.keywords[i]

        (success, expr_val) = namespace.native_eval(arg.value,
                local_variables=local_variables)
        if not success:
            print('EV confusion at arg %d [%s]' % (i, call_ast))
            # TODO: need to handle this; we're dead

        # A ** actual appears in the keyword actuals as a argument
        # with no name (unlike a * actual, which has its own node type)
        # so if we see a "nameless" keyword parameter then we know
        # it's actually a reference to a dictionary we need to pull in
        #
        if arg.arg == None:

            # TODO: the expr_val might be anything, but only a subclass
            # of dictionary-like things will actually work!
            #
            if not isinstance(expr_val, dict):
                print('EV failure: expected a dict with **')
                return None, None

            # TODO: wrap this up in a test to make sure that keys()
            # and lookups actually work.

            for key in expr_val.keys():
                msg = insert_keyword(kw_args, key, expr_val[key])
                if msg:
                    print('EV failure: %s' % msg)
                    return None, None
        else:
            msg = insert_keyword(kw_args, arg.arg, expr_val)
            if msg:
                print('EV failure: %s' % msg)
                return None, None

    return pos_args, kw_args

def check_actuals(func_ast, pos_args, kw_args, call_ast=None, qbits=None):
    """
    Confirm that the actual parameters (as given by pos_args and kw_args)
    correctly match the declaration of the function (as provided in the
    func_ast, and return a new dictionary that maps formal parameter names
    to their actual values for this invocation.

    The call_ast, if provided, is used to provide tag errors and warnings
    with the location of the call, but is not used otherwise.

    The qbits map, if provided, is used to label variables that are known
    to be qbits (FIXME this is clunky)

    The checks are:

    a) are there enough pos_args to match the function definition

    b) are there any kw_args that are not expected?

    c) are there any required kw_args that are absent?

    d) are any parameters specified more than once?

    FIXME this needs to be described more tightly
    """

    return dict() # FIXME doesn't do anything



class SimpleEvaluator(object):

    def __init__(self, importer, local_context, local_types=None):

        self.importer = importer

        if not local_context:
            local_context = dict() # degenerate context

            # If there's no local context, then ignore any local types
            # that we're given, because they must be bogus
            #
            # TODO: could add a sanity check for this.

            local_types = None

        if not local_types:
            local_types = dict() # degenerate types

        assert isinstance(local_context, dict), 'local_context must be a dict'
        assert isinstance(local_types, dict), 'local_types must be a dict'

        self.locals_stack = list()
        self.locals_stack.append(local_context)

        self.types_stack = list()
        self.types_stack.append(local_types)

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

    def update_node(self, node):
        """
        Update a node by replacing its variable references with the
        values bound to those variables in the current context

        Returns the new, potentially modified node
        """

        NodeError.error_msg(node, 'update_node not implemented yet')
        return node

    def do_assignment(self, node):
        """
        Handle an assignment statement by creating/updating local bindings
        """

        # FIXME: this isn't right.  We need to handle this case correctly
        #
        qbit_create = is_qbit_create(node)
        if qbit_create:
            # TODO: need to track the creation of the qbit.  This is
            # currently done elsewhere.
            return True

        local_variables = self.locals_stack[-1]

        namespace = self.importer.path2namespace[node.qgl_fname]
        success = namespace.native_exec(node, local_variables=local_variables)
        if not success:
            NodeError.error_msg(node, 'failed to evaluate [%s]' % ast2str(node))
            return False

        print('EV locals %s' % str(self.locals_stack[-1]))
        return True

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


if __name__ == '__main__':
 
    file_name = 'aaa.py'
    main_name = 't1'

    importer = NameSpaces(file_name, main_name)

    if not importer.qglmain:
        NodeError.fatal_msg(None, 'no qglmain function found')

    NodeError.halt_on_error()

    ptree = importer.qglmain

    test_calls = [
            'foo(1, 2, 3, e=55)',
            'foo(a, b, c)',
            'foo(a + b, b + c, 2 * c)',
            'foo(a, *[11, 12, 13])',
            'foo(a, *l1)',
    ]

    for call in test_calls:
        t1 = ast.parse(call, mode='eval')
        t1 = t1.body
        print('T1 %s' % ast.dump(t1))
        t1.qgl_fname = ptree.qgl_fname

        loc = { 'a' : 100, 'b' : 101, 'c' : 102, 'l1' : [22, 23] }

        (pos, kwa) = compute_actuals(t1, importer, local_variables=loc)
        print('T1 %s [%s] [%s]' % (call, str(pos), str(kwa)))

    evaluator = SimpleEvaluator(importer, None)
    for stmnt in ptree.body:
        if isinstance(stmnt, ast.Assign):
            evaluator.do_assignment(stmnt)


