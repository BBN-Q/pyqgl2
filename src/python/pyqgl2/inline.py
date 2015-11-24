# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import ast
import meta

from copy import deepcopy

from pyqgl2.ast_util import NodeError
from pyqgl2.importer import NameSpaces

class InlineReturn(BaseException):
    pass

class TempVarManager(object):

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
    def create_temp_var_manager(name_prefix='__qgl2__tmp'):
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
            return '%s_%s' % (base, orig_name)
        else:
            return base

class NameRewriter(ast.NodeTransformer):

    def __init__(self):
        self.name2name = dict()

    def add_mapping(self, old_name, new_name):

        # A little sanity checking
        #
        assert isinstance(old_name, str), \
                ('old_name [%s] must be a string' % str(old_name))
        assert isinstance(new_name, str), \
                ('new_name [%s] must be a string' % str(new_name))

        self.name2name[old_name] = new_name

    def visit_Name(self, node):
        if node.id in self.name2name:
            node.id = self.name2name[node.id]

        return node

    def rewrite(self, ptree, mapping=None):
        """
        Write all the Name nodes in the given AST parse tree
        according to the current name2name mapping, and return
        the resulting tree.

        This method is destructive; it modifies the tree in-place
        """

        if mapping:
            for name in mapping.keys():
                self.add_mapping(name, mapping[name])

        new_ptree = self.visit(ptree)

        return new_ptree

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

    1. Create names for local variables to correspond
        to the formal parameters of the function

        These local variables are drawn from a namespace
        that will not conflict with other variables in the
        program.

    2. Create a list of statements that assigns the evaluation
        of the expressions in the actual parameters to the
        corresponding local variables that represent the formal
        parameters

        Steps 1 and 2 are complicated by needing to handle
        keyword arguments

    3. Create a copy of the body of the original function

    4. Rewrite all references to the formal parameters in the
        copy of the body to be references to the local variables
        that represent the formal parameters

    5. Append the list from #2 and the list from #4 and return it.
    """

    failed = False

    # sanity checking: this has to start with a FunctionDef
    # and a Call.  Otherwise, we can't do anything with it.
    #
    # Note: this returns the original ptree, not a copy.
    # TODO: think about whether it should be a copy.
    #
    if not isinstance(func_ptree, ast.FunctionDef):
        print('error: first arg needs to be a FunctionDef %s' %
                type(func_ptree))
        return None

    if not isinstance(call_ptree, ast.Call):
        print('error: second arg needs to be a Call %s' %
                ast.dump(call_ptree))
        return None

    rewriter = NameRewriter()

    tmp_names = TempVarManager.create_temp_var_manager()

    func_body = deepcopy(func_ptree.body)
    formal_params = deepcopy(func_ptree.args.args)
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
    print('ALL_FP_NAMES: %s' % str(all_fp_names))

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

        NodeError.diag_msg(call_ptree,
                'ASSIGN %s -> %s' % (new_name, ast.dump(actual_param)))

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

        NodeError.diag_msg(call_ptree,
                ('KASSIGN %s -> %s' %
                    (new_name, ast.dump(keyword_param.value))))

        seen_param_names[orig_name] = keyword_param.value
        setup_locals.append(ast.Assign(
                    targets=list([ast.Name(id=new_name, ctx=ast.Store())]),
                    value=keyword_param.value))

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

            NodeError.diag_msg(call_ptree,
                    ('DASSIGN %s -> %s' %
                        (new_name, ast.dump(defaults[param_ind]))))

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

    # We need to annotate the code for setting up each local
    # with a reasonable line number and file name (even though
    # it's all fictitious) so that any error messages generated
    # later make some sense
    #
    # We give the source file a name that signifies that it's
    # rewritten code.  (I'm ambivalent about this)
    #
    source_file = '_mod_' + call_ptree.qgl_fname
    for assignment in setup_locals:
        for subnode in ast.walk(assignment):
            subnode.qgl_fname = source_file

            ast.copy_location(assignment, call_ptree)
            ast.fix_missing_locations(assignment)

    for stmnt in func_body:
        new_stmnt = rewriter.rewrite(stmnt)
        ast.fix_missing_locations(new_stmnt)
        new_func_body.append(new_stmnt)

    inlined = setup_locals + new_func_body

    return inlined

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

    if not hasattr(node, 'qgl_func'):
        # unexpected: all FunctionDef nodes should be marked
        return False

    if not node.qgl_func:
        return False

    for stmnt in node.body:
        for subnode in ast.walk(stmnt):
            if isinstance(subnode, ast.Return):
                return False

    return True

def inliner(base_call):
    """
    Recursively expand a function by inlining all the
    procedure calls it can discover within the given
    call.

    In order to be inlined, a method must be declared
    to be a QGL function, and it must not be a class
    or instance method (it may be static).
    """

    # find the function being called; try to inline it.
    # then for each call in the body of the function
    # (whether or not the body was inlined), try to inline
    # that call.  Continue until every possible inline
    # has been exhausted (or the stack blows up) and then
    # stich all the results together.

    pass

def test_1():
    code = """
@qgl2decl
def foo(a, b, c):
    dummy(a + b + c)
foo(1, 2, 3)
"""

    importer = NameSpaces('<test>', text=code)
    ptree = importer.path2ast['<test>']
    func = ptree.body[0]

    print('IS_PROCEDURE: %s' % is_qgl_procedure(func))

    func_def = ptree.body[0]
    func_call = ptree.body[1].value

    ptree.body = create_inline_procedure(func_def, func_call)
    post = meta.asttools.dump_python_source(ptree)
    print('test_1 POST:\n%s' % post)

def test_2():
    code = """
@qgl2decl
def foo(a=1, b=2, c=3):
    dummy(a + b + c)
foo()
foo(x(12))
foo(d=12)
# foo(10, 20)
# foo(10, 20, 30)
# foo(c='c', b='b', a='a')
# foo(c='c', a='a')
"""

    importer = NameSpaces('<test>', text=code)
    ptree = importer.path2ast['<test>']

    func_def = ptree.body[0]

    scratch = deepcopy(ptree)

    print('CODE:\n%s' % code)
    for call in range(1, len(ptree.body)):
        scratch.body = create_inline_procedure(
                func_def, ptree.body[call].value)
        post = meta.asttools.dump_python_source(scratch)
        print('test_2 %d POST:\n%s' % (call, post))

def test_3():
    code = """
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

    importer = NameSpaces('<test>', text=code)
    ptree = importer.path2ast['<test>']

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

def test_4():
    code = """
@qgl2func
def foo(a, b):
    a = 1
    dummy(a + b)
foo(x, y)
"""

    importer = NameSpaces('<test>', text=code)
    ptree = importer.path2ast['<test>']

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

def test_rewriter():

    code = """
a = 1
b = 2
c = a + b
d = a + b + c
e = foo(a + b, c + d)
f = bar(d(a, b) + c(c, d))
"""

    rewrites = { 'a' : 'alpha',
            'b' : 'beta',
            'c' : 'gamma',
            'd' : 'delta'
    }

    ptree = ast.parse(code)

    rewriter = NameRewriter()
    pre = meta.asttools.dump_python_source(ptree)
    new_ptree = rewriter.rewrite(ptree, rewrites)
    post = meta.asttools.dump_python_source(new_ptree)

    print('PRE:\n%s' % pre)
    print('POST:\n%s' % post)

def test_module():
    code = """
@qgl2func
def foo(a, b):
    a = 1
    dummy(a + b)
x = 2
y = 200
foo(x, y)
"""

    importer = NameSpaces('<test>', text=code)
    ptree = importer.path2ast['<test>']

    func_def = ptree.body[0]

    inlined = create_inline_procedure(ptree.body[0], ptree.body[3].value)

    new_body = list([ptree.body[0]]) + inlined + ptree.body[1:]
    new_module = ast.Module(body=new_body)
    # print('NEW BODY\n%s' % ast.dump(new_module))
    print('AS CODE\n%s' % meta.asttools.dump_python_source(new_module))


def main():
    """
    test driver (for very simple tests)
    """

    test_rewriter()
    test_1()
    test_2()
    test_3()
    test_4()

    test_module()

main()
