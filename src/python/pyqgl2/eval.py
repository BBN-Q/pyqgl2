#!/usr/bin/env python3

# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import ast
import collections
import re

import pyqgl2.ast_util
import pyqgl2.inline

from pyqgl2.ast_util import NodeError, ast2str, expr2ast, copy_all_loc
from pyqgl2.debugmsg import DebugMsg
from pyqgl2.importer import NameSpaces
from pyqgl2.inline import inline_call
from pyqgl2.inline import Inliner
from pyqgl2.inline import NameFinder, NameRedirector, NameRewriter
from pyqgl2.inline import QubitPlaceholder
from pyqgl2.inline import TempVarManager
from pyqgl2.qgl2_check import QGL2check
from pyqgl2.single import is_qbit_create
from pyqgl2.quickcopy import quickcopy

from QGL import Qubit
from QGL import QubitFactory

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
                    'failed to evaluate test [%s]' % ast2str(node).strip())
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
                    'failed to evaluate iters [%s]' % ast2str(node).strip())
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

    def eval_expr(self, expr):

        local_variables = self.locals_stack[-1]
        namespace = self.importer.path2namespace[expr.qgl_fname]

        success, values = namespace.native_eval(
                expr, local_variables=local_variables)

        return success, values

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
                    ('failed to evaluate assignment [%s]' %
                        ast2str(node).strip()))
            return False, None

        # print('EV locals %s' % str(self.locals_stack[-1]))

        # Now we need to update the state we're tracking

        if isinstance(node, ast.Assign):
            target = node.targets[0]
        else:
            target = node.target

        self.fake_assignment_worker(target, values,
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

        # print('EV FA to [%s]' % ast2str(target_ast))
        namespace = self.importer.path2namespace[target_ast.qgl_fname]

        local_variables = self.locals_stack[-1]

        # TODO: we used to copy local_variables here. Why?

        self.fake_assignment_worker(
                target_ast, values, local_variables, namespace)

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
    QGL2MEAS = 3
    ERROR = -1

    def expand_qgl2decl_call(self, call_node):

        # If the function we're trying to call is the value of a
        # local symbol, then we need to track down that value.
        # If it turns out to be a qgl2stub, then turn the symbol
        # back into that stub.  [NOTE: this needs to be fixed to
        # work properly if the stub is not accessible in the current
        # namespace, or has been aliased within this namespace!]
        #
        # We're not good at finding things generally, but we
        # can try to find it in the local bindings.
        #
        if ((not isinstance(call_node.func, ast.Name)) and
                (not isinstance(call_node.func, ast.Attribute))):
            return None

        # TODO: this probably isn't right for looking up Attributes
        #
        local_variables = self.locals_stack[-1]
        if call_node.func.id not in local_variables:
            return None

        val = local_variables[call_node.func.id]

        if (not hasattr(val, '__qgl2_wrapper__') or
                (val.__qgl2_wrapper__ != 'qgl2decl')):
            return None

        func_name = val.__name__
        namespace = self.importer.path2namespace[call_node.qgl_fname]

        if func_name in namespace.local_defs:
            func_def = namespace.local_defs[func_name]
        elif func_name in namespace.from_as:
            # TODO: check whether this commutes, or whether we
            # need to chase down the reference if the import-from
            # is for a symbol that in turn is an import-from...
            # (but beware of loops!)
            #
            (from_func_name, from_func_fname) = namespace.from_as[func_name]
            from_namespace = self.importer.path2namespace[from_func_fname]
            func_def = from_namespace.local_defs[from_func_name]
        else:
            NodeError.error_msg(
                    call_node, 'symbol [%s] is not defined' % func_name)
            return None

        if not isinstance(func_def, ast.FunctionDef):
            NodeError.error_msg(
                    call_node, 'symbol [%s] is not a function' % func_name)
            return None

        inliner = Inliner(self.importer)

        # build a new call node with the same actuals, but the correct
        # function name
        #
        new_call_node = ast.Call(
                func=ast.Name(id=func_name),
                args=call_node.args, keywords=call_node.keywords)
        pyqgl2.ast_util.copy_all_loc(new_call_node, call_node, recurse=True)

        runtime_check = inliner.add_runtime_checks(new_call_node)
        if runtime_check:
            (chk_assts, chk_checks, chk_call) = runtime_check

            checks = chk_assts + chk_checks
            final_call_node = chk_call.value
        else:
            checks = None
            final_code_node = new_call_node

        sketch_call = inline_call(final_call_node, self.importer)
        if isinstance(sketch_call, list):
            # BRJ: commenting this out because I don't know how to deal
            # with this now that I have removed "with infunc(...)" notations.
            # is this a reason that we need to keep such annotations?

            # new_call_with = sketch_call[0]

            # This is gross, and needs extra explaining...
            # The inlined function we just created is in terms
            # of the checked call (so its actual parameters are the
            # values that are created by the checks), but the
            # the final with-infunc needs to be in terms of the
            # original actuals, so that that scope checking is
            # correct.  To reconcile this, we create a new
            # withitems parameter for the with-infunc, using the
            # new_call_node, and replace the with-infunc
            # withitems with it.

            # new_ap_names = new_call_node.args[:]
            # new_ap_names.insert(
            #         0, new_call_with.items[0].context_expr.args[0])
            # new_call_with.items[0].context_expr.args = new_ap_names

            # if there are checks, then insert them into the body
            #
            if checks:
                # new_call_with.body = checks + new_call_with.body
                new_call = checks + sketch_call

            # print('INLINED REF [\n%s\n]' % ast2str(new_call_with).strip())
            # return new_call_with
            return new_call
        else:
            # TODO: if we got this far and then failed, something
            # terrible probably happened.  Come up with decent
            # diagnostics
            #
            return None

    def find_call_type(self, call_node):
        """
        Find the type of a call.

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

        # If the function we're trying to call is the value of a
        # local symbol, then we need to track down that value.
        # If it turns out to be a qgl2stub, then turn the symbol
        # back into that stub.  [NOTE: this needs to be fixed to
        # work properly if the stub is not accessible in the current
        # namespace, or has been aliased within this namespace!]
        #
        # We're not good at finding things generally, but we
        # can try to find it in the local bindings.
        #
        if ((not isinstance(call_node.func, ast.Name)) and
                (not isinstance(call_node.func, ast.Attribute))):
            NodeError.error_msg(
                    call_node, 'cannot handle anonymous func yet')
            return self.ERROR

        local_variables = self.locals_stack[-1]
        if call_node.func.id in local_variables:
            # print('found locally %s' % call_node.func.id)
            val = local_variables[call_node.func.id]

            if hasattr(val, '__qgl2_wrapper__'):
                # print('has qgl2 wrapper %s' % call_node.func.id)
                if val.__qgl2_wrapper__ == 'qgl2stub':
                    # print('has qgl2 stub wrapper %s' % call_node.func.id)

                    # do surgery on the call to set the name back from
                    # the local name to the stub name.  NOTE: this can
                    # ONLY be done AFTER loops are unrolled, and
                    # everything is converted to static single
                    # assignment, or else this might clobber a
                    # symbol that is still a variable.
                    #
                    call_node.func = ast.Name(id=val.__name__)
                    call_node.qgl_implicit_import = (
                            val.__name__, val.__qgl_implicit_import__, None)
                    return self.QGL2STUB
                elif val.__qgl2_wrapper__ == 'qgl2meas':
                    # do the same name re-writing as with qgl2stubs
                    call_node.func = ast.Name(id=val.__name__)
                    call_node.qgl_implicit_import = (
                            val.__name__, val.__qgl_implicit_import__, None)
                    return self.QGL2MEAS
                else:
                    NodeError.error_msg(
                            call_node,
                            ('cannot handle %s func arg [%s] yet' %
                                (val.__qgl2_wrapper__, val.__name__)))
                    return self.ERROR

            elif hasattr(val, '__name__'):
                # print('has a name %s (%s)' % (call_node.func.id, val.__name__))
                # similar to the qgl2stub case (see above)
                call_node.func = ast.Name(id=val.__name__)
                return self.NONQGL2

            else:
                # Something unanticipated...
                NodeError.error_msg(
                        call_node,
                        ('local symbol unexpectedly used as function [%s]' %
                            ast.dump(call_node)))
                return self.ERROR

        # If we get here, it's because the call is NOT via a
        # local symbol, so we need to look up the symbol.

        # print('not local %s' % call_node.func.id)

        funcname = pyqgl2.importer.collapse_name(call_node.func)
        if not funcname:
            NodeError.error_msg(call_node,
                    ('no function definition found for [%s]' %
                        ast.dump(call_node.func)))
            return self.ERROR

        func_ast = self.importer.resolve_sym(call_node.qgl_fname, funcname)
        if not func_ast:
            if funcname in __builtins__:
                return self.NONQGL2
            else:
                NodeError.error_msg(call_node,
                        ('no function definition found for [%s]' %
                            ast.dump(call_node.func)))
                return self.ERROR

        # if it's a stub, then leave it alone.
        if pyqgl2.inline.is_qgl2_meas(func_ast):
            return self.QGL2MEAS
        elif pyqgl2.inline.is_qgl2_stub(func_ast):
            # print('EV IS QGL2STUB: passing through')
            # print('EV STUB %s' % ast.dump(call_node))
            return self.QGL2STUB
        elif pyqgl2.inline.is_qgl2_def(func_ast):
            # print('EV IS QGL2DECL: passing through')
            return self.QGL2DECL

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

    PRECOMPUTED_VALUES = dict()

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

        # we rewrite variable names to make each variable
        # single-assignment
        #
        self.rewriter = NameRewriter()

        # redirect_global looks like a variable, but it is NOT.
        # The redirect_global MUST be the name of the dictionary
        # used to store the table of precomputed local values,
        # as it is visible within the emitted "QGL1" function.
        #
        # redirect_name is a shorter, convenient name of a
        # local-scope variable used to cache a reference to
        # the global named by redirect_global.
        #
        self.redirect_global_name = 'PRECOMPUTED_VALUES'
        self.redirect_name = '_v'

        # condition variables set to indicate whether we're inside
        # a loop, and whether a "break" or "continue" has been
        # executed in a substatement of the loop.
        #
        # TODO: I don't think that we need to stack these, since
        # we'll always know from context where we are.  But I haven't
        # proven that this is always true (nor have a proven that
        # stacking these might not be the easiest thing to do...)
        # Think about this.
        #
        self.in_loop = False
        self.seen_break = False
        self.seen_continue = False
        self.in_quantum_condition = False

        # the 'use names' (i.e. QBIT_1) for qbits known to be
        # allocated
        #
        self.allocated_qbits = set()

        # run-time variables, which store the results of measurements
        # or computations on other run-time values
        # use a list because measurements are ordered
        self.runtime_variables = list()

    def get_state(self):
        """
        Save a reference to the top of the locals_stack in
        EvalTransformer.PRECOMPUTED_VALUES for future use
        (and return the reference)
        """

        local_variables = self.eval_state.locals_stack[-1]
        EvalTransformer.PRECOMPUTED_VALUES = local_variables

        return local_variables

    def print_state(self):

        print('EVS: PREAMBLE:')
        for stmnt in self.preamble_stmnts:
            print('    %s' % ast2str(stmnt).strip())

        print('EVS: LOCALS:')
        local_variables = self.eval_state.locals_stack[-1]
        for key in sorted(local_variables.keys()):
            print('    %s = %s' % (key, str(local_variables[key])))

    def replace_bindings(self, stmnts):
        """
        Walk through a list of statements, replacing all of the
        references to variables with references to dictionary
        entries, creating a dictionary capturing the references
        (as a member) as a side effect.  This is a destructive
        operation that edits the stmnts in place.

        Returns the new dictionary.

        Assumes that the stmnts have already been transformed
        into single-assignment form, and the values have all
        been precomputed.  Names that are not present in the
        local variables are unchanged by this procedure, and
        their presence is not considered to be unusual (although
        for the purpose of debugging, we note them for now).
        """

        new_values = dict()

        local_variables = self.eval_state.locals_stack[-1]

        name_finder = NameFinder()
        name_redirector = NameRedirector(
                values=new_values, table_name=self.redirect_name)

        for stmnt in stmnts:

            # First, update the values dictionary to make
            # sure that it contains all the values referenced
            # in the statements
            #
            names, _dotted_names, _sub_names = name_finder.find_names(stmnt)

            for name in names:
                if name in local_variables:
                    new_values[name] = local_variables[name]
                else:
                    # for debugging only
                    # let's see if it's a qbit, and if it's
                    # not a qbit, let's see if it's a stub
                    #
                    if name in self.allocated_qbits:
                        # print('EV RB qbit [%s]' % name)
                        pass
                    elif self.eval_state.importer.resolve_sym(
                            stmnt.qgl_fname, name):
                        # print('EV RB func [%s]' % name)
                        pass
                    else:
                        # This isn't always an error: it will
                        # fail for global variables, which we
                        # don't treat completely consistently
                        # (typically 'concur' and 'seq')
                        #
                        print('EV RB sym absent [%s] in %s' %
                                (name, stmnt.qgl_fname))

            # This assumes that the rewriting can always be done
            # in place, and reuse the top level node of the
            # statement, so we don't need to capture it.
            #
            # TODO: verify this.
            #
            name_redirector.visit(stmnt)

        # Stash a reference to new_values in PRECOMPUTED_VALUES,
        # so we can find it again within the QGL1 function we
        # create.
        #
        # Implementation note: this needs to be via a class reference,
        # not an instance reference, because even though
        # self.PRECOMPUTED_VALUES and EvalTransformer.PRECOMPUTED_VALUES
        # initially reference the same thing, reassigning self.*
        # will not change EvalTransformer.*.
        #
        EvalTransformer.PRECOMPUTED_VALUES = new_values

        return new_values

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
        node = quickcopy(orig_node)

        # restore the last known set of locals before
        # trying to process the body of the node
        self.setup_locals()

        # add assignments for passed qbit parameters
        qbit_preamble = list()
        local_variables = self.eval_state.locals_stack[-1]
        for k, v in local_variables.items():
            if isinstance(v, Qubit):
                # FIXME kludge assumption that label is sufficient description
                stmnt = ast.parse("{0} = QubitFactory('{1}')".format(k, v.label))
                copy_all_loc(stmnt.body[0], node, recurse=True)
                qbit_preamble.append(stmnt.body[0])
            elif hasattr(v, '__iter__') and all(isinstance(x, Qubit) for x in v):
                # a uniform list of Qubits
                # FIXME same kludge as above
                tmp_namer = TempVarManager.create_temp_var_manager(
                        name_prefix='___preamble')
                qstrs = ""
                tmp_names = []
                for elem in v:
                    tmp_name = tmp_namer.create_tmp_name(elem.label)
                    tmp_names.append(tmp_name)
                    qstrs += "{0} = QubitFactory('{1}')\n".format(tmp_name, elem.label)
                qstrs += "{0} = ({1})".format(k, ", ".join(tmp_names))
                stmnt = ast.parse(qstrs)
                for s in stmnt.body:
                    copy_all_loc(s, node, recurse=True)
                qbit_preamble += stmnt.body
        node.body = qbit_preamble + node.body
        node.body = self.do_body(node.body)

        # For debugging purposes, print out what we have stored up.
        # self.print_state()

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

    def rewrite_assign(self, stmnt):

        name_finder = NameFinder()

        if isinstance(stmnt, ast.Assign):
            target = stmnt.targets[0]
        else:
            target = stmnt.target

        (simple_names, dotted_names, sub_names) = name_finder.find_names(
                target)

        # TODO: handle this like we do for array subscripts
        #
        if dotted_names:
            NodeError.warning_msg(target,
                    ('assignment to attributes is unreliable in QGL2 %s' %
                        str(list(dotted_names))))

        tmp_targets = TempVarManager.create_temp_var_manager(
                name_prefix='___ass')

        for name in simple_names:
            new_name = tmp_targets.create_tmp_name(name)
            self.rewriter.add_mapping(name, new_name)

        # For each of the subscripted names, we need to make a copy
        # of the object so that the new reference will work.
        # For example, if the assignment is "a[1] = x" and we give
        # "a" the new name "a__ass_001" then we need to copy
        # "a" to "a__ass_001" (or else "a__ass_001[1] = x" isn't
        # going to work).
        #
        local_variables = self.eval_state.locals_stack[-1]

        for name in sub_names:
            if name in self.rewriter.name2name:
                use_name = self.rewriter.name2name[name]
            else:
                print('UNEXPECTED error: use name not in rewriter')
                print('    use_name [%s]' % name)
                use_name = name
                # We're probably about to crash

            new_name = tmp_targets.create_tmp_name(name)
            self.rewriter.add_mapping(name, new_name)

            if use_name not in local_variables:
                print('UNEXPECTED error: use name not in local variables')
                print('    use_name [%s]' % use_name)
            else:
                val = local_variables[use_name]

                if isinstance(val, list):
                    local_variables[new_name] = val[:]
                elif isinstance(val, dict):
                    local_variables[new_name] = dict.copy(val)
                else:
                    local_variables[new_name] = deepcopy(val)

        self.rewriter.rewrite(target)

    def setup(self):
        """
        Generate the list of statements needed to set up the
        classical variables; these statements will be inserted
        inserted into the QGL1 function after the Qubit setup
        and prior to the creation of the sequences

        Currently there is little to do, other than importing
        the EvalTransformer and then finding a reference to
        the EvalTransformer's dict of cached values
        """

        stmnts = list()

        # Even though EvalTransformer *should* be in the namespace
        # where the function we're creating will be executed, it
        # doesn't seem to be able to find it, so import it again.
        #
        # This may be a latent bug, because this behavior is unexpected
        # and probably means I misunderstood some nuance of the
        # Python execution algorithm.
        #
        local_imp = 'from %s import %s' % (__name__, type(self).__name__)
        local_ref = '%s = %s.%s' % (
                self.redirect_name,
                type(self).__name__, self.redirect_global_name)

        stmnts.append(ast.parse(local_imp, mode='exec').body[0])
        stmnts.append(ast.parse(local_ref, mode='exec').body[0])

        return stmnts

    def do_for(self, stmnt):
        """
        Unroll a for loop.

        This is currently done WITHOUT checking whether the for
        loop can be replaced with a Qrepeat statement.  This might
        be done here, but it might be better done in the flattener.
        """

        name_finder = NameFinder()

        # TODO: sanity checking

        iter_copy = quickcopy(stmnt.iter)

        self.rewriter.rewrite(iter_copy)

        success, loop_values = self.eval_state.eval_expr(iter_copy)
        if not success:
            NodeError.error_msg(stmnt.iter,
                    ('could not evaluate iter expression [%s]' %
                        ast2str(stmnt.iter).strip()))
            return False, None

        # FIXME: Should loop_values here be an empty list instead of None?
        # This can be a symptom of supply a list with value of None to iterate over,
        # EG failing to handle if measChans is None: measChans = qubits
        if loop_values is None:
            DebugMsg.log("None loop values for %s" % ast2str(stmnt).strip())
            NodeError.error_msg(stmnt.iter,
                                ("Success evaluating but got None loop_values for %s" % ast2str(stmnt.iter).strip()))
            return False, None

        if not isinstance(loop_values, collections.Iterable):
            NodeError.error_msg(
                    stmnt.iter, "iter expression is not iterable")
            return False, None

        tmp_iters = TempVarManager.create_temp_var_manager(
                name_prefix='___iter')
        loop_iters_name = tmp_iters.create_tmp_name('for_iter')

        tmp_targets = TempVarManager.create_temp_var_manager(
                name_prefix='___targ')

        iters_list = list()

        targets = stmnt.target
        loop_var_names, dotted_var_names, sub_var_names = name_finder.find_names(targets)
        # print('DO FOR SUB %s' % str(sub_var_names))
        # print('EV X2 [%s][%s]' % (str(loop_var_names), dotted_var_names))

        # TODO: what should we do with dotted names?  We don't really
        # know what to do with them in a generalized way, because we
        # can't reliably tell what they represent.  For now, we'll
        # just warn the user.

        if dotted_var_names:
            NodeError.warning_msg(targets,
                    ('assignment to attributes is unreliable in QGL2 %s' %
                        str(list(dotted_var_names))))

        iters_txt = '%s = %s' % (
                loop_iters_name, ast2str(iter_copy).strip())
        iters_ast = ast.parse(iters_txt, mode='exec').body[0]
        pyqgl2.ast_util.copy_all_loc(iters_ast, stmnt.iter, recurse=True)

        # print('EVF iters_txt [%s]' % iters_txt)
        # print('EVF qgl2fname %s' % iters_ast.qgl_fname)

        self.preamble_stmnts.append(iters_ast)
        self.preamble_values.append(loop_values)

        body_template = stmnt.body
        targets_template = targets

        for loop_value in loop_values:

            new_body = quickcopy(body_template)
            new_targets = quickcopy(targets_template)

            loop_var_names, _, _ = name_finder.find_names(new_targets)
            for name in loop_var_names:
                new_name = tmp_targets.create_tmp_name(name)
                # print('EV Fl loop var %s -> %s' % (name, new_name))
                self.rewriter.add_mapping(name, new_name)

            self.rewriter.rewrite(new_targets)

            # Fake the assignment, to update the current variable bindings
            #
            self.eval_state.fake_assignment(new_targets, loop_value)

            # and now recurse, to expand this copy of the body
            #
            new_body = self.do_body(new_body)
            iters_list.extend(new_body)

            # if we've seen a "continue", then continue, but if we've
            # seen a "break", then we need to break out of this loop.
            # In either case, we need to clear the condition bits.
            #
            if self.seen_continue:
                self.seen_continue = False
            if self.seen_break:
                self.seen_break = False
                break

        # for ns in self.preamble_stmnts:
        #     print('EVF pre %s' % ast2str(ns).strip())
        # for ns in iters_list:
        #     print('EVF run %s' % ast2str(ns).strip())

        return True, iters_list

    def do_while(self, stmnt):
        """
        Evaluate/expand a "while" statement

        Like do_if, except that it may expand the body an
        arbitrary number of times (for a classical test).
        """

        if stmnt.orelse:
            NodeError.error_msg(stmnt.orelse,
                    'QGL2 while statements cannot have an else clause')
            return False, list()

        new_stmnt = quickcopy(stmnt)
        self.rewriter.rewrite(new_stmnt)

        is_classical, test = self.is_classical_test(new_stmnt.test)

        was_in_loop = self.in_loop
        self.in_loop = True

        if is_classical:
            if test:
                success, new_stmnts = self.do_classical_while(new_stmnt, test)
            else:
                success, new_stmnts = True, list()
        else:
            success, new_stmnts = self.do_quantum_while(new_stmnt)

        self.in_loop = was_in_loop
        return success, new_stmnts

    def do_classical_while(self, stmnt, test):

        # We know we're going to go through the body at
        # least once, if we get here at all (because the
        # test must have been true the first time it was
        # evaluated.
        #
        new_body = self.do_body(stmnt.body)

        while True:
            # Make a copy, so that the rewriter changes the
            # copy for the *next* iteration
            #
            stmnt = quickcopy(stmnt)
            self.rewriter.rewrite(stmnt)

            is_classical, test = self.is_classical_test(stmnt.test)
            if not is_classical:
                NodeError.error_msg(stmnt,
                        'test changed from classical to quantum?')
                return False, list()
            elif test:
                new_body += self.do_body(stmnt.body)
            else:
                break

        return True, new_body

    def do_quantum_while(self, stmnt):

        # was_in_quantum_condition = self.in_quantum_condition
        # self.in_quantum_condition = True
        # stmnt.body = self.do_body(stmnt.body)
        # self.in_quantum_condition = was_in_quantum_condition
        # return True, list([stmnt])
        NodeError.error_msg(stmnt,
            'QGL2 does not support while loops with run-time values')
        return False, list()

    def do_if(self, stmnt):
        """
        Evaluate/expand an "if" statement

        Return a tuple (success, body), where success is True
        if the expansion should be considered successful, and body
        is the resulting list of statements.

        We only handle two types of conditionals here:

        1. conditionals that involve only classical values that
            can be computed at compile-time (that DO NOT depend
            on quantum variables)

        2. a conditional based on measurement of a single
            quantum variable

            For example:

            "if MEAS(qbit0):" or "if not MEAS(qbit0)"

        It is not legal to mix the two, although the attempt
        to detect violations may be incomplete (FIXME)

        For classical conditions, we can compute the outcome at
        compiletime; we evaluate the condition, and then return
        either body statements or the orelse statements.

        For quantum conditions, we leave the work for a later pass.
        """

        self.rewriter.rewrite(stmnt)

        # check the test to see whether it is classical or quantum

        is_classical, test = self.is_classical_test(stmnt.test)

        # If we ran into an error in is_classical_test, then
        # give up immediately.  This can mean that there was a
        # quantum value hidden somewhere in the test, but it can
        # also indicate other kinds of errors.  In any case, we
        # should not continue.
        #
        if NodeError.error_detected():
            return False, list()

        was_in_loop = self.in_loop
        self.in_loop = True # TODO: check: should be False?

        if is_classical:
            success, new_stmnts = self.do_if_classical(stmnt, test)
        else:
            success, new_stmnts = self.do_if_quantum(stmnt)

        self.in_loop = was_in_loop
        return success, new_stmnts

    def is_classical_test(self, test_expr):
        """
        Test whether a test expression is known at compile-time (classical)
        or run-time (quantum).

        Return (is_classical, value), where is_classical is True if
        the expression is purely classical, False otherwise, and
        value is the truth-value of the expression if it is classical.
        (if the expression is quantum, then the truth-value must
        be determined at run-time)

        One of the ways that we test whether the expression is
        classical is by attempting to compute it; if the evaluation
        fails, then one possible reason is that it is quantum.
        If it succeeds, we save (and return) the result so that
        we can avoid re-evaluating the expression, because it
        might not be idempotent or pure, and we don't want to
        incur a second set of side effects.
        """

        # examine the variables in test_expr and return False
        # if any of those variables are run-time values
        # TODO there ought to be a recursive way to do this that
        # will be correct for a larger class of expressions
        if (isinstance(test_expr, ast.Name) and
                test_expr.id in self.runtime_variables):
            return False, False
        elif isinstance(test_expr, ast.Call):
            for arg in test_expr.args:
                if arg.id in self.runtime_variables:
                    return False, False
        elif (isinstance(test_expr, ast.UnaryOp) and
                isinstance(test_expr.op, ast.Not) and
                isinstance(test_expr.operand, ast.Name) and
                test_expr.operand.id in self.runtime_variables):
            return False, False
        elif isinstance(test_expr, ast.Compare):
            if (isinstance(test_expr.left, ast.Name) and
                test_expr.left.id in self.runtime_variables):
                return False, False
            if (isinstance(test_expr.comparators[0], ast.Name) and
                test_expr.comparators[0].id in self.runtime_variables):
                return False, False

        # If this fails, it should print out a useful
        # error message and it should set the error detection
        # bit, so that when the caller sees that that this
        # has failed, it can react accordingly.
        #
        return self.eval_state.do_test(test_expr)

    def is_measurement(self, stmnt):
        if (isinstance(stmnt, ast.Call) and
                self.eval_state.find_call_type(stmnt) == self.eval_state.QGL2MEAS):
            return True
        else:
            return False

    def do_if_classical(self, stmnt, test):

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

        # cull out toplevel pass statements
        #
        stmnt_list = [ substmnt for substmnt in stmnt_list
                if not isinstance(substmnt, ast.Pass) ]

        if len(stmnt_list) > 0:
            expanded_body = self.do_body(stmnt_list)
        else:
            expanded_body = list()

        return True, expanded_body

    def do_if_quantum(self, stmnt):
        # NOTE "quantum" condition is a misnomer. This ought to be called
        # a "runtime" condition.
        was_in_quantum_condition = self.in_quantum_condition
        self.in_quantum_condition = True

        stmnt.body = self.do_body(stmnt.body)
        if stmnt.orelse:
            stmnt.orelse = self.do_body(stmnt.orelse)

        self.in_quantum_condition = was_in_quantum_condition
        return True, list([stmnt])

    def call_checker(self, vec):
        """
        Called to do runtime type checking.

        The runtime type checks are defined by tuples of the form
        (var_name, type_name, fp_name, func, src, row, col) where

        var_name: the name of the variable to check (see below
            for how to find this in the current scope)

        type_name: the name of the type this variable must be
            (right now 'qbit' or 'classical')

        fp_name: the name of the formal parameter that will be
            bound to that var_name

        func: the name of the function being called

        src, row, col: the source file path, source row number,
            and source column number

        Note that the var_name may be the name of a temporary
        variable, which may in turn have been overwritten as
        part of a later transformation, like translation to
        single static assignment (after the check was created)
        so before looking for this name in the local scope,
        it needs to be mapped (using the rewriter) to whatever
        name it has in this context.
        """

        local_variables = self.eval_state.locals_stack[-1]

        for check in vec:
            (var_name, type_name, fp_name, func, src, row, col) = check

            mapped_name = self.rewriter.get_mapping(var_name)
            value = local_variables[mapped_name]

            # QGL2check actually does the check and prints
            # warning/error messages as needed, and sets the
            # error level accordingly, so that the caller of
            # this function can detect whether an error has
            # been detected and act accordingly
            #
            QGL2check(value, type_name, fp_name, func, src, row, col)

    def do_body(self, body):

        new_body = list()

        # We can't use an ordinary for loop over range(len(body))
        # because sometimes we restart the iteration after rewriting
        # elements of the body, and therefore the number of times
        # we execute the loop may be larger than the number of elements
        # in the body
        #
        last_index = len(body)
        stmnt_index = 0

        while stmnt_index < last_index:
            # print('stmnt_index = %d' % stmnt_index)

            # TODO: if we've seen a "break" or "continue" but we're
            # not inside a nested statement that supports these,
            # then something is wrong
            #
            if self.seen_break or self.seen_continue:
                break

            # If an error has been detected (during the previous
            # element, or somewhere within a recursive call) then
            # bail out now
            #
            if NodeError.error_detected():
                break

            stmnt = body[stmnt_index]
            stmnt_index += 1

            # deal with "op=" two-address bin-op assignments by rewriting
            # them as three-address statements.  We need this in order
            # to correctly convert to static single assignment format.
            #
            if isinstance(stmnt, ast.AugAssign):
                new_right = ast.BinOp(
                        left=quickcopy(stmnt.target),
                        right=stmnt.value,
                        op=stmnt.op)
                new_stmnt = ast.Assign(targets=[stmnt.target],
                        value=new_right)

                # print('WAS (%s) NOW (%s)' %
                #         (ast2str(stmnt), ast2str(new_stmnt)))

                pyqgl2.ast_util.copy_all_loc(new_stmnt, stmnt, recurse=True)

                stmnt = new_stmnt

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
                # If the assignment is due to qbit creation
                # then we have some housekeeping to do.
                # We create a fake value (a QubitPlaceholder instance)
                # to assign to the target, and then update the locals
                # with this binding.
                #
                # FIXME this only handles a limited set of all
                # the ways qbits might be created.  It would be
                # better to actually invoke the QubitFactory here,
                # although that would break many other things.
                #
                if is_qbit_create(stmnt):
                    self.rewriter.rewrite(stmnt.value)
                    sym_name, use_name, _node = is_qbit_create(stmnt)

                    # is_qbit_create returns the "old" style use-name,
                    # but what we need to pass to the Qubit creator
                    # is the label, which is the suffix of the use-name.
                    #
                    label_name = re.sub('QBIT_', '', use_name)
                    qbit = QubitPlaceholder.factory(stmnt, label=label_name)

                    self.allocated_qbits.add(use_name)

                    local_variables = self.eval_state.locals_stack[-1]
                    local_variables[sym_name] = qbit
                    # print('EV: QBIT CREATE %s' % ast.dump(stmnt))
                    new_body.append(stmnt)
                    continue

                # look for measurement assignments and update
                # self.runtime_variables
                # TODO handle generic computations on runtime values
                if self.is_measurement(stmnt.value):
                    self.change_cnt += 1
                    # schedule the measurement pulse(s)
                    new_stmnt = ast.Expr(value=stmnt.value)
                    pyqgl2.ast_util.copy_all_loc(new_stmnt, stmnt, recurse=True)
                    new_body.append(new_stmnt)
                    # track the return value as a runtime variable
                    if len(stmnt.targets) > 1:
                        NodeError.error_msg(stmnt,
                            'Cannot handle multiple targets in measurement assignment [%s]' % ast2str(stmnt))
                    self.runtime_variables.append(stmnt.targets[0].id)
                    continue

                # replace the names of variables in this statement with
                # the single-assignment names

                self.rewriter.rewrite(stmnt.value)

                self.rewrite_assign(stmnt)

                success, values = self.eval_state.do_assignment(stmnt)
                if success:
                    self.change_cnt += 1
                    # print('EV did assignment [%s]' % ast2str(stmnt))
                    self.preamble_stmnts.append(stmnt)
                    self.preamble_values.append(values)
                else:
                    NodeError.error_msg(stmnt,
                            'assignment failed [%s]' % ast2str(stmnt))
                    break

            elif (isinstance(stmnt, ast.Expr) and
                    isinstance(stmnt.value, ast.Call)):

                # If this is a check function, then send it
                # to the call_checker to be evaluated.
                # (The stmnt itself is ignored; all the info
                # is in the qgl2_check_vector attribute)
                #
                if hasattr(stmnt.value, 'qgl2_check_vector'):
                    self.call_checker(stmnt.value.qgl2_check_vector)
                    continue

                self.rewriter.rewrite(stmnt)

                # If it's a call to a reference to a qgl2decl, then
                # we need to do just-in-time inlining.
                #
                # We create a new with-infunc and replace its body
                # with the type checking for the call followed by
                # the inlined version of the call, and then do a
                # decrement the stmnt_index and continue to restart
                # evaluation on the expansion
                #
                ref_call = self.eval_state.expand_qgl2decl_call(stmnt.value)
                if ref_call:
                    # inject the inlined code into the body
                    body = body[:stmnt_index-1] + ref_call + body[stmnt_index:]
                    last_index += len(ref_call) - 1
                    stmnt_index -= 1
                    # body[stmnt_index] = ref_call
                    continue

                # If it's a call, we need to figure out whether it's
                # something we should leave alone, expand, or consider
                # to be an error.

                # XXX should we keep it, or get rid of it?
                call_type = self.eval_state.find_call_type(stmnt.value)
                if call_type == self.eval_state.ERROR:
                    # Ooops.  Fail hard.
                    break
                elif call_type == self.eval_state.QGL2DECL:
                    # We can't proceed, with the evaluation,
                    # but leave the stmnt in the new body,
                    # in the hope that we can expand it later.
                    #
                    NodeError.error_msg(
                            stmnt, 'internal failure: qgl2decl not inlined?')
                    new_body.append(stmnt)
                elif call_type == self.eval_state.QGL2STUB:
                    # real success
                    new_body.append(stmnt)
                elif call_type == self.eval_state.QGL2MEAS:
                    # A measurement where the user does not want to store
                    # the return value. Just schedule the control part.
                    new_body.append(stmnt)
                elif call_type == self.eval_state.NONQGL2:
                    # Do the statement for effect
                    #
                    self.eval_state.eval_expr(stmnt)
                    continue

            elif isinstance(stmnt, ast.For):
                # print('EV ast.For check')

                # NOTE: detection of simple iteration (and conversion
                # to Qrepeat, if possible) is not done here.
                # An old example of this is done in the loop unroller.
                # The do_for function only tries to expand the elts.

                success, new_stmnts = self.do_for(stmnt)
                if not success:
                    NodeError.error_msg(stmnt,
                            'failed to unroll [%s]' % ast2str(stmnt).strip())
                    continue

                new_body += new_stmnts

            elif isinstance(stmnt, ast.If):
                success, if_body = self.do_if(stmnt)
                if not success:
                    break

                new_body += if_body

            elif isinstance(stmnt, ast.While):
                success, while_body = self.do_while(stmnt)
                if not success:
                    break

                new_body += while_body

            elif isinstance(stmnt, ast.With):
                # If it's a "with" statement, then make a new "with"
                # statement with a rewritten body
                #
                # TODO: need to also rewrite the target itself,
                # because it might be an expression (like "Qrepeat(x)")

                # print('WITH %s' % ast.dump(stmnt))

                new_with = quickcopy(stmnt)
                # new_with = expr2ast('with True:\n    pass')
                # pyqgl2.ast_util.copy_all_loc(new_with, stmnt, recurse=True)
                # new_with.items = deepcopy(stmnt.items)

                for item in new_with.items:
                    self.rewriter.rewrite(item)

                new_with.body = self.do_body(new_with.body)

                # Don't add the new with statement unless there's
                # something in the body (note: we assume that "pass"
                # statements are already culled out of the body
                #
                if len(new_with.body) > 0:
                    new_body.append(new_with)

            # For "break" and "continue" statements, mark the conditions
            # and then abandon the processing of the rest of the body
            # iff we're executing this as the result of a classical
            # predicate.  If we can reach here as the result of a quantum
            # predicate, then we need to keep going.
            #
            # I don't agree with this logic. I think you need you handle
            # both cases the same way. --Blake
            elif isinstance(stmnt, ast.Break):
                # if self.in_quantum_condition:
                #     self.rewriter.rewrite(stmnt)
                #     new_body.append(stmnt)
                # else:
                #     self.seen_break = True
                #     break
                self.seen_break = True
                break
            elif isinstance(stmnt, ast.Continue):
                # if not self.in_quantum_condition:
                #     self.rewriter.rewrite(stmnt)
                #     new_body.append(stmnt)
                # else:
                #     self.seen_continue = True
                #     break
                self.seen_continue = True
                break

            elif isinstance(stmnt, ast.AugAssign):
                DebugMsg.log(
                        'unexpected AugAssign [%s]' % ast.dump(stmnt),
                        DebugMsg.HIGH)
                NodeError.fatal_msg(stmnt, 'unhandled statement (op=)')
                return new_body

            else:
                # TODO: we could add more sanity checks here,
                # looking for things that shouldn't ever happen.
                # Right now we just assume that anything else is OK,
                # but there are things that could go wrong.

                self.rewriter.rewrite(stmnt)

                new_body.append(stmnt)
                print('EV unhandled [%s]' % ast.dump(stmnt))

        # If we've pruned everything out of the body,
        # then insert a pass statement to keep things
        # syntactically correct
        #
        # TODO should this be done here?  Probably better
        # to let the caller decide whether to insert something
        #
        # if len(new_body) == 0:
        #     new_pass = ast.Pass()
        #     pyqgl2.ast_util.copy_all_loc(new_pass, body[0])
        #     new_body.append(new_pass)

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
