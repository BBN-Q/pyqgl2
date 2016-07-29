# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import ast
import meta

from copy import deepcopy

from pyqgl2.ast_util import NodeError, expr2ast
from pyqgl2.importer import NameSpaces
from pyqgl2.importer import collapse_name
from pyqgl2.lang import QGL2

import pyqgl2.ast_util
import pyqgl2.scope

class BarrierIdentifier(object):

    NEXTNUM = 1

    @staticmethod
    def next_bid():
        nextnum = BarrierIdentifier.NEXTNUM
        BarrierIdentifier.NEXTNUM += 1
        return nextnum


class QubitPlaceholder(object):
    """
    Placeholder for a Qubit/Channel

    It would be preferable to use the actual Qubit object
    here, but that requires closer integration with QGL1
    """

    # mapping from label to reference
    KNOWN_QUBITS = dict()

    def __init__(self, use_name):
        self.use_name = use_name

    @staticmethod
    def factory(use_name, **kwargs):

        mapping = QubitPlaceholder.KNOWN_QUBITS

        if use_name not in mapping:
            mapping[use_name] = QubitPlaceholder(use_name, **kwargs)
        return mapping[use_name]


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

        # If we can absorb this name into a constant, do so.
        # Otherwise, see if the name has been remapped to a
        # local temp, and use that name.

        if node.id in self.name2const:
            node = self.name2const[node.id]
        elif node.id in self.name2name:
            node.id = self.name2name[node.id]

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
        return self.name2name[name]

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
        new_ptree.qgl2_rewriter = deepcopy(self)

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

def check_call_parameters(call_ptree):
    """
    If the function uses *args and/or **kwargs, then punt on inlining.
    This isn't an error, but it defeats inlining (for now).

    Note that Python permits many combinations of positional parameters,
    keyword parameters, as well as *args, and **kwargs, and we only
    support a small subset of them:

    1) A call with positional or keyword parameters, but NO *args or
    **kwargs parameters.

    2) A call with one *args and/or one **kwargs parameters (if both
    are supplied, then the *args MUST come first, as required by
    ordinary Python syntax) but NO positional or keyword parameters

    We do consider it an error if we see any other combination
    of parameter types, and try to provide a meaningful error message.

    We might want to expand the number of cases we handle, but this
    captures a lot of the common cases.
    """

    # print('CALL TREE %s' % ast.dump(call_ptree))

    # TODO: sanity checks on input

    # Check positional arguments:
    #
    # if there's a stararg, then there must be exactly one stararg
    # and it must be the only positional arg
    #
    stararg_cnt = 0
    kwarg_cnt = 0

    funcname = collapse_name(call_ptree.func)

    posarg_cnt = len(call_ptree.args)
    keyword_cnt = len(call_ptree.keywords)

    for posarg in call_ptree.args:
        if isinstance(posarg, ast.Starred):
            stararg_cnt += 1

    if (stararg_cnt > 0):
        if stararg_cnt > 1:
            NodeError.error_msg(call_ptree,
                    ('call to %s() has multiple *args' % funcname))
            return False

        if (stararg_cnt == 1) and (posarg_cnt > 1):
            NodeError.error_msg(call_ptree,
                    ('call to %s() mixes positional arguments and *args' %
                        funcname))
            return False

    # Check keyword args:
    #
    # if there's a **kwargs, then there must be exactly one **kwargs
    # and it must be the only keyword arg
    #
    for keyarg in call_ptree.keywords:
        if keyarg.arg == None: # None represents **
            kwarg_cnt += 1

    if (kwarg_cnt > 0):

        # Not even sure if this is valid Python...
        #
        if kwarg_cnt > 1:
            NodeError.error_msg(call_ptree,
                    ('call to %s() has multiple **kwargs' % funcname))
            return False

        if (kwarg_cnt == 1) and (keyword_cnt > 1):
            NodeError.error_msg(call_ptree,
                    ('call to %s() mixes keyword arguments and **kwargs' %
                        funcname))
            return False

    # if either kwarg_cnt or stararg_cnt are > 0, then
    # make sure that both the number of other positional
    # and keyword arguments is exactly zero
    #
    if (stararg_cnt != 0) and (kwarg_cnt != keyword_cnt):
        NodeError.error_msg(call_ptree,
                ('call to %s() mixes keyword arguments and *args' %
                    funcname))
        return False
    elif (kwarg_cnt != 0) and (stararg_cnt != posarg_cnt):
        NodeError.error_msg(call_ptree,
                ('call to %s() mixes positional arguments and **kwargs' %
                    funcname))
        return False

    if stararg_cnt > 0:
        NodeError.warning_msg(call_ptree,
                'call to %s() uses *args; cannot inline' % funcname)
        return False
    elif kwarg_cnt > 0:
        NodeError.warning_msg(call_ptree,
                'call to %s() uses **kwargs; cannot inline' % funcname)
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
    if not check_call_parameters(call_ptree):
        return None

    # TODO: check that the name of the called function
    # matches the function definition?

    rewriter = NameRewriter()

    tmp_names = TempVarManager.create_temp_var_manager()

    func_ptree = deepcopy(func_ptree)

    func_body = func_ptree.body
    formal_params = func_ptree.args.args

    actual_params = deepcopy(call_ptree.args)
    keyword_actual_params = deepcopy(call_ptree.keywords)

    setup_locals = list()
    new_func_body = list()

    # parameters that we've already processed (to make sure
    # that we don't do something as both an ordinary and keyword
    # parameter, and make sure that all the keyword parameters
    # get initialized
    #
    seen_param_names = dict()

    if len(actual_params) > len(formal_params):
        # Not exactly the same as the Python3 error message,
        # but close enough
        #
        NodeError.error_msg(call_ptree,
                ('%s() takes %d positional arguments but %d were given' %
                    (func_ptree.name, len(formal_params), len(actual_params))))
        return None

    # Make a list of all the formal parameter names,
    # to make sure that no bogus parameters are inserted
    # into the call.  (they won't have any effect, but
    # they're almost certainly a symptom that something
    # is wrong)
    #
    all_fp_names = [param.arg for param in formal_params]

    # examine the call, and build the code to assign
    # the actuals to the formals.
    #
    # First we do the non-keyword actual parameters, which
    # map directly to the formal parameters
    #
    for param_ind in range(len(actual_params)):
        orig_name = formal_params[param_ind].arg
        actual_param = actual_params[param_ind]
        seen_param_names[orig_name] = actual_param

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
    #
    for orig_name in seen_param_names.keys():

        # Here's where we might do something clever:
        #
        # if this is the name of a fp we don't need to assign:
        #    continue

        new_name = tmp_names.create_tmp_name(orig_name=orig_name)
        actual_param = seen_param_names[orig_name]
        rewriter.add_mapping(orig_name, new_name)

        # NodeError.diag_msg(call_ptree,
        #         'ASSIGN %s -> %s' % (new_name, ast.dump(actual_param)))

        setup_locals.append(ast.Assign(
                targets=list([ast.Name(id=new_name, ctx=ast.Store())]),
                value=actual_param))

    # deal with any specified keyword parameters
    #
    for keyword_param in keyword_actual_params:
        orig_name = keyword_param.arg

        # If a named parameter has a name that doesn't match
        # any of the formal parameters, consider it an error
        #
        if orig_name not in all_fp_names:
            NodeError.error_msg(call_ptree,
                    ('%s() got an unexpected keyword argument \'%s\'' %
                        (func_ptree.name, orig_name)))
            failed = True
            continue

        # TODO: we don't check whether the keyword parameter
        # matches a formal parameter

        # santity check: check to make sure we haven't done this
        # parameter already
        #
        if orig_name in seen_param_names:
            NodeError.error_msg(call_ptree,
                    ('%s() got multiple values for argument \'%s\'' %
                        (func_ptree.name, orig_name)))
            failed = True
            continue

        new_name = tmp_names.create_tmp_name(orig_name=orig_name)
        rewriter.add_mapping(orig_name, new_name)

        # NodeError.diag_msg(call_ptree,
        #         ('KASSIGN %s -> %s' %
        #             (new_name, ast.dump(keyword_param.value))))

        seen_param_names[orig_name] = keyword_param.value
        setup_locals.append(ast.Assign(
                    targets=list([ast.Name(id=new_name, ctx=ast.Store())]),
                    value=keyword_param.value))

    setup_checks = list()

    for param_ind in range(len(actual_params)):

        arg = formal_params[param_ind]
        anno = arg.annotation
        if not anno:
            continue

        if not isinstance(anno, ast.Name):
            NodeError.fatal_msg(
                    anno, 'type annotation is not a symbol')
            break

        fpname = arg.arg
        new_name = rewriter.name2name[fpname]

        actual_param = actual_params[param_ind]

        # TODO: add back the make_symtype_check when it's reliable
        #
        # check = make_symtype_check(new_name, anno.id, actual_param, fpname)
        # if check:
        #     setup_checks.append(check)

    # deal with any unspecified keyword parameters
    #
    # this is awkward, because there are a lot of things that
    # the programmer can do that aren't correct.
    #
    # What we do is we scan forward down the
    # list of formal parameters for which we have defaults,
    # looking for any whose names have not yet been seen, and
    # add those to the assignments.
    defaults = func_ptree.args.defaults
    if len(defaults) > 0:
        keyword_params = formal_params[-len(defaults):]

        for param_ind in range(len(keyword_params)):
            orig_name = keyword_params[param_ind].arg

            if orig_name in seen_param_names:
                continue

            new_name = tmp_names.create_tmp_name(orig_name=orig_name)
            rewriter.add_mapping(orig_name, new_name)

            # NodeError.diag_msg(call_ptree,
            #         ('DASSIGN %s -> %s' %
            #             (new_name, ast.dump(defaults[param_ind]))))

            seen_param_names[orig_name] = defaults[param_ind]
            setup_locals.append(ast.Assign(
                        targets=list([ast.Name(id=new_name, ctx=ast.Store())]),
                        value=defaults[param_ind]))

    # Finally we check to see whether there are any formal
    # parameters we haven't seen in either form, and chide
    # the user if there are.
    #
    for formal_param in formal_params:
        orig_name = formal_param.arg

        if orig_name not in seen_param_names:
            # Not precisely like the standard Python3 error msg
            # but reasonably close
            #
            NodeError.error_msg(call_ptree,
                    ('%s() missing required positional argument: \'%s\'' %
                        (func_ptree.name, orig_name)))
            failed = True

    if failed:
        return None

    # Now rescan the list of locals, looking for any we might
    # be able to reduce to constants.
    #
    constants = list()
    new_setup_locals = list()

    for name in seen_param_names:
        actual = seen_param_names[name]

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
            new_setup_locals.append(ast.Assign(
                    targets=list([ast.Name(id=new_name, ctx=ast.Store())]),
                    value=actual))

        # print('ARG %s = %s' %
        #         (name, pyqgl2.ast_util.ast2str(actual)))
        # print('ARG %s = %s' % (name, ast.dump(actual)))

    # NOTE: this interacts badly with doing eval-time error checking,
    # because letting the "constants" through untouched removes
    # an opportunity to check them (which can currently only be done
    # for things assigned to symbols
    #
    setup_locals = new_setup_locals

    # Now rewrite any local variable names to avoid conflicting
    # with other names in the in-lined scope
    #
    local_names = find_local_names(func_ptree)
    new_local_names = set()
    for name in local_names:
        # if it's not a parameter, then we haven't
        # already set up a new name for it, so do so here
        #
        if name not in seen_param_names:
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

            pyqgl2.ast_util.copy_all_loc(assignment, call_ptree)
            ast.fix_missing_locations(assignment)

    # Make a list of all of the formal parameters declared to be qbits,
    # and use this to define the barrier statements for this call
    #
    qbit_fparams = list()
    qbit_aparams = list()
    for formal_param in formal_params:
        if (formal_param.annotation and
                formal_param.annotation.id == QGL2.QBIT):
            qbit_fparams.append(formal_param.arg)
            qbit_aparams.append(rewriter.name2const[formal_param.arg].id)

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

        # stash a reference to the original call in the new_stmnt,
        # so that we can trace back the original variables used
        # in the call
        #
        # We want to preserve the call, and make sure it doesn't
        # get clobbered.  I'm not sure whether we need to make a
        # scratch copy of the original call_ptree, but it won't
        # hurt
        #
        new_stmnt.qgl2_orig_call = deepcopy(call_ptree)

    with_infunc = expr2ast(
            ('with infunc(\'%s\', %s): pass' %
                (func_ptree.name, qbit_aparams_txt)))

    # print('WITH INFUNC %s' % ast.dump(with_infunc))
    pyqgl2.ast_util.copy_all_loc(with_infunc, func_body[0], recurse=True)
    with_infunc.body = new_func_body

    inlined = setup_locals + setup_checks + [with_infunc]

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

    def visit_Attribute(self, node):
        name = collapse_name(node)
        self.dotted_names.add(name)

    def visit_Name(self, node):
        self.simple_names.add(node.id)

    def find_names(self, node):
        """
        Find the simple names (purely local names) and the
        "dotted" names (attributes of an instance, class,
        or module) referenced by a given AST node.

        Returns (simple, dotted) where "simple" is the set
        of simple names and "dotted" is the set of dotted names.

        Note that this skips NameConstants, because these
        names are fixed symbols in Python 3.4+ and cannot be
        renamed or modified (and therefore they're not really
        "local" names at all).
        """

        self.reset()
        self.visit(node)

        return self.simple_names, self.dotted_names

    def find_local_names(self, node):
        """
        A specialized form of find_names that only
        returns the local names
        """

        simple, _dotted = self.find_names(node)
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
        # TODO: expand what we can represent as literals
        # (i.e. add simple lists, tuples).
        #
        # TODO: add a comment, if possible, with the name of the variable

        value = self.values[name]

        if isinstance(value, int) or isinstance(value, float):
            redirection = ast.Num(n=value)
        elif isinstance(value, str):
            redirection = ast.Str(s=value)
        elif isinstance(value, QubitPlaceholder):
            redirection = ast.Name(id=value.use_name, ctx=ast.Load())
            redirection.qgl_is_qbit = True
        else:
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
                    funcdef, module_names=namespace.all_names)

        new_ptree = deepcopy(funcdef)

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
                    new_args.append(ap_arg)
                    continue

                if isinstance(ap_arg, ast.Name):
                    new_name = ap_arg.id
                    to_check = ap_arg
                    new_args.append(ap_arg)
                else:
                    new_name = tmp_var.create_tmp_name(orig_name=fp_arg.arg)
                    to_check = ast.Name(id=new_name)
                    new_args.append(to_check)

                    # NOTE: need to copy location info into to_check.
                    # FIXME (every new AST created needs to have a
                    # location assigned properly)

                    val_str = pyqgl2.ast_util.ast2str(ap_arg).strip()
                    expr = '%s = %s' % (new_name, val_str)
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

            new_call = deepcopy(call_ptree)
            new_call.args = new_args
            new_call.keywords = new_kwargs
            new_call = ast.Expr(value=new_call)

            # FAKE, FIXME
            return new_assignments + [new_call] # fake

        else:
            NodeError.diag_msg(
                    call_ptree, '%s() is not QGL2; not touching ' % func_name)
            return call_ptree


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

            inlined = inline_call(call_ptree, self.importer)
            if isinstance(inlined, ast.Call):
                stmnt.value = inlined
                new_body.append(stmnt)

                # Replace the previous two lines with these,
                # when the checked_call function does the right
                # thing.
                #
                # checked_call = self.make_checked_call(call_ptree)
                # if isinstance(checked_call, ast.Call):
                #     stmnt.value = inlined
                #     new_body.append(stmnt)
                # else:
                #     new_body += checked_call
                continue

            self.change_cnt += 1

            NodeError.diag_msg(call_ptree,
                    ('inlined call to %s()' %
                        collapse_name(call_ptree.func)))
            for expr in inlined:
                new_body.append(expr)

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
            new_call = deepcopy(base_call)

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
                    func_ptree, module_names=loc_syms):
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
