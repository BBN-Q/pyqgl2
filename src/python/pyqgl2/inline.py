# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import ast
import meta
import numpy as np

from pyqgl2.ast_util import NodeError, expr2ast
from pyqgl2.importer import NameSpaces
from pyqgl2.importer import collapse_name
from pyqgl2.lang import QGL2
from pyqgl2.quickcopy import quickcopy
from pyqgl2.qreg import QRegister, QReference

import pyqgl2.ast_util
import pyqgl2.scope

from pyqgl2.ast_util import ast2str

class TempVarManager(object):
    """
    Manages the state needed to create variable names
    that are (with high probability) unique across
    the entire program

    These variable names are typically used to create
    temporary variable names, needed to serve as local
    variables in the place of formal parameters after
    a function is inlined.
    """

    # There may be more than one TempVarManager, with different
    # rules for constructing names.  This is the map from
    # base names to instances of TempVarManager

    NAME2REF = dict()

    def __init__(self):

        # These are intentionally bogus values, to make
        # sure that a TempVarManager that didn't get created
        # via create_temp_var_manager() will fail if it
        # is ever used.
        #
        self.name_prefix = None
        self.index = None

    @staticmethod
    def create_temp_var_manager(name_prefix='___qgl2_tmp'):
        if name_prefix in TempVarManager.NAME2REF:
            return TempVarManager.NAME2REF[name_prefix]

        new_ref = TempVarManager()
        new_ref.name_prefix = name_prefix
        new_ref.index = 0

        TempVarManager.NAME2REF[name_prefix] = new_ref
        return new_ref

    def create_tmp_name(self, orig_name=None):
        self.index += 1

        base = '%s_%.3d' % (self.name_prefix, self.index)
        if orig_name:

            # if the name that we're converting to a temp
            # is already a temp name, then try to find the
            # original root name and use that name instead.
            #
            components = orig_name.split(self.name_prefix, 1)
            if len(components) == 2:
                orig_name = components[0]

            return '%s%s' % (orig_name, base)
        else:
            return base


class NameRewriter(ast.NodeTransformer):

    def __init__(self):
        self.name2name = dict()
        self.name2const = dict()

    def visit_Name(self, node):
        """
        Rewrite a Name node to replace it with a "constant"
        (which may be another name) or to replace it with
        a reference to a different name, if possible.
        """

        # Note: we update older references to point to
        # newer references, so that subsequent traversals are
        # faster.  This will help speed up long loops where
        # the same symbols appear multiple times.
        # For example, if we find a chain like W -> X -> Y -> Z
        # we'll change the mapping for W and X to point to Z so
        # the next time we need to lookup W or X, it's faster.

        start_id = node.id

        while (node.id in self.name2const) or (node.id in self.name2name):
            # If we can absorb this name into a constant, do so.
            # Otherwise, see if the name has been remapped to a
            # local temp, and use that name.

            if node.id in self.name2const:
                node = self.name2const[node.id]

                # re-point to current tail
                self.name2const[start_id] = node
                break
            elif node.id in self.name2name:
                node.id = self.name2name[node.id]

                # re-point to next element in chain
                self.name2name[start_id] = node.id

        return node

    def visit_Expr(self, node):
        """
        If the expression is a Call, then rewrite the original call
        as well, so that we can find the bindings later
        """

        if hasattr(node, 'qgl2_orig_call'):
            node.qgl2_orig_call = self.rewrite(node.qgl2_orig_call)

        self.generic_visit(node)
        return node

    def add_constant(self, old_name, value_ptree):
        """
        Add a mapping from a name to a "constant" value that
        can replace that name in the current context
        """

        # A little sanity checking
        #
        assert isinstance(old_name, str), \
                ('old_name [%s] must be a string' % str(old_name))
        assert isinstance(value_ptree, ast.AST), \
                ('value_ptree [%s] must be an AST node ' %
                        str(type(value_ptree)))

        self.name2const[old_name] = value_ptree

    def add_mapping(self, old_name, new_name):
        """
        Add a mapping from a name to another name (typically
        the name of a temporary variable that replaces a
        formal parameter when a function is inlined).
        """

        # A little sanity checking
        #
        assert isinstance(old_name, str), \
                ('old_name [%s] must be a string' % str(old_name))
        assert isinstance(new_name, str), \
                ('new_name [%s] must be a string' % str(new_name))

        self.name2name[old_name] = new_name

    def get_mapping(self, name):
        start_name = name

        while (name in self.name2const) or (name in self.name2name):
            # If we can absorb this name into a constant, do so.
            # Otherwise, see if the name has been remapped to a
            # local temp, and use that name.

            if name in self.name2const:
                name = self.name2const[name].id
                break
            elif name in self.name2name:
                name = self.name2name[name]

                # re-point to next element in chain
                self.name2name[start_name] = name

        return name

    def rewrite(self, ptree, mapping=None, constants=None):
        """
        Write all the Name nodes in the given AST parse tree
        according to the current name2name mapping, and return
        the resulting tree.

        This method is destructive; it modifies the tree in-place
        """

        if mapping:
            for name in mapping.keys():
                self.add_mapping(name, mapping[name])

        if constants:
            for name in constants.keys():
                self.add_constant(name, constants[name])

        new_ptree = self.visit(ptree)

        # Keep a copy of the rewriter, so we can track variables
        # that might be removed during the inlining process.  We
        # care about things like whether the original code referenced
        # qbits, even if the inlined code does not
        #
        new_ptree.qgl2_rewriter = quickcopy(self)

        return new_ptree

def is_qgl2_def(node):
    """
    Return True if the node has been marked as the
    definition of a QGL2 function, False otherwise

    Note: doesn't do any sanity checking on node.
    """

    return (hasattr(node, 'qgl_func') and node.qgl_func)

def is_qgl2_stub(node):
    '''
    Return True if the node has been marked as a QGL2
    stub for a QGL1 function, else False.
    '''
    return (hasattr(node, 'qgl_stub') and node.qgl_stub)

def is_qgl2_meas(node):
    '''
    Return True if the node has been marked as a QGL2 measurement.
    '''
    return (hasattr(node, 'qgl_meas') and node.qgl_meas)

def check_call_actuals(call_ptree):
    """
    Check whether a function is invoked with *args or **kwargs
    explicitly.  We can't handle this right now, so we want to
    treat it as an error elsewhere.

    If the actual parameters can't be handled, then emit a message
    and return False; otherwise return True
    """

    # TODO: sanity checks on input

    if isinstance(call_ptree.func, ast.Name):
        func_name = call_ptree.func.id
    else:
        func_name = 'anon'

    for arg in call_ptree.args:
        if isinstance(arg, ast.Starred):
            NodeError.error_msg(call_ptree,
                    ('function %s() has *args' % func_name))
            return False

    for arg in call_ptree.keywords:
        if arg.arg is None:
            NodeError.error_msg(call_ptree,
                    ('function %s() has **kwargs' % func_name))
            return False

    return True

def check_func_parameters(func_ptree):
    """
    If the function uses **kwargs, then punt on inlining.
    This isn't necessarily error, but it defeats inlining (for now).

    Note that Python permits many combinations of positional parameters,
    keyword parameters, as well as *args, and **kwargs, and we only
    support a small subset of them: a call with positional or keyword
    parameters, and possibly an *args, but NOT **kwargs parameters.

    We might want to expand the number of cases we handle, but this
    captures a lot of the common cases.
    """

    # TODO: sanity checks on input

    if func_ptree.args.kwarg:
        NodeError.error_msg(func_ptree,
                ('function %s() has **kwargs' % func_ptree.name))
        return False

    return True

def make_symtype_check(symname, symtype, actual_param, fpname):
    """
    Create and return AST that performs a check that the given symbol
    has the given type, and prints and error message and halts if
    a type violation is detected.  This AST is intended to be inserted
    into the original program to check that the actual parameters to
    a function or procedure match the declared types.

    The actual_param is used to create the error message.

    The way that types are specified is a little clunky.
    In addition to literal types (like str, int, etc) there is also
    at least one "anti-type", 'classical', which matches any type
    that isn't quantum.

    TODO: this doesn't handle aggregate types, like lists of
    qbits, yet.
    """

    # If we're passed a type instead of a name of a type,
    # then convert it.
    #
    # (This shouldn't happen right now, but it might be possible
    # in the future.)
    #
    if isinstance(symtype, type):
        # TODO: this method of finding the name of the type
        # might not be portable.  I haven't checked whether this
        # is from the spec, or just the way CPython works
        #
        symtype = symtype.__name__

    check_ast = None

    errcode = 'NodeError._emit_msg(NodeError.NODE_ERROR_ERROR, \'%s\')'

    if symtype == QGL2.CLASSICAL:
        txt = NodeError._create_msg(
                actual_param, NodeError.NODE_ERROR_ERROR,
                '[%s] declared classical, got quantum' % fpname)
        expr = (('if isinstance(%s, QubitPlaceholder): ' % symname) +
                (errcode % txt))
        check_ast = expr2ast(expr)
    elif symtype == QGL2.QBIT:
        txt = NodeError._create_msg(
                actual_param, NodeError.NODE_ERROR_ERROR,
                '[%s] declared quantum, got classical' % fpname)
        expr = (('if not isinstance(%s, QubitPlaceholder): ' % symname) +
                (errcode % txt))
        check_ast = expr2ast(expr)
    else:
        txt = NodeError._create_msg(
                actual_param, NodeError.NODE_ERROR_ERROR,
                '[%s] does not match declared type [%s]' % (fpname, symtype))
        expr = ('if not isinstance(%s, %s): %s' %
                    (symname, symtype, errcode % txt))
        check_ast = expr2ast(expr)

    if check_ast:
        pyqgl2.ast_util.copy_all_loc(check_ast, actual_param, recurse=True)

    return check_ast

def find_param_annos(func_args):
    """
    Return a dictionary of param_name -> annotation.id for all of the
    formal parameter names mentioned in the given func_args (which is
    assumed to be an ast.arguments instance) that have annotations
    """

    annos = dict()

    args = func_args.args + func_args.kwonlyargs
    for arg in args:
        if arg.annotation:
            if not isinstance(arg.annotation, ast.Name):
                NodeError.fatal_msg(
                        arg, 'annotation of param [%s] not a symbol' % arg.id)
                return None

            annos[arg.arg] = arg.annotation.id

    # NOTE: we ignore annotations on *args or **kwargs.
    # (we ignore **kwargs in general...)
    # Not sure how to interpret annotations on varargs; have
    # not investigated.

    return annos

def find_param_names(func_args):
    """
    Return a set of all of the formal parameter names mentioned
    in the given func_args (which is assumed to be an ast.arguments
    instance)
    """

    names = set()

    args = func_args.args + func_args.kwonlyargs
    for arg in args:
        name = arg.arg
        if name in names:
            NodeError.fatal_msg(
                    arg, 'param name [%s] appears more than once' % name)
            return None

        names.add(name)

    if func_args.vararg:
        name = func_args.vararg.arg

        if name in names:
            NodeError.fatal_msg(
                    arg, 'param name [%s] appears more than once' % name)
            return None

        names.add(name)

    if func_args.kwarg:
        name = func_args.kwarg.arg

        if name in names:
            NodeError.fatal_msg(
                    arg, 'param name [%s] appears more than once' % name)
            return None

        names.add(name)

    return names

def find_param_bindings(call_ptree, func_ptree):
    """
    Walks through the call AST ptree, to the function defined
    by the given FunctionDef AST ptree, and matches up the formal
    and actual parameters.

    Returns (status, names, name2actual) where

    - status is True if the matching succeeded, or False otherwise.
        if status is False, names and names2actual have no defined
        meaning and should be ignored.

    - names is a list of all of the formal parameters in the order
        in which they appear in the call (with defaulted parameters
        appearing after all of the non-defaulted parameters).  We
        preserve this (rather than just using the declared order of
        the formal parameters) because if evaluation the actuals has
        any side effect, then we want to preserve the order as such.

    - name2actual is a dictionary from formal parameter name to
        actual parameter expressions (which are AST instances from
        the call_ptree).

    This is more complex than it sounds, given Python's wealth
    of different ways to say the same thing (positional parameters
    vs keyword parameters, *args, and **kwargs).

    TODO: we do not support calling with *args or **kwargs (although we do
    support them as formal parameters).  Adding this should be possible,
    although the resulting code will be more complex.
    """

    status = True
    names = list()
    name2actual = dict()

    pos_actual_params = call_ptree.args
    formal_params = func_ptree.args.args

    if func_ptree.args.vararg:
        has_starargs = True
        star_name = func_ptree.args.vararg.arg
    else:
        has_starargs = False

    # Basic sanity checking...
    #
    if (len(pos_actual_params) > len(formal_params)) and not has_starargs:
        # Not exactly the same as the Python3 error message,
        # but close enough
        #
        NodeError.error_msg(call_ptree,
                ('%s() takes %d positional arguments but %d were given' %
                    (func_ptree.name,
                        len(pos_formal_params), len(actual_params))))
        return False, names, name2actual

    param_ind = 0
    while param_ind < len(pos_actual_params):
        if param_ind < len(formal_params):
            formal_param = formal_params[param_ind]

            orig_name = formal_param.arg
            actual_param = pos_actual_params[param_ind]
            name2actual[orig_name] = actual_param
            names.append(orig_name)

            param_ind += 1
        elif has_starargs:
            star_value = ast.List(
                    elts=pos_actual_params[param_ind:])
            name2actual[star_name] = star_value
            names.append(star_name)

            # TODO: is it possible to have an annotation on starargs?
            # If so, how should it be interpreted?
            # NOTE: we assume this is impossible/irrelevant right now

            break
        else:
            NodeError.error_msg(call_ptree,
                     'too many positional arguments')
            return False, names, name2actual

    # If there's a declared starargs, but no values found for
    # it, we still need to assign it an empty list.  We create
    # out out of thin air and copy the position of the call_ptree
    # into it.
    #
    if has_starargs:
        if star_name not in name2actual:
            star_value = ast.List(elts=list())
            pyqgl2.ast_util.copy_all_loc(star_value, call_ptree, recurse=True)
            name2actual[star_name] = star_value
            names.append(star_name)

    # Then consider each keyword-specified parameter.
    # TODO: we blindly accept keyword parameters even
    # if the keywords don't match any formal parameters.
    # This should be checked.
    #
    # Also note that we DO NOT address **kwargs.
    #
    kw_actual_params = call_ptree.keywords

    while param_ind < len(kw_actual_params):
        arg = kw_actual_params[param_ind]
        orig_name = arg.arg
        actual_param = arg.value

        if orig_name not in name2actual:
            name2actual[orig_name] = actual_param
            names.append(orig_name)
        else:
            NodeError.error_msg(call_ptree,
                     'parameter (%s) is defined more than once' % orig_name)
            status = False
            continue

    if not status:
        return False, names, name2actual

    # Next, add any values for any parameters that weren't explicitly
    # specified by the call, but which have default values specified
    # as part of the function definition

    pos_defaults = func_ptree.args.defaults
    if pos_defaults:
        num_pos = len(formal_params)

        # make a slice of just the formal positional parameters
        # that have defaults; this simplifies computing the
        # array offsets
        #
        pos_defaulted_params = formal_params[-len(pos_defaults):]

        for param_ind in range(len(pos_defaulted_params)):
            orig_name = pos_defaulted_params[param_ind].arg
            if orig_name not in name2actual:
                # need to copy the default AST, because we're going
                # to annotate it with the location of the call.
                value = quickcopy(pos_defaults[param_ind])
                pyqgl2.ast_util.copy_all_loc(value, call_ptree, recurse=True)
                name2actual[orig_name] = value
                names.append(orig_name)

    kw_defaults = func_ptree.args.kw_defaults
    if kw_defaults:
        for param_ind in range(len(kw_defaults)):
            orig_name = func_ptree.args.kwonlyargs[param_ind].arg
            if orig_name not in name2actual:
                # need to copy the default AST, because we're going
                # to annotate it with the location of the call.
                value = quickcopy(kw_defaults[param_ind])
                pyqgl2.ast_util.copy_all_loc(value, call_ptree, recurse=True)
                name2actual[orig_name] = value
                names.append(orig_name)

    # Finally we check to see whether there are any positional
    # parameters we haven't seen in either form, and chide
    # the user if there are any missing.
    #
    fp_names = find_param_names(func_ptree.args)

    for fp_name in fp_names:
        if fp_name not in name2actual:
            # Not very much like the standard Python3 error msg,
            # but reasonably close
            #
            NodeError.error_msg(call_ptree,
                    ('%s() missing parameter: \'%s\'' %
                        (func_ptree.name, fp_name)))
            return False, names, name2actual

    return True, names, name2actual

def create_inline_procedure(func_ptree, call_ptree):
    """
    Given a ptree rooted at a FuncDefinition, create
    an equivalent ptree for an "inline" version of the
    ptree.

    Note that this procedure is specialized for use
    with "procedures", not general functions.  A procedure
    is a function that does not contain any return statements.
    (There are ways to handle return statements, but they
    are ugly and make later optimization more difficult,
    so we are beginning with procedures)

    We can only inline non-recursive procedures.  No
    attempt is made to transform recursive procedures
    into non-recursive procedures, or even detect
    non-recursive procedures.

    The basic mechanism is:

    1. Create a list of new local variables, one for each
        of the formal parameters of the function

        These local variables are drawn from a namespace
        that will not conflict with other variables in the
        program.

    2. Create a list of statements that assigns the evaluation
        of the expressions in the actual parameters to the
        corresponding local variables that represent the formal
        parameters

        Steps 1 and 2 are complicated by needing to handle
        keyword arguments.  Note: we DO NOT handle *args
        and **kwargs right now.

        Note: as a special case, "constant" actual parameters
        may be substituted as-is for their formal parameters,
        without using local variables.  These variables
        are removed from the list of new local variables.

    3. Create a copy of the body of the original function

    4. Find all "local" variables created in the body of
        the original function, not including the formal
        parameters.  Create a new name for each of these
        variables (based on each original name)

        This is done to avoid conflicts with variables of
        the same name in the new scope of the body.

    5. Rewrite all references to the formal parameters and
        local variables in the
        copy of the body to be references to the local variables
        with the new names.

    6. Append the list from #2 and the list from #5 and return it.
    """

    failed = False

    # sanity checking: this has to start with a FunctionDef
    # and a Call.  Otherwise, we can't do anything with it.
    #
    if not isinstance(func_ptree, ast.FunctionDef):
        NodeError.error_msg(call_ptree,
                'first arg must be FunctionDef, not %s' % type(func_ptree))
        return None

    if not isinstance(call_ptree, ast.Call):
        NodeError.error_msg(call_ptree,
                'second arg must be Call, not %s' % type(call_ptree))
        return None

    if not is_qgl2_def(func_ptree):
        NodeError.warning_msg(call_ptree,
                'skipping inlining [%s]: not declared QGL2' % func_ptree.name)
        return None

    if is_qgl2_stub(func_ptree):
        # FIXME: Is this block needed. Running AllXY it
        # is never executed.
        print('SKIP QGL1 Stub NAME %s' % func_ptree.name)
        return None

    # print('FUNC NAME %s' % func_ptree.name)

    # Check whether this is a function we can handle.
    #
    if not check_func_parameters(func_ptree):
        NodeError.fatal_msg(call_ptree,
                'cannot inline call to function [%s]' % func_ptree.name)
        return None

    if not check_call_actuals(call_ptree):
        NodeError.fatal_msg(call_ptree,
                'cannot inline call to function [%s]' % func_ptree.name)
        return None

    # TODO: check that the name of the called function
    # matches the function definition?

    rewriter = NameRewriter()

    tmp_names = TempVarManager.create_temp_var_manager()

    func_ptree = quickcopy(func_ptree)

    func_body = func_ptree.body
    formal_params = func_ptree.args.args

    actual_params = quickcopy(call_ptree.args)
    keyword_actual_params = quickcopy(call_ptree.keywords)

    new_func_body = list()

    # Note: the first version of QGL2 did not permit functions
    # that had formal parameters of *args or **kwargs, but users
    # have noted that some idioms become awkward without *args.
    # So, I'm going to add them back in and see what the consequences
    # are.  Note that there's no type checking on *args parameters;
    # we assume that if there's a type error it will be caught later.
    #
    # Also note that we do not support all of the *args
    # bells and whistles, and we don't support functions that
    # are called by *args/**kwargs as their actuals.

    # check whether there's a *args lurking
    #
    has_starargs = func_ptree.args.vararg is not None

    # TODO: check that there's only one *args.  We don't understand
    # what to do with more than one.

    # Examine the call, and build the code to assign
    # the actuals to the formals.
    #
    # Python gets a bit complicated with functions that mix
    # *args and keyword args: the keyword args must come after
    # the *args, and cannot be treated as positional, but
    # if there isn't a *args, then positional args map onto
    # keyword args.

    # parameters that we've already processed (to make sure
    # that we don't do something as both an ordinary and keyword
    # parameter, and make sure that all the keyword parameters
    # get initialized
    #
    # For each actual parameter, figure out what formal parameter
    # it belongs with.  We don't have to worry about most of the
    # illegal cases because the Python parser should have detected
    # them.
    #

    status, param_names, name2actual = find_param_bindings(
            call_ptree, func_ptree)

    """
    name2actual = dict()
    param_names = list()

    if has_starargs:
        star_name = func_ptree.args.vararg.arg

    param_ind = 0
    while param_ind < len(actual_params):
        if param_ind < len(formal_params):
            formal_param = formal_params[param_ind]

            orig_name = formal_param.arg
            actual_param = actual_params[param_ind]
            name2actual[orig_name] = actual_param
            param_names.append(orig_name)

            param_ind += 1
        elif has_starargs:
            star_value = ast.List(
                    elts=actual_params[param_ind:])
            name2actual[star_name] = star_value
            param_names.append(star_name)

            # TODO: is it possible to have an annotation on starargs?
            # If so, how should it be interpreted?
            # NOTE: we assume this is impossible/irrelevant right now

            break
        else:
            NodeError.error_msg(call_ptree,
                     'too many positional arguments')
            failed = True

    # If there's a declared starargs, but no values found for
    # it, we still need to assign it an empty list
    #
    if has_starargs:
        if star_name not in name2actual:
            name2actual[star_name] = ast.List(elts=list())
            param_names.append(star_name)

    # Then consider each keyword-specified parameter.
    # TODO: we blindly accept keyword parameters even
    # if the keywords don't match any formal parameters.
    # This should be checked.
    #
    # Also note that we DO NOT address **kwargs.
    #
    while param_ind < len(call_ptree.keywords):
        arg = call_ptree.keywords[param_ind]
        orig_name = arg.arg
        actual_param = arg.value

        if orig_name not in name2actual:
            name2actual[orig_name] = actual_param
            param_names.append(orig_name)
        else:
            NodeError.error_msg(call_ptree,
                     'parameter (%s) is defined more than once' % orig_name)
            failed = True
            continue

    if failed:
        return None

    # Next, add any values for any parameters that weren't explicitly
    # specified by the call, but which have default values specified
    # as part of the function definition

    pos_defaults = func_ptree.args.defaults
    if pos_defaults:
        num_pos = len(formal_params)

        # make a slice of just the formal positional parameters
        # that have defaults; this simplifies computing the
        # array offsets
        #
        pos_defaulted_params = formal_params[-len(pos_defaults):]

        for param_ind in range(len(pos_defaulted_params)):
            orig_name = pos_defaulted_params[param_ind].arg
            if orig_name not in name2actual:
                name2actual[orig_name] = pos_defaults[param_ind]
                param_names.append(orig_name)

    kw_defaults = func_ptree.args.kw_defaults
    if kw_defaults:
        for param_ind in range(len(kw_defaults)):
            orig_name = func_ptree.args.kwonlyargs[param_ind].arg
            if orig_name not in name2actual:
                name2actual[orig_name] = kw_defaults[param_ind]
                param_names.append(orig_name)

    # Finally we check to see whether there are any positional
    # parameters we haven't seen in either form, and chide
    # the user if there are any missing.
    #
    fp_names = find_param_names(func_ptree.args)

    for fp_name in fp_names:
        if fp_name not in name2actual:
            # Not very much like the standard Python3 error msg,
            # but reasonably close
            #
            NodeError.error_msg(call_ptree,
                    ('%s() missing parameter: \'%s\'' %
                        (func_ptree.name, fp_name)))
            failed = True
    """

    if failed:
        return None

    # Potential optimizations: many other possible cases TODO
    #
    # 1. If an actual parameter is a reference or a constant, and
    # isn't reassigned, then we can just pass it in as such;
    # no need to give it a local name.
    #
    # 2. If an actual parameter is reassigned before use,
    # no need to do the initial ap -> fp assignment.
    #
    # There are many possible cases, and their analyses are
    # complicated.  For now we're going to ignore them and
    # just treat all actual parameters in the default way.
    # We can't go wrong this way.

    # Now rescan the list of locals, looking for any we might
    # be able to reduce to constants.
    #
    constants = list()
    setup_locals = list()

    annos = find_param_annos(func_ptree.args)

    # iterate over param_names so that we process the parameters
    # in the calling order (at least except for *args) instead
    # of declared order.  They may differ if keyword parameters
    # are used.
    #
    for name in param_names:
        actual = name2actual[name]

        # FIXME: this interacts badly with doing eval-time error checking,
        # because letting the "constants" through untouched removes
        # an opportunity to check them (which can currently only be done
        # for things assigned to symbols
        #

        # TODO: only considering the most basic cases right now.
        # There are many other cases we could potentially handle.
        #
        if ((isinstance(actual, ast.Num) or
                isinstance(actual, ast.Str) or
                isinstance(actual, ast.Name) or
                isinstance(actual, ast.NameConstant)) and
                is_static_ref(func_ptree, name)):
            rewriter.add_constant(name, actual)

        else:
            new_name = rewriter.get_mapping(name)
            setup_locals.append(ast.Assign(
                    targets=list([ast.Name(id=new_name, ctx=ast.Store())]),
                    value=actual))

        # print('ARG %s = %s' %
        #         (name, pyqgl2.ast_util.ast2str(actual)))
        # print('ARG %s = %s' % (name, ast.dump(actual)))

    # Now rewrite any local variable names to avoid conflicting
    # with other names in the in-lined scope
    #
    local_names = find_local_names(func_ptree)
    new_local_names = set()
    for name in local_names:
        # if it's not a parameter, then we haven't
        # already set up a new name for it, so do so here
        #
        if name not in name2actual:
            new_local_names.add(name)
            new_name = tmp_names.create_tmp_name(orig_name=name)
            rewriter.add_mapping(name, new_name)

    # We need to annotate the code for setting up each local
    # with a reasonable line number and file name (even though
    # it's all fictitious) so that any error messages generated
    # later make some sense
    #
    source_file = call_ptree.qgl_fname
    for assignment in setup_locals:
        for subnode in ast.walk(assignment):
            subnode.qgl_fname = source_file

            pyqgl2.ast_util.copy_all_loc(assignment, call_ptree, recurse=True)

    # placeholder for more actual checking.
    for name in param_names:
        if name in annos:
            anno_type = annos[name]
            if anno_type:
                # print('CHECK that %s param %s is a %s' %
                #         (func_ptree.name, name, anno_type))
                # FIXME: do something
                pass

    # Make a list of all of the formal parameters declared to be qbits,
    # and use this to define the barrier statements for this call
    #
    qbit_fparams = list()
    qbit_aparams = list()

    for name in param_names:
        if (name in annos) and (annos[name] == QGL2.QBIT):

            # If we get a parameter that's not an ast.Name, but it's declared
            # to be a qbit, then we know that the type checking is going
            # to fail.  Return an empty list now and let the error checker
            # figure out what happened.
            #
            # TODO: what if the expression isn't a const?
            #
            if not isinstance(rewriter.name2const[name], ast.Name):
                # FIXME: returning an empty list here is probably wrong
                return list()

            qbit_fparams.append(name)
            qbit_aparams.append(rewriter.name2const[name].id)

    qbit_aparams_txt = ', '.join(sorted(qbit_aparams))

    # Now check whether any formal qbit parameters map onto
    # the same actual, by examining the name rewriter.
    qbit_aparams_reverse = dict()
    for qbit_fparam in qbit_fparams:

        # a qbit will, by this point, have an entry in the
        # name2const map that points back to the original variable
        # name bound to the qbit.  This is what we're comparing
        # against -- which is imperfect, because we don't prevent
        # the same qbit from being bound to multiple variables.
        #
        # A more important problem is that since we are tracing
        # this back to the original name, we don't have a simple
        # way to tell the user what the *local* name is, which
        # is usually more useful
        #
        qbit_aparam = rewriter.name2const[qbit_fparam].id
        if qbit_aparam in qbit_aparams_reverse:
            NodeError.error_msg(call_ptree,
                    'dup qbit [%s] used for [%s] and [%s]' % (
                        qbit_aparam,
                        qbit_aparams_reverse[qbit_aparam], qbit_fparam))
            return None
        else:
            qbit_aparams_reverse[qbit_aparam] = qbit_fparam

    # We want to preserve a reference to the original call,
    # and make sure it doesn't get clobbered.
    #
    # I'm not sure whether we need to make a complete copy
    # of the original call_ptree, but it won't hurt
    #
    orig_call_ptree = quickcopy(call_ptree)

    isFirst = True
    for stmnt in func_body:
        # Skip over method docs
        if (isFirst and isinstance(stmnt, ast.Expr) and
                isinstance(stmnt.value, ast.Str)):
            isFirst = False
            continue
        isFirst = False

        new_stmnt = rewriter.rewrite(stmnt)
        ast.fix_missing_locations(new_stmnt)
        new_func_body.append(new_stmnt)

        # If it's any kind of a control-flow statement, then
        # it needs to get executed on all of the qbits in
        # the context of the original call, so link back
        # to the original call, but if it's an expression,
        # then it only needs to execute on the qbits that
        # it references directly.
        #
        if not isinstance(new_stmnt, ast.Expr):
            new_stmnt.qgl2_orig_call = orig_call_ptree

    inlined = setup_locals + new_func_body

    return inlined

class NameFinder(ast.NodeVisitor):
    """
    A visitor for finding the names referenced by a node

    See find_names() for more info
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.simple_names = set()
        self.dotted_names = set()
        self.array_names = set()

    def visit_Attribute(self, node):
        name = collapse_name(node)
        self.dotted_names.add(name)

    def visit_Name(self, node):
        self.simple_names.add(node.id)

    def visit_Subscript(self, node):
        self.array_names.add(node.value.id)

    def find_names(self, node):
        """
        Find the simple names (purely local names) and the
        "dotted" names (attributes of an instance, class,
        or module) referenced by a given AST node.

        Returns (simple, dotted, array) where "simple" is the set
        of simple names, "dotted" is the set of dotted names,
        and "array" is the set of array names (i.e. subscripted
        symbols, which may be lists, dictionaries, or anything
        else that can be subscripted -- not just arrays).

        Note that this skips NameConstants, because these
        names are fixed symbols in Python 3.4+ and cannot be
        renamed or modified (and therefore they're not really
        "local" names at all).
        """

        self.reset()
        self.visit(node)

        return self.simple_names, self.dotted_names, self.array_names

    def find_local_names(self, node):
        """
        A specialized form of find_names that only returns the
        simple local names, discarding the dotted and array names
        """

        simple, _dotted, _array = self.find_names(node)
        return simple


class NameRedirector(ast.NodeTransformer):
    """
    A visitor for finding the names referenced by a node

    See find_names() for more info
    """

    def __init__(self, values=None, table_name='_T'):

        self.table_name = table_name
        self.values = values

    def visit_Attribute(self, node):
        return node

    def visit_Name(self, node):

        name = node.id
        # if the name doesn't have an entry in the values
        # table, then we can't transform it
        #
        if name not in self.values:
            return node

        # If the value is something we can represent
        # by value (i.e. an integer, or a list of strings) then
        # replace its reference with its value rather than
        # replacing the reference with a reference to the new
        # table.
        #
        # As special case, we replace references to qubits
        # with their special QBIT_ name.  This is a bit of
        # a hack; the downstream code expects to see just
        # the name.
        #
        # TODO: add a comment, if possible, with the name of the variable

        value = self.values[name]

        numpy_scalar_types = (
            np.int8, np.int16, np.int32, np.int64,
            np.uint8, np.uint16, np.uint32, np.uint64,
            np.float16, np.float32, np.float64,
            np.complex64, np.complex128
        )
        if (isinstance(value, int) or isinstance(value, float) or
                isinstance(value, numpy_scalar_types)):
            redirection = ast.Num(n=value)
        elif isinstance(value, str):
            redirection = ast.Str(s=value)
        elif isinstance(value, QRegister):
            redirection = ast.Name(id=value.use_name(), ctx=ast.Load())
            redirection.qgl_is_qbit = True
        elif isinstance(value, QReference):
            if isinstance(value.idx, slice):
                lower = ast.Num(n=value.idx.start) if value.idx.start else None
                upper = ast.Num(n=value.idx.stop) if value.idx.stop else None
                step = ast.Num(n=value.idx.step) if value.idx.step else None
                idx = ast.Slice(lower, upper, step)
            else:
                idx = ast.Index(ast.Num(n=value.idx))
            redirection = ast.Subscript(value=ast.Name(id=value.use_name(), ctx=ast.Load()),
                                        slice=idx,
                                        ctx=ast.Load())
            redirection.qgl_is_qbit = True
        elif hasattr(value, '__iter__'):
            # for simple (non-nested) iterables, try parsing the repr()
            # of the value, and then replacing QRegisters as above
            try:
                redirection = ast.parse(repr(value)).body[0].value
                for ct, element in enumerate(value):
                    if isinstance(element, QRegister):
                        redirection.elts[ct] = ast.Name(id=element.use_name(),
                                                        ctx=ast.Load())
                        redirection.elts[ct].qgl_is_qbit = True
            except:
                NodeError.warning_msg(node,
                    "Could not represent the value [%s] of [%s] as an AST node" % (value, name))
                redirection = ast.Subscript(
                        value=ast.Name(id=self.table_name, ctx=ast.Load()),
                        slice=ast.Index(value=ast.Str(s=name)))
        else:
            NodeError.warning_msg(node,
                "Could not represent the value [%s] of [%s] as an AST node" % (value, name))
            redirection = ast.Subscript(
                    value=ast.Name(id=self.table_name, ctx=ast.Load()),
                    slice=ast.Index(value=ast.Str(s=name)))

        return redirection

def names_in_ptree(ptree):
    """
    Return a set of all of the Name strings in ptree

    Useful for finding the names of symbols defined via
    assignment in expressions, particulary tuples, which
    may be nested arbitrarily deeply.

    Skips NameConstants, because these values can't be
    overridden by assignment (or at least they really
    shouldn't be).
    """

    names = set()
    if not ptree:
        return names

    for node in ast.walk(ptree):
        if isinstance(node, ast.Name):
            names.add(node.id)

    return names

def is_name_in_ptree(name, ptree):
    """
    Return True if an ast.Name node with the given name as its id
    appears anywhere in the ptree, False otherwise
    """

    if not ptree:
        return False

    for node in ast.walk(ptree):
        if isinstance(node, ast.Name) and (node.id == name):
            return True

    return False

def is_static_ref(ptree, name):
    """
    Scan the given ptree to see whether the given name can be replaced
    with a static reference (to a value, or to a more complex expression)

    Names can be replaced if they are not reassigned.
    (there are other cases, but we're doing the simple case first)

    A return of False doesn't necessarily imply that we need to hang
    on to the variable, but it means that we've been unable to prove
    that we can discard it, so we should keep it.
    """

    # Wander through the tree, looking for any place where the
    # symbol is used as the target of an assignment.  This is more
    # complicated than it sounds, because there are many places
    # where implicit assignments can be hidden (and I'm probably
    # missing some), such as loop variables.  Most of these should
    # be flagged as warnings (for example, using a loop variable
    # that overshadows a formal parameter is virtually always a
    # programming error) but we don't attempt to judge here.
    #
    for node in ast.walk(ptree):
        if isinstance(node, ast.Assign):
            if is_name_in_ptree(name, node.targets[0]):
                # This isn't an error, but it's something we'd
                # like to deprecate, because it hinders optimization
                NodeError.warning_msg(node,
                        ('parameter [%s] overwritten by assignment ' % name))
                return False

        elif isinstance(node, ast.AugAssign):
            if is_name_in_ptree(name, node.target):
                # Like Assignment
                NodeError.warning_msg(node,
                        ('parameter [%s] overwritten by assignment ' % name))
                return False

        elif isinstance(node, ast.For):
            if is_name_in_ptree(name, node.target):
                NodeError.warning_msg(node,
                        ('parameter [%s] overshadowed by loop variable' %
                            name))
                return False

        elif isinstance(node, ast.With):
            for item in node.items:
                if is_name_in_ptree(name, item.optional_vars):
                    NodeError.warning_msg(item,
                            ('parameter [%s] overshadowed by "as" variable' %
                                name))
                    return False

        elif isinstance(node, ast.Try):
            # check all the handlers; the way these
            # are represented isn't like the other constructs
            # so we can't just look for ast.Names
            #
            for handler in node.handlers:
                if handler.name == name:
                    NodeError.warning_msg(handler,
                            ('parameter [%s] overshadowed by "as" variable' %
                                name))
                    return False

    # If the name survived all of those checks, then return True.
    #
    return True

def create_inline_function(ptree, actual_params=None):
    """
    Like create_inline_procedure, but for a function.
    The first four steps are the same, but then there is
    additional work on the copy of the body:

    a) Create a local name for the return value, if any

        It is not required that a function return a value;
        a naked return statement may also be used as
        non-local control flow

    b) Scan the body, searching for return statements;
        replace them with code that assigns the returned
        value (if any) to the local variable and then
        raises an InlineReturn exception.

    c) Wrap the body in a try block that catches all
        InlineReturn exceptions and ignores all others.

    Note: if there are any promiscuous except clauses
    in the body that catch InlineReturn exceptions,
    this may fail!

    Finally, paste new try block to the end of the list
    of statements to assign the formal parameters...

    But we're not done yet: if the function actually
    does return anything, then make sure that the
    assignment from the return value of the call is
    replaced with an assignment from the local variable
    assigned by the individual return statements.
    This step can't be done here, but needs to be
    done in the calling context.  To make this easier,
    set node.qgl_retname to name of the temporary
    variable.
    """

    pass

def is_qgl_procedure(node):
    """
    Return True if the node represents a function that
    may be treated as a QGL procedure (i.e. it was
    declared to be a QGL function, and it contains
    no "return" statements or expressions), False otherwise
    """

    # First, check that it's a function definition.
    #
    if not isinstance(node, ast.FunctionDef):
        return False

    if not is_qgl2_def(node):
        return False
    # print('FUNC NAME %s' % node.name)

    if not node.qgl_func:
        return False

    # Don't inline qgl stubs
    if node.qgl_stub:
        return False

    for stmnt in node.body:
        for subnode in ast.walk(stmnt):
            if isinstance(subnode, ast.Return):
                return False

    return True

def find_local_names(ptree, preserve_set=None):
    """
    Find and return a set of all of the "local names"
    in the given ptree.  These are the names of variables
    that may be brought into existence within the context of this
    ptree.

    Unfortunately, the most we can say is that they *may* be
    created this way.  They may have been created in a surrounding
    context (i.e. a nested function definition, or a lambda, etc).
    We get confused about these right now.

    TODO: mark the tree as we go, so we can deal with nested
    constructs, closures, etc.
    """

    local_names = set()

    if not ptree:
        return local_names

    for node in ast.walk(ptree):
        # TODO: look for "local" and "global" declarations
        # and process them
        pass

    # We don't do any checking here for things like duplicate
    # names (for loop variables, etc).
    # We could check for multiple definitions, but we wouldn't
    # know which one came "first" the way we do for overshadowed
    # parameters.
    #
    # TODO: we could add some diagnostic for duplicate names
    #
    for node in ast.walk(ptree):
        if isinstance(node, ast.Assign):
            # find all variables, possibly buried in tuples
            new_names = names_in_ptree(node.targets[0])
        elif isinstance(node, ast.For):
            # find all the loop variables
            new_names = names_in_ptree(node.target)
        elif isinstance(node, ast.With):
            # find all of the "as" variables in node.items
            new_names = set()
            for item in node.items:
                new_names.update(names_in_ptree(item.optional_vars))
        elif isinstance(node, ast.Try):
            # find all of the "as" variables in node.handlers
            new_names = set()
            for handler in node.handlers:
                new_names.add(handler.name)
        else:
            continue

        local_names.update(new_names)

    return local_names


class Inliner(ast.NodeTransformer):

    def __init__(self, importer):
        super(Inliner, self).__init__()

        self.importer = importer
        self.change_cnt = 0

    def reset_change_count(self):
        self.change_cnt = 0

    def inline_function(self, funcdef):
        """
        Iteratively expand a ptree that represents a function
        definition by expanding as many of the calls it makes
        as possible, and then return the resulting function
        definition.

        Also places a copy of the function (with a new name)
        in the same namespace as the original function.

        This would be more elegant to do recursively, but we use
        ast.walk() in a few places, and it can't tolerate having
        the ptree change out from under it.
        """

        if not isinstance(funcdef, ast.FunctionDef):
            NodeError.fatal_msg(funcdef,
                    'expected ast.FunctionDef got [%s]' % str(type(funcdef)))

        if not is_qgl2_def(funcdef):
            # unexpected: all FunctionDef nodes should be marked
            return funcdef

        namespace = self.importer.path2namespace[funcdef.qgl_fname]

        # If we haven't already done a scope check for this function,
        # do it now (and marked it as checked)
        #
        if not hasattr(funcdef, 'qgl2_scope_checked'):
            funcdef.qgl2_scope_checked = True

            pyqgl2.scope.scope_check(
                    funcdef,
                    module_names=namespace.all_names,
                    global_names=namespace.native_globals)

        new_ptree = quickcopy(funcdef)

        while True:
            change_count = self.change_cnt
            new_body = self.inline_body(new_ptree.body)
            if not new_body:
                # This shouldn't happen?
                break

            # If we didn't make any changes, then we're finished
            #
            if change_count == self.change_cnt:
                break

            new_ptree.body = new_body
            # print('MODIFIED CODE:\n%s' % pyqgl2.ast_util.ast2str(new_ptree))

        # Create a new version of this function, with a new name,
        # and add it to the namespace of the original function
        #
        temp_manager = TempVarManager.create_temp_var_manager()
        new_name = temp_manager.create_tmp_name(new_ptree.name)
        new_ptree.name = new_name

        self.importer.add_function(namespace, new_name, new_ptree)

        funcdef.qgl_inlined = new_ptree

        return new_ptree

    def make_checked_call(self, call_ptree):
        """
        Given a call, see if we can turn it into a "checked call",
        which includes checks that the call is made with parameters
        of the desired type.

        Returns the original call_ptree if no expansion occurs.
        Returns a list of statements if the expansion occurs
        (not that this list might only contain one statement, if
        the expansion is trivial).  The caller can determine whether
        any transformation was made (or attempted) by looking at
        the return type; an ast.Call means nothing was modified,
        and a list means something was (potentially) changed.

        For example, if we have a call like

            foo(a, b, c) # a, b, and c are arbitrary expressions

        and we have the definition of foo and know that it declares
        that the parameters of foo must be of type int, str, and list,
        then this would turn into something like:

            tmp_a = a
            tmp_b = b
            tmp_c = c
            assert isinstance(tmp_a, int)
            assert isinstance(tmp_b, str)
            assert isinstance(tmp_c, list)
            foo(tmp_a, tmp_b, tmp_c)

        FIXME: This is about half working -- the positional args are
        more or less correct, but the keyword args are not started.
        """

        if not isinstance(call_ptree, ast.Call):
            NodeError.error_msg(base_call, 'not a call')
            return call_ptree

        func_filename = call_ptree.qgl_fname
        func_name = collapse_name(call_ptree.func)

        func_ptree = self.importer.resolve_sym(func_filename, func_name)
        if not func_ptree:
            # This isn't necessarily an error.  It could be an
            # innocent library function that we don't have a
            # definition for, and therefore can't inline it.
            #
            NodeError.diag_msg(
                    call_ptree, 'definition for %s() not found' % func_name)
            return call_ptree

        if is_qgl_procedure(func_ptree):
            NodeError.diag_msg(
                    call_ptree, '%s() is qgl2decl; skipping' % func_name)
            # We don't do anything with qgl2decl procedures right now
            # (they get handled inside the inliner).  Someday we might
            # want to unify this, but we don't do this right now.

            print('PUNTING ON call to %s' % func_name)

            return call_ptree

        elif is_qgl2_stub(func_ptree):
            NodeError.diag_msg(
                    call_ptree, '%s() is a qgl2stub' % func_name)
            # TODO: add checking...
            print('STUB STUB!')
            tmp_var = TempVarManager.create_temp_var_manager()

            call_expr = ast.Expr(value=call_ptree)
            pyqgl2.ast_util.copy_all_loc(call_expr, call_ptree)

            new_assignments = list()
            new_args = list()
            new_kwargs = list()

            print('AST STC %s' % ast.dump(call_ptree))
            print('AST FPC %s' % ast.dump(func_ptree))

            # 1. make a new assignment for each actual parameter, unless
            #    the value is a symbol or number.
            # 2. add type checks for each tmp variable
            # 3. construct new call with the tmps as the actuals

            for ind in range(len(call_ptree.args)):
                ap_arg = call_ptree.args[ind]
                fp_arg = func_ptree.args.args[ind]

                # if there's no annotation for this formal parameter,
                # then we can't do a type check.  Just add the actual
                # to new_args.
                #
                # If it's a symbol, then we can check the
                # type in-place and don't need to make a copy.
                if not fp_arg.annotation:
                    print('NEWNAME3 %s %s' % (ap_arg.id, fp_arg.id))
                    new_args.append(ap_arg)
                    continue

                if isinstance(ap_arg, ast.Name):
                    new_name = ap_arg.id
                    to_check = ap_arg
                    new_args.append(ap_arg)
                    print('NEWNAME2 %s' % new_name)
                else:
                    new_name = tmp_var.create_tmp_name(orig_name=fp_arg.arg)
                    to_check = ast.Name(id=new_name)
                    new_args.append(to_check)

                    # NOTE: need to copy location info into to_check.
                    # FIXME (every new AST created needs to have a
                    # location assigned properly)

                    val_str = pyqgl2.ast_util.ast2str(ap_arg).strip()
                    expr = '%s = %s' % (new_name, val_str)
                    print('NEWNAME %s old %s' % (new_name, val_str))
                    new_assignments.append(expr2ast(expr))

                # def make_symtype_check(symname, symtype, actual_param, fpname):
                print('CHECK name %s type %s fpname %s' %
                        (new_name, fp_arg.annotation.id, fp_arg.arg))
                check = make_symtype_check(
                        new_name, fp_arg.annotation.id, ap_arg, fp_arg.arg)
                print('CHECKA %s' % pyqgl2.ast_util.ast2str(check).strip())
                new_assignments.append(check)

            for kwarg in call_ptree.keywords:
                if (isinstance(kwarg.value, ast.Name) or
                        isinstance(kwarg.value, ast.Num)):
                    new_kwargs.append(kwarg)
                else:
                    new_name = tmp_var.create_tmp_name()
                    new_kwargs.append(
                            ast.keyword(
                                arg=kwarg.arg, value=ast.Name(id=new_name)))
                    val_str = pyqgl2.ast_util.ast2str(kwarg.value).strip()
                    expr = '%s = %s' %  (new_name, val_str)
                    new_assignments.append(expr2ast(expr))

            for x in new_assignments:
                print('NA %s' % pyqgl2.ast_util.ast2str(x).strip())

            new_call = quickcopy(call_ptree)
            new_call.args = new_args
            new_call.keywords = new_kwargs
            new_call = ast.Expr(value=new_call)

            # FAKE, FIXME
            return new_assignments + [new_call] # fake

        else:
            NodeError.diag_msg(
                    call_ptree, '%s() is not QGL2; not touching ' % func_name)
            return call_ptree

    def add_runtime_checks(self, call_ptree):

        # We should always be passed an ast.Call; gripe if it
        # isn't one.
        #
        if not isinstance(call_ptree, ast.Call):
            print('add_runtime_checks: not a call (%s)' %
                    ast2str(call_ptree).strip())
            return None

        # If it's already marked as checked, then don't bother to
        # attempt to add any checks.
        #
        if hasattr(call_ptree, 'qgl2_checked_call'):
            # print('Already have check for [%s]' % func_name)
            return None

        func_filename = call_ptree.qgl_fname

        if not isinstance(call_ptree.func, ast.Name):
            NodeError.error_msg(
                    call_ptree,
                    ('cannot inline function expression [%s]'
                        % ast2str(call_ptree).strip()))
            return None

        func_name = collapse_name(call_ptree.func)
        func_ptree = self.importer.resolve_sym(func_filename, func_name)

        if func_ptree:
            return add_runtime_call_check(call_ptree, func_ptree)
        else:
            # print('add_runtime_checks: no definition for [%s]' % func_name)
            return None

    def inline_body(self, body):
        """
        inline a list of expressions or other statements
        (e.g. the body of a "for" loop) and return a
        corresponding list of expressions (which might be
        the same list, if there were no changes)

        Increments self.change_cnt if the new body is
        different than the original body.  The exact
        value of self.change_cnt should not be
        interpreted as the number of "changes" made
        (because this concept is not defined) but
        increases when changes are made.  If a ptree
        is visited and the change_count is not changed,
        then no changes were made.
        """

        new_body = list()

        for stmnt_ind in range(len(body)):
            stmnt = body[stmnt_ind]

            if not isinstance(stmnt, ast.Expr):
                new_stmnt = self.visit(stmnt)
                new_body.append(new_stmnt)
                continue

            if not isinstance(stmnt.value, ast.Call):
                new_stmnt = self.visit(stmnt)
                new_body.append(new_stmnt)
                continue

            call_ptree = stmnt.value

            runtime_check = self.add_runtime_checks(call_ptree)
            if runtime_check:
                (chk_assts, chk_checks, chk_call) = runtime_check
                new_body += chk_assts
                new_body += chk_checks

                # if we added any checks, then count this as
                # a change (even though it may be invisible,
                # we don't want to throw away the side effects)
                #
                if len(chk_assts) or len(chk_checks):
                    self.change_cnt += 1

                # Do not append the checked call to the new body:
                # we're going to try to inline it below.
                # Replace the value of the current stmnt and the
                # call_ptree with the chk_call, so that the right
                # call is fed to the inliner
                #
                call_ptree = chk_call.value
                stmnt.value = call_ptree

            inlined = inline_call(call_ptree, self.importer)
            if isinstance(inlined, ast.Call):
                stmnt.value = inlined
                new_body.append(stmnt)
            elif isinstance(inlined, list):
                new_body += inlined
                self.change_cnt += 1

            if inlined != call_ptree:
                NodeError.diag_msg(
                        call_ptree,
                        ('inlined call to %s' %
                            ast2str(call_ptree).strip()))
            else:
                NodeError.diag_msg(
                        call_ptree,
                        ('did not inline call to %s' %
                            ast2str(call_ptree).strip()))

        return new_body

    def visit_FunctionDef(self, node):
        node.body = self.inline_body(node.body)
        return node

    def visit_For(self, node):
        node.body = self.inline_body(node.body)
        node.orelse = self.inline_body(node.orelse)
        return node

    def visit_While(self, node):
        node.body = self.inline_body(node.body)
        node.orelse = self.inline_body(node.orelse)
        return node

    def visit_If(self, node):
        node.body = self.inline_body(node.body)
        node.orelse = self.inline_body(node.orelse)
        return node

    def visit_With(self, node):
        node.body = self.inline_body(node.body)
        return node

    def visit_Try(self, node):
        node.body = self.inline_body(node.body)
        node.orelse = self.inline_body(node.orelse)
        node.finalbody = self.inline_body(node.finalbody)
        return node


def funcdef_has_type_anno(func_ptree):
    """
    Return True if we can find any type annotation in the
    given function definition, False otherwise
    """

    assert isinstance(func_ptree, ast.FunctionDef), \
            'expected a function definition'

    found_anno = False
    for fparam in func_ptree.args.args:
        if fparam.annotation:
            found_anno = True
            break

    return found_anno

def make_check_ast(symname, typename, src_ast, fp_name, fun_name):

    chk_txt = '%s(\'%s\', \'%s\')' % (QGL2.CHECK_FUNC, fun_name, fp_name)

    chk_ast = expr2ast(chk_txt)
    pyqgl2.ast_util.copy_all_loc(chk_ast, src_ast, recurse=True)
    chk_ast.value.qgl2_checked_call = True

    chk_args = make_check_tuple(
            symname, typename, src_ast, fp_name, fun_name)

    chk_ast.value.qgl2_check_vector = list([chk_args])

    return chk_ast

def make_check_ast_vec(fun_name, src_ast, vec):

    chk_ast = expr2ast('%s(\'%s\')' % (QGL2.CHECK_FUNC, fun_name))

    chk_ast.value.qgl2_checked_call = True
    chk_ast.value.qgl2_check_vector = vec

    pyqgl2.ast_util.copy_all_loc(chk_ast, src_ast, recurse=True)

    return chk_ast


def make_check_tuple(symname, typename, src_ast, fp_name, fun_name):

    check_tuple = (
            symname, typename, fp_name, fun_name,
            src_ast.qgl_fname, src_ast.lineno, src_ast.col_offset)

    return check_tuple

def add_runtime_call_check(call_ptree, func_ptree):
    """
    Insert runtime checks for valid parameters for the given call
    to the given function.

    If the function does not have parameter type annotations, then
    we can't add checks, and we just return None.  The caller
    needs to handle this case; it doesn't mean that the function
    shouldn't be called, etc.

    NOTE: we're treating this call as a statement because we
    assume that it's not being used as an expression.  THIS IS
    NOT GENERALLY TRUE and we'll need to handle the general
    case soon.

    If the function has parameter type annotations, then
    for each parameter with a type annotation, we need to add a check.
    The current process is described below: it could be made more
    efficient by handling special cases more elegantly, but efficiency
    is not a high priority for compile-time type checking (at this time),
    so we're aiming for simplicity instead.

    1. Create a tmp symbol name for each typed formal parameter.

    2. Create an assignment statement that assigns each formal parameter
        to the corresponding tmp symbol.

    3. Create a new call to the func specified by the func_ptree
        that uses the value bound to the tmp symbol names as its actual
        parameters

    4. For each symbol created in step 1, create a statement to check that
        it is of the correct type, with error messages that match the
        location information in the corresponding actual parameter.

    5. Put together a statement list containing the statements from
        steps 2, 4, and 3.

        The symbol bindings and checks from steps 2 and 4 can be interleaved
        (if that makes it easier to implement), but all of steps 2 and 4
        must be finished before step 4.

    So, for example, if we had a function defined list:

    @qgl2decl
    def foo(a: classical, b: qbit) -> classical:
        return a # we don't care about the body here

    and then a call to foo like:

        foo(x + y, q)

    We would transform this call from

        [ foo(x + y, q) ]

    to something like:

        [
            tmp_a = x + y,
            tmp_b = q,
            if not is_classical(tmp_a): print('a must be classical'); fail(),
            if not is_qbit(tmp_b) : print('b must be a qbit'); fail(),
            foo(tmp_a, tmp_b)
        ]

    A subtle note is how to handle a call to a function that has
    some of its formal parameters annotated with types, but not all.
    (maybe this will be illegal someday, but right now partial types
    are permitted...)  It is tempting to only perform this transformation
    on actual parameters that can be type checked, i.e.

        def foo(a, b, c: qbit):
            pass

        foo(x(), y(), z())

    Would be transformed to something like:

        tmp_z = z()
        QGL2check(z, 'qbit', ...)
        foo(x(), y(), tmp_z)

    But this reorders the evaluation of the expressions in the
    call (z() is called before x() and y()), and this can change
    the behavior of the program if any of these functions have
    side effects (and the ability of Python to create non-obvious
    side effects makes this impractical to check).  We need
    to preserve the relative order of evaluation across all the
    actual parameters.
    """

    if not funcdef_has_type_anno(func_ptree):
        return None

    # print('CALL AST %s' % ast.dump(call_ptree))
    # print('FUNC AST %s' % ast.dump(func_ptree))

    tmp_names = TempVarManager.create_temp_var_manager()

    tmp_assts = list()
    tmp_checks = list()
    params_seen = set()

    pos_args = list()
    kw_args = list()

    tmp_check_tuples = list()

    # make sure that the user hasn't provided more args
    # than the function was declared to take...
    #
    max_argcnt = len(func_ptree.args.args)
    act_argcnt = len(call_ptree.args)

    if max_argcnt < act_argcnt:
        NodeError.error_msg(
                call_ptree,
                ('too many parameters to %s (%d given, max %d)' %
                    (func_ptree.name, act_argcnt, max_argcnt)))
        return None

    # Regular args in the call first:
    for arg_index in range(act_argcnt):
        fp_name = func_ptree.args.args[arg_index].arg
        params_seen.add(fp_name)

        ap_node = call_ptree.args[arg_index]
        if isinstance(ap_node, ast.Name):
            # If the ap is already a name, then we can use it as-is.
            new_name = ap_node.id
            pos_args.append(ap_node)
        else:
            new_name = tmp_names.create_tmp_name(orig_name=fp_name)
            new_ast = expr2ast(
                    '%s = %s' % (new_name, ast2str(ap_node).strip()))
            pyqgl2.ast_util.copy_all_loc(new_ast, ap_node, recurse=True)
            tmp_assts.append(new_ast)

            pos_args.append(new_ast.targets[0])

        anno = func_ptree.args.args[arg_index].annotation
        if anno:
            if not isinstance(anno, ast.Name):
                NodeError.error_msg(
                        anno, 'a type annotations must be a name')
                return None

            check_tuple = make_check_tuple(
                    new_name, anno.id, call_ptree, fp_name, func_ptree.name)
            tmp_check_tuples.append(check_tuple)

    # Then kwargs in the call:
    #
    # (there's a lot of commonality here with the regular args,
    # and perhaps it can be simplified, but there are differences)
    #
    for arg_index in range(len(call_ptree.keywords)):
        ap_node = call_ptree.keywords[arg_index]
        fp_name = ap_node.arg

        # TODO: add the same short-cut as we use for positional
        # parameters for aps that are already names

        # NOTE: this test isn't always exercised right now,
        # because the AST parser currently fails when it tries
        # to parse a call with a repeated keyword parameter.
        # But we need it to detect when a kw arg shadows
        # a positional arg.  Unfortunately, this means that
        # the user may see two different error messages for
        # what is essentially the same bug.
        #
        if fp_name in params_seen:
            NodeError.error_msg(
                    call_ptree,
                    ('[%s] parameter [%s] multiply defined' %
                        (func_ptree.name, fp_name)))
            return None

        params_seen.add(fp_name)

        new_name = tmp_names.create_tmp_name(orig_name=fp_name)

        new_ast = expr2ast('%s = %s' %
                        (new_name, ast2str(ap_node.value).strip()))
        pyqgl2.ast_util.copy_all_loc(new_ast, ap_node, recurse=True)
        tmp_assts.append(new_ast)
        kw_args.append((fp_name, new_name))

        # We need to scan through the function definition to find
        # whether there's an annotation for this parameter
        #
        anno = None
        for arg in func_ptree.args.args:
            if arg.arg == fp_name:
                if arg.annotation:
                    anno = arg.annotation

        if anno:
            if not isinstance(anno, ast.Name):
                NodeError.error_msg(
                        anno, 'type annotations must be names')
                return None

            check_tuple = make_check_tuple(
                    new_name, anno.id, call_ptree, fp_name, func_ptree.name)
            tmp_check_tuples.append(check_tuple)

    # We pass all the parameters to the new call as keyword arguments.
    # Python doesn't care, and it makes things easier for us if we don't
    # have to keep track of args vs kwargs.
    #
    args_txt = ''
    if pos_args:
        args_txt += ', '.join(
                ['%s' % ast2str(arg).strip() for arg in pos_args])

    if pos_args and kw_args:
        args_txt += ', '

    if kw_args:
        args_txt += ', '.join(['%s=%s' % arg for arg in kw_args])

    new_call_txt = '%s(%s)' % (func_ptree.name, args_txt)

    # print('NEW CALL TXT %s' % new_call_txt)

    new_call_ast = expr2ast(new_call_txt)

    pyqgl2.ast_util.copy_all_loc(new_call_ast, call_ptree, recurse=True)
    new_call_ast.value.qgl2_checked_call = True

    # mark the call with the return type (if any) of the checked call
    if hasattr(func_ptree, 'qgl_return'):
        new_call_ast.value.qgl_return = func_ptree.qgl_return

    if tmp_check_tuples:
        checker = make_check_ast_vec(
                func_ptree.name, call_ptree, tmp_check_tuples)
        tmp_checks = list([checker])
    else:
        tmp_checks = list()

    return tmp_assts, tmp_checks, new_call_ast


def inline_call(base_call, importer):
    """
    Recursively expand a function by inlining all the
    procedure calls it can discover within the given
    call.

    Returns either a call (if the call can't
    be inlined) or a list of expressions that
    should replace the call.  The call may be
    the original call (or a copy of it) or it
    may be a call to an optimized version of
    the function originally called.

    In order to be inlined, a method must be declared
    to be a QGL function, and it must not be a class
    or instance method (it may be static), and it must
    be a "procedure" (no return statements).

    base_call is the AST for the call to the function.
    This AST is assumed to be annotated with the QGL2
    extensions (via the importer) so that the name of
    the source file, and the namespace, etc, are available.
    """

    # find the function being called; try to inline it.
    # then for each call in the body of the function
    # (whether or not the body was inlined), try to inline
    # that call.  Continue until every possible inline
    # has been exhausted (or the stack blows up) and then
    # stitch all the results together.

    if not isinstance(base_call, ast.Call):
        NodeError.error_msg(base_call, 'not a call')
        return base_call

    if not isinstance(base_call.func, ast.Name):
        NodeError.error_msg(
                base_call,
                ('function not called by name [%s]' %
                    ast2str(base_call).strip()))
        return base_call

    func_filename = base_call.qgl_fname
    func_name = collapse_name(base_call.func)

    func_ptree = importer.resolve_sym(func_filename, func_name)
    if not func_ptree:
        # This isn't necessarily an error.  It could be an
        # innocent library function that we don't have a
        # definition for, and therefore can't inline it.
        #
        NodeError.diag_msg(base_call,
                'definition for %s() not found' % func_name)
        return base_call

    if not is_qgl_procedure(func_ptree):
        if is_qgl2_stub(func_ptree):
            NodeError.diag_msg(base_call,
                               '%s() is a QGL1 stub' % func_name)
        else:
            NodeError.diag_msg(base_call,
                               '%s() is not a QGL2 procedure' % func_name)
        # we can't inline this call, because it doesn't
        # appear to be a QGL2 procedure.  But if we have
        # the definition of the function, we can try to
        # optimize it by inlining its calls.

        # If we haven't already inlined this, then try to
        # do so here, and then stash the inlined version
        # of the function with the function definition
        #
        if func_ptree.qgl_stub:
            # We don't inline / rewrite the names of QGL1 stubs
            new_func = func_ptree
        elif not hasattr(func_ptree, 'qgl_inlined'):
            inliner = Inliner(importer)
            new_func = inliner.inline_function(func_ptree)
        else:
            new_func = func_ptree.qgl_inlined

        # if we didn't change the function, then we don't
        # need to change the call either
        #
        if new_func == func_ptree:
            return base_call
        else:
            # make a copy of the call, and then edit it to call
            # the new function.
            #
            new_call = quickcopy(base_call)

            # TODO: check what namespace the inlined function
            # lives in, and make sure that it gets put back
            # there.  For example, if new_call.func is an
            # Attribute instead of a Name, this probably fails.
            #
            if not isinstance(new_call, ast.Name):
                NodeError.diag_msg(new_call,
                        'unexpected attribute')
            new_call.func.id = func_ptree.qgl_inlined.name

            return new_call

    else:
        # Analyze the function for potential scope errors, if we
        # haven't already.
        #
        # The analysis doesn't depend on the calling context (so
        # we get the same result each time), so once the function
        # definition has been marked as qgl2_scope_checked, we don't
        # check it again.
        #
        if not hasattr(func_ptree, 'qgl2_scope_checked'):
            func_ptree.qgl2_scope_checked = True

            namespace = importer.path2namespace[func_ptree.qgl_fname]

            loc_syms = namespace.all_names
            if not pyqgl2.scope.scope_check(
                    func_ptree, module_names=loc_syms,
                    global_names=namespace.native_globals):
                return None

        inlined = create_inline_procedure(func_ptree, base_call)
        if not inlined:
            NodeError.diag_msg(base_call,
                    'inlining of %s() failed' % func_name)
            return base_call

        return inlined


class TestInliner(object):

    def init_code(self, text):
        importer = NameSpaces('<test>', text=text)
        ptree = importer.path2ast['<test>']
        func = ptree.body[0]

        return importer, ptree

    CODE1 = """
@qgl2decl
def foo(a, b, c):
    dummy(a + b + c)
foo(1, 2, 3)
"""

    def test_1(self):

        code = self.CODE1
        importer, ptree = self.init_code(code)
        func_def = ptree.body[0]
        func_call = ptree.body[1].value

        ptree.body = create_inline_procedure(func_def, func_call)
        post = meta.asttools.dump_python_source(ptree)
        print('test_1 POST:\n%s' % post)

    CODE2 = """
@qgl2decl
def foo(a=1, b=2, c=3):
    dummy(a + b + c)
foo()
foo(x(12))
foo(d=12)
foo(10, 20)
foo(10, 20, 30)
foo(c='c', b='b', a='a')
foo(c='c', a='a')
"""

    def test_2(self):

        code = self.CODE2
        importer, ptree = self.init_code(code)
        func_def = ptree.body[0]

        scratch = deepcopy(ptree)

        print('CODE:\n%s' % code)
        for call in range(1, len(ptree.body)):
            scratch.body = create_inline_procedure(
                    func_def, ptree.body[call].value)
            post = meta.asttools.dump_python_source(scratch)
            print('test_2 %d POST:\n%s' % (call, post))

    CODE3 = """
@qgl2decl
def foo(a, b, c='c'):
    dummy(a + b + c)
foo()
foo(1)
foo(1, 2)
foo(1, 2, 3)
foo(1, 2, 3, c=44)
foo(1, 2, 3, 4)
"""

    def test_3(self):

        code = self.CODE3
        importer, ptree = self.init_code(code)
        func_def = ptree.body[0]

        scratch = deepcopy(ptree)

        print('CODE:\n%s' % code)
        for call in range(1, len(ptree.body)):
            scratch.body = create_inline_procedure(
                    func_def, ptree.body[call].value)
            if scratch.body:
                post = meta.asttools.dump_python_source(scratch)
                print('test_3 %d POST:\n%s' % (call, post))
            else:
                print('test_3 %d failed' % call)

    CODE4 = """
@qgl2func
def foo(a, b):
    a = 1
    dummy(a + b)
foo(x, y)
"""

    def test_4(self):
        code = self.CODE4
        importer, ptree = self.init_code(code)
        func_def = ptree.body[0]
        func_def = ptree.body[0]

        scratch = deepcopy(ptree)

        print('CODE:\n%s' % code)
        for call in range(1, len(ptree.body)):
            scratch.body = create_inline_procedure(
                    func_def, ptree.body[call].value)
            if scratch.body:
                post = meta.asttools.dump_python_source(scratch)
                print('test_4 %d POST:\n%s' % (call, post))
            else:
                print('test_4 %d failed' % call)

    REWRITER_CODE = """
a = 1
b = 2
c = a + b
d = a + b + c
e = foo(a + b, c + d)
f = bar(d(a, b) + c(c, d))
"""

    def test_rewriter(self):

        rewrites = {
                'a' : 'alpha',
                'b' : 'beta',
                'c' : 'gamma',
                'd' : 'delta'
        }

        ptree = ast.parse(self.REWRITER_CODE)

        rewriter = NameRewriter()
        pre = meta.asttools.dump_python_source(ptree)
        new_ptree = rewriter.rewrite(ptree, rewrites)
        post = meta.asttools.dump_python_source(new_ptree)

        print('PRE:\n%s' % pre)
        print('POST:\n%s' % post)

    CODE_INLINER = """
@qgl2decl
def foo(a, b):
    dummy(a + b, a - b)
foo(12, 13)
"""

    def test_inliner(self):

        code = self.CODE_INLINER
        importer, ptree = self.init_code(code)
        ptree = importer.path2ast['<test>']

        call_ptree = ptree.body[1].value

        inline_call(call_ptree, importer)

    CODE_MODULE = """
@qgl2func
def foo(a, b):
    a = 1
    dummy(a + b)
x = 2
y = 200
foo(x, y)
"""

    def test_module(self):
        code = self.CODE_MODULE
        importer, ptree = self.init_code(code)
        func_def = ptree.body[0]

        inlined = create_inline_procedure(ptree.body[0], ptree.body[3].value)

        new_body = list([ptree.body[0]]) + inlined + ptree.body[1:]
        new_module = ast.Module(body=new_body)
        # print('NEW BODY\n%s' % ast.dump(new_module))
        print('AS CODE\n%s' % meta.asttools.dump_python_source(new_module))

    CODE_FORLOOP = """
@qgl2decl
def aaa(a, b, c):
    bbb(a, a + b, a + c)
@qgl2decl
def bbb(a, b, c):
    ccc(a, a + b, a + c)

@qgl2decl
def ccc(a, b, c):
    print(a, b, c)

@qgl2decl
def foobar(x, y=88, z=89):
    for zz in [1, 2, 3]:
        qqq = 3
        aaa(x, y, z)

@qgl2main
def main():
    foobar(x=1, y=2, z=3)
"""

    def test_forloop(self):
        code = self.CODE_FORLOOP
        importer, ptree = self.init_code(code)

        print('AST %s' % ast.dump(ptree))
        print('INPUT CODE\n%s' % pyqgl2.ast_util.ast2str(ptree))

        if not importer.qglmain:
            print('error: no qglmain??')
            return

        inliner = Inliner(importer)
        new_ptree = inliner.inline_function(importer.qglmain)

        print('RESULT CODE\n%s' % pyqgl2.ast_util.ast2str(new_ptree))

        print('ORIG foobar\n%s' % pyqgl2.ast_util.ast2str(
                importer.path2ast[importer.base_fname]))


if __name__ == '__main__':

    def main():
        """
        test driver (for very simple tests)
        """

        tester = TestInliner()

        tester.test_forloop()

        tester.test_rewriter()
        tester.test_1()
        tester.test_2()
        tester.test_3()
        tester.test_4()

        tester.test_module()

        tester.test_inliner()

    main()
