#!/usr/bin/env python3

# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import ast

from ast import NodeTransformer
from copy import deepcopy

import pyqgl2.ast_util
import pyqgl2.inline


from pyqgl2.ast_util import NodeError, ast2str
from pyqgl2.debugmsg import DebugMsg
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

        assert isinstance(func_ast, ast.FunctionDef), \
                'func_ast must be FunctionDef'

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

    def do_test(self, node):
        """
        Evaluate an test expression, to see if it can be determined
        in the current context
        """

        local_variables = self.locals_stack[-1]

        namespace = self.importer.path2namespace[node.qgl_fname]
        success, val = namespace.native_eval(node,
                local_variables=local_variables)
        if not success:
            NodeError.error_msg(node,
                    'failed to evaluate [%s]' % ast2str(node))
            return False, None
        else:
            return True, val

    def do_iters(self, node):
        """
        Evaluate an iters expression, and see if we can turn it
        into a list we can express in AST
        """

        local_variables = self.locals_stack[-1]

        namespace = self.importer.path2namespace[node.qgl_fname]
        success, val = namespace.native_eval(node,
                local_variables=local_variables)
        if not success:
            NodeError.error_msg(node,
                    'failed to evaluate [%s]' % ast2str(node))
            return False, None

        # TODO: review whether this always works.
        #
        # If we get something like a set, tuple, iterator, etc, we need to
        # convert it to a list, because that's the only type we understand
        # at the next level.  Does just tossing it into a list() do this,
        # or are there side-effects we need to consider?
        #
        if not isinstance(val, list):
            val = list(val)

        # these are fragile operations; try to be more defensive
        #
        try:
            val_str = str(val)
            val_ast = ast.parse(val_str, mode='eval')
        except BaseException as exc:
            NodeError.error_msg(node, 'cannot convert iter value back to AST')
            NodeError.error_msg(node, 'original expr: [%s]' % ast2str(node))
            NodeError.error_msg(node, 'transformed expr: [%s]' % val_str)
            return False, None

        # What we get back from ast.parse is an ast.Expression, but what
        # we want is the body wrapped by that Expression
        #
        return True, val_ast.body


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
            print('EV: ERROR: must handle qbit_create')
            return True, None

        local_variables = self.locals_stack[-1]

        namespace = self.importer.path2namespace[node.qgl_fname]
        rval = node.value

        success, values = namespace.native_eval(
                node.value, local_variables=local_variables)
        if not success:
            NodeError.error_msg(node,
                    'failed to evaluate [%s]' % ast2str(node))
            return False, None

        print('EV locals %s' % str(self.locals_stack[-1]))

        # Now we need to update the state we're tracking

        self.fake_assignment_worker(node.targets[0], values,
                local_variables, namespace)

        return True, values

    def fake_assignment(self, target_ast, values):
        """
        Fake the assignment of the given values to the given targets.

        The targets are specified as AST, but the values are the
        native Python values.

        This assignment is presumed to be compatible; we don't check
        (although we do try to detect failures).
        """

        namespace = self.importer.path2namespace[target_ast.qgl_fname]

        local_variables = self.locals_stack[-1]
        scratch_locals = deepcopy(local_variables)

        self.fake_assignment_worker(
                target_ast, values, scratch_locals, namespace)

        self.locals_stack[-1] = scratch_locals

    def fake_assignment_worker(self,
            target_ast, values, scratch_locals, namespace):

        if isinstance(target_ast, ast.Name):
            scratch_locals[target_ast.id] = values
        elif (isinstance(target_ast, ast.Tuple) or
                isinstance(target_ast, ast.List)):
            for i in range(len(target_ast.elts)):
                self.fake_assignment_worker(
                        target_ast.elts[i], values[i],
                        scratch_locals, namespace)
        elif isinstance(target_ast, ast.Subscript):

            # In this case, we don't have an ideal situation
            # because the Python rules for evaluating subscripts
            # within tuples are weird.

            # TODO: detect subscripts within tuples, and warn
            # the user about potential weirdness

            # TODO: there are many things that can go wrong here,
            # and we don't deal with many of them gracefully.

            node = target_ast.value
            while not isinstance(node, ast.Name):
                node = node.value
            name = node.id

            slices = list()
            node = target_ast
            while isinstance(node, ast.Subscript):
                slices.append(node.slice.value)
                node = node.value

            slices.reverse()
            local_variables = self.locals_stack[-1]

            ref = scratch_locals[name]
            for i in range(len(slices) - 1):
                slice_ast = slices[i]
                text = ast2str(slice_ast)
                (success, ind) = namespace.native_eval(text,
                        local_variables=local_variables)
                if success:
                    ref = ref[ind]
                else:
                    NodeError.error_msg(slice_ast,
                            'could not eval slice expr [%s]' % text)
                    return

            slice_ast = slices[-1]
            text = ast2str(slice_ast)
            (success, ind) = namespace.native_eval(text,
                    local_variables=local_variables)
            if success:
                ref[ind] = values
            else:
                NodeError.error_msg(slice_ast,
                        'could not eval slice expr [%s]' % text)
                return

        else:
            DebugMsg.log('bogus target_ast [%s]' % ast.dump(target_ast),
                    DebugMsg.HIGH)

    NONQGL2 = 0
    QGL2STUB = 1
    QGL2DECL = 2
    ERROR = -1

    def do_call(self, call_node):
        """
        Pseudo-execute a call.
        
        If it's a call to a stub function, then we don't do anything
        now, because we'll actually execute it later.  Return QGL2STUB.

        If it's a call to a qgl2decl function, then return QGL2DECL.
        This call should be inlined, so this is a temporary failure:
        we need to inline the function, and then try again.

        Anything else, we don't execute, and return NONQGL2.  This
        means that the function is executed only for a side effect,
        and we're not really sure what to do with it yet.

        If there's an error, return ERROR.
        """

        funcname = pyqgl2.importer.collapse_name(call_node.func)
        func_ast = self.importer.resolve_sym(call_node.qgl_fname, funcname)
        if not func_ast:
            NodeError.error_msg(call_node,
                    ('no function definition found for [%s]' %
                        ast.dump(call_node.func)))
            return self.ERROR

        # if it's a stub, then leave it alone.
        if pyqgl2.inline.is_qgl2_stub(func_ast):
            print('EV IS QGL2STUB: passing through')
            return self.QGL2STUB
        elif pyqgl2.inline.is_qgl2_def(func_ast):
            print('EV IS QGL2DECL: passing through')
            return self.QGL2DECL

        # otherwise, let's see if we can evaluate it.  We do this only
        # for its side effects; we don't care what the value returned
        # by the call is (or if there even is one).

        """
        namespace = self.importer.path2namespace[call_node.qgl_fname]
        print('EV NS %s' % namespace)
        local_variables = self.locals_stack[-1]
        success = namespace.native_exec(call_node,
                local_variables=local_variables)
        if not success:
            NodeError.error_msg(call_node,
                    'failed to evaluate [%s]' % ast2str(call_node))
            return False

        print('EV locals %s' % str(self.locals_stack[-1]))
        """

        return self.NONQGL2


class EvalTransformer(object):
    """
    Transform an AST by replacing expressions with their values
    where possible

    This is not a subclass of ast.NodeTransformer because it
    doesn't implement most of the NodeTransformer interface,
    and it would be incorrect to use it as a NodeTransformer
    except in very specific cases.  Rather than try to hobble
    a NodeTransformer, I'm going to simply implement functions
    to handle those cases.

    Takes a conservative approach; may need multiple iterations
    to completely evaluate something.  Needs to work in conjunction
    with the loop unroller and function inliner; will not attempt
    to handle loops, stub functions, or qgl2decl'd functions
    """

    def __init__(self, eval_state):
        """
        eval_state is a SimpleEvaluator instance
        """

        assert isinstance(eval_state, SimpleEvaluator), \
                ('expected a SimpleEvaluator, got %s' % type(eval_state))

        self.eval_state = eval_state

        # a list of assignment statements to evaluate before
        # anything else, to compute the values used later at runtime
        #
        self.preamble_stmnts = list()
        self.preamble_values = list()

        # set to zero every time visit() is called, and then
        # incremented every time a change is made
        #
        self.change_cnt = 0

    def print_state(self):

        print('EVS: PREAMBLE:')
        for stmnt in self.preamble_stmnts:
            print('    %s' % ast2str(stmnt).strip())

        print('EVS: LOCALS:')
        local_variables = self.eval_state.locals_stack[-1]
        for key in sorted(local_variables.keys()):
            print('    %s = %s' % (key, str(local_variables[key])))

    def visit(self, orig_node):
        """
        Visit a function definition, transforming it according to
        the current context, and returning the result.

        Note: this method is called "visit" to match the interface
        provided by the NodeTransformer classes, but this isn't a
        NodeTransformer.
        """

        assert isinstance(orig_node, ast.FunctionDef), \
                ('expected ast.FunctionDef, got %s' % type(node))

        self.change_cnt = 0
        node = deepcopy(orig_node)

        # restore the last known set of locals before
        # trying to process the body of the node
        #
        self.setup_locals()

        node.body = self.do_body(node.body)

        # For debugging purposes, print out what we have stored up.
        self.print_state()

        return node

    def setup_locals(self):

        # TODO: should we empty out the local variables in
        # self.eval_state before we start?
        # How do we leave them in the correct initial state, with
        # the actuals for the current call and nothing else?

        # every time we do a visit, "replay" the preamble to
        # bring the current state up-to-date.  We don't do this
        # by re-evaluating things, but just by setting up the
        # local state to recreate the assignments
        #
        # use the old value from preamble_values
        # don't recompute anything
        #
        for i in range(len(self.preamble_stmnts)):
            stmnt = self.preamble_stmnts[i]
            value = self.preamble_values[i]

            if isinstance(stmnt, ast.Assign):
                self.eval_state.fake_assignment(stmnt.targets[0], value)

    def do_body(self, body):

        new_body = list()

        # still_valid is True as long as we're making progress
        # on converting the body.  As soon as we hit anything we
        # can't process, we immediately stop and append the rest of
        # the body as-is.
        #
        still_valid = True

        for stmnt_index in range(len(body)):
            stmnt = body[stmnt_index]

            if not still_valid:
                new_body.append(stmnt)
                continue

            print('EV stmnt todo %s' % ast.dump(stmnt))

            # Skip over any pass statements or comment strings.
            #
            # TODO we might want to keep some record that we saw them,
            # but we don't want to emit them.  Right now we discard them.
            #
            # TODO: I don't think we can always omit a pass statement.
            # only if we've removed the calling context as well.
            #
            if isinstance(stmnt, ast.Pass):
                self.change_cnt += 1
                continue

            elif (isinstance(stmnt, ast.Expr) and
                    isinstance(stmnt.value, ast.Str)):
                self.change_cnt += 1
                continue

            elif isinstance(stmnt, ast.Assign):
                # FIXME: this isn't quite right yet.  We need to
                # handle the case of qbit creation better.
                # Right now it's handled elsewhere, but it could
                # be handled here.
                if is_qbit_create(stmnt):
                    print('EV: QBIT CREATION (punting)')
                    new_body.append(stmnt)
                    continue

                success, values = self.eval_state.do_assignment(stmnt)
                if success:
                    self.change_cnt += 1
                    print('EV did assignment [%s]' % ast2str(stmnt))
                    self.preamble_stmnts.append(stmnt)
                    self.preamble_values.append(values)
                else:
                    print('EV FAILED assignment [%s]' % ast2str(stmnt))
                    # maybe we'll be successful next time.
                    # (unlikely, but possible)
                    new_body.append(stmnt)

            elif (isinstance(stmnt, ast.Expr) and
                    isinstance(stmnt.value, ast.Call)):
                # If it's a call, we need to figure out whether it's
                # something we should leave alone, expand, or consider
                # to be an error.

                new_body.append(stmnt)

                # XXX should we keep it, or get rid of it?
                success = self.eval_state.do_call(stmnt.value)
                if success == self.eval_state.ERROR:
                    # Ooops.  Fail hard.
                    still_valid = False
                    break
                elif success == self.eval_state.QGL2DECL:
                    # We can't proceed, with the evaluation,
                    # but leave the stmnt in the new body,
                    # in the hope that we can expand it later.
                    #
                    new_body.append(stmnt)
                    still_valid = False
                    continue
                elif success == self.eval_state.QGL2STUB:
                    # real success
                    new_body.append(stmnt)
                elif success == self.eval_state.NONQGL2:
                    # We don't know what to do...  punt.
                    NodeError.error_msg(stmnt,
                            'not sure how to handle [%s]' % ast2str(stmnt))
                    still_valid = False
                    continue

            elif isinstance(stmnt, ast.For):
                print('EV ast.For check')

                if not isinstance(stmnt.iter, ast.List):

                    print('EV ast.For iter not ast.List')
                    success, new_iter = self.eval_state.do_iters(stmnt.iter)
                    if not success:
                        # we'll try again later
                        new_body.append(stmnt)
                        still_valid = False
                        continue

                    print('EV iter evaluated %s to %s' %
                            (ast2str(stmnt.iter), ast2str(new_iter)))
                    print('EV2 iter evaluated to %s' % ast.dump(new_iter))

                    if not isinstance(new_iter, ast.List):
                        NodeError.error_msg(stmnt.iter,
                                'iter does not evaluate to list')
                        still_valid = False
                        break
                    else:
                        stmnt.iter = new_iter
                        self.change_cnt += 1
                        still_valid = False

                # NOTE: detection of simple iteration (and conversion
                # to Qrepeat, if possible) is done in the loop unroller,
                # not here.  This function only tries to expand the elts.

                new_body.append(stmnt)

            elif isinstance(stmnt, ast.If):
                # if is't an "if" statement, try to figure out
                # whether the condition is determined, and if so
                # the replace this statement with either the "if"
                # or "else" clause.

                success, test = self.eval_state.do_test(stmnt.test)
                if success:
                    # Even though we don't know whether we're going
                    # to make any "real" changes, we figured something out
                    # that we didn't figure out before, so we count
                    # it as a change
                    #
                    self.change_cnt += 1

                    if test:
                        stmnt_list = stmnt.body
                    else:
                        stmnt_list = stmnt.orelse

                    for substmnt in stmnt_list:
                        # skip over pass statements
                        #
                        # TODO: could also omit anything after a break
                        # or continue statement, because they'll
                        # be unreachable
                        #
                        if isinstance(substmnt, ast.Pass):
                            continue

                        new_body.append(substmnt)

            else:
                # TODO: we could add more sanity checks here,
                # looking for things that shouldn't ever happen.
                # Right now we just assume that anything else is OK,
                # but there are things that could go wrong.

                new_body.append(stmnt)
                still_valid = False
                print('EV unhandled [%s]' % ast.dump(stmnt))

        # If we've pruned everything out of the body,
        # then insert a pass statement to keep things
        # syntactically correct
        #
        if len(new_body) == 0:
            new_pass = ast.Pass()
            pyqgl2.ast_util.copy_all_loc(new_pass, orig_node)
            new_body.append(new_pass)

        print('EV final\n%s' % str([ast2str(n) for n in new_body]))

        return new_body


if __name__ == '__main__':

    def test_calls():
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

    def test_fake_assignment(importer):

        test_assignments = [
                [ 'a = 12', 12 ],
                [ '(a, b) = ("a", "b")', ('a', 'b') ],
                [ '(A, [B, C]) = ("A", ("B", "C"))', ('A', ('B', 'C')) ],
                [ 'x, [y, z], w = "x", ["y", "z"], "w"',
                    ('x', ['y', 'z'], 'w') ],
                [ 'a, b = "a", ("1", "2", "3")',
                    ('a', ('1', '2', '3')) ],
                [ 'a1[1] = "A"', "A" ],
                [ 'a2[1][2] = "A12"', "A12" ],
                [ 'a3[1][2][3] = "A123"', "A123" ],
                [ 'a1[identity(0)] = "A0"', "A0" ],
                [ 'a2[identity(0)][identity(1)] = "A01"', "A01" ],
                [ 'a2[identity(2)][identity(3)] = "A23"', "A23" ],
                [ 'a2[identity(0) + 1][identity(1) + 1] = "A12"', "A12" ],
        ]

        for (text, val) in test_assignments:
            t1 = ast.parse(text, mode='exec')
            t1 = t1.body[0]

            # set the qgl_fname, so that there's a namespace
            #
            for subnode in ast.walk(t1):
                subnode.qgl_fname = 'aaa.py'

            print('T1 %s' % ast.dump(t1))

            evaluator = SimpleEvaluator(importer, None)
            local_variables = evaluator.locals_stack[-1]
            local_variables['a1'] = ['x', 'y', 'z', 'w']
            local_variables['a2'] = [
                    ['x0', 'y0', 'z0', 'w0'],
                    ['x1', 'y1', 'z1', 'w1'],
                    ['x2', 'y2', 'z2', 'w2'],
                    ['x3', 'y3', 'z3', 'w3'],
            ]
            local_variables['a3'] = [
                    [
                    ['x00', 'y00', 'z00', 'w00'],
                    ['x01', 'y01', 'z01', 'w01'],
                    ['x02', 'y02', 'z02', 'w02'] ],
                    [
                    ['x10', 'y10', 'z10', 'w10'],
                    ['x11', 'y11', 'z11', 'w11'],
                    ['x12', 'y12', 'z12', 'w12'] ],
                    [
                    ['x20', 'y20', 'z20', 'w20'],
                    ['x21', 'y21', 'z21', 'w21'],
                    ['x22', 'y22', 'z22', 'w22'] ],
            ]

            evaluator.fake_assignment(t1.targets[0], val)
            print('result [%s] [%s]' % (text, evaluator.locals_stack[-1]))

    file_name = 'aaa.py'
    main_name = 't1'

    importer = NameSpaces(file_name, main_name)

    if not importer.qglmain:
        NodeError.fatal_msg(None, 'no qglmain function found')

    NodeError.halt_on_error()
    ptree = importer.qglmain
    print('PTREE %s' % ptree.qgl_fname)

    test_fake_assignment(importer)

    evaluator = SimpleEvaluator(importer, None)
    for stmnt in ptree.body:
        if isinstance(stmnt, ast.Assign):
            evaluator.do_assignment(stmnt)

    et = EvalTransformer(SimpleEvaluator(importer, None))
    ptree2 = et.visit(ptree)

