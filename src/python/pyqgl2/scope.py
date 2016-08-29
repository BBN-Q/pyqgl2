# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
Check that the variable names referenced in a function are
defined within the scope of that function.

This is a useful heuristic in some cases, but is contrary
to the Python programming model, which permits this to be
more dynamic, using things like decorators and **kwargs
to sneak names into the local scope in a way that can be
impossible to analyze without considering the context in
which the function is called.

It is also possible to explicitly undefine a variable name,
and we don't take that into account either: once a variable
has been given a name, we assume that it remains until it
falls out of scope.

A more difficult (and more typical) problem is that whether
a name is or is not bound to a variable may depend on details
of the execution.  We don't have a good answer for this
yet.  For example:

        # y is not bound yet
        if x:
            y = 'something'

        print(y)

If x is non-False, then y will be bound, but if not, then
y will be unbound and the "print(y)" will fail with an
exception.  (there are also other, less obvious situations
where variables may or may not be bound after a statement
is executed, such as loops with empty iterators, or
assignments within orelse or except blocks)

We're going to start with simple heuristics:

1) If a name appears as in the formal parameters of the
    function definition, it is assumed to be in-scope

2) If a name appears as an lval (or part of an lval tuple)
    prior to its reference, it is assumed to be in-scope

    "prior to its reference" means "prior in the preorder walk
    through the AST" and there's no guarantee that the
    code that defines the symbol is executed prior to the
    code referencing the symbol.

3) If a name appears anywhere else (not the lval) in a
    statement, and is not in the global scope nor a formal
    parameter nor has appeared in an earlier assignment
    (in order of appearance) then consider it an potential
    error.

4) If a name first appears at a nesting level X and then
    is referenced at any nesting level smaller than X,
    consider it a potential error.

5) Redefinitions of builtins (either by use as a formal
    parameter, or explicitly assigned) is considered a
    potential error.
"""

import ast
import builtins

import pyqgl2.inline

from pyqgl2.ast_util import NodeError


def scope_check(function_def, module_names=None):
    """
    Convenience function to create a CheckScoping instance and
    use it to check the scoping of variables within an ast.FunctionDef.

    The caller should use NodeError.error_detected() and/or
    NodeError.halt_on_error() to check if any errors were detected.
    Ordinarily this function has no effect except to generate
    warning or error messages if it detects problems.

    Returns True to indicate success.  Right now, there's no way
    for this function to fail (short of crashing), but eventually
    we might decide that some of the warnings are really errors.
    """

    # Something is seriously wrong if we get anything other than
    # an ast.FunctionDef
    #
    assert isinstance(function_def, ast.FunctionDef)

    checker = CheckScoping(module_names=module_names)
    checker.visit(function_def)

    return True


class CheckScoping(ast.NodeVisitor):
    """
    """

    BUILTIN_SCOPE = -2
    MODULE_SCOPE = -1
    PARAM_SCOPE = 0
    LOCAL_SCOPE = 1

    def __init__(self, module_names=None):

        # mapping from name to nesting level (the nesting level
        # is 1-based: formal parameters are at nesting level 0).
        # Python builtins are -2, which means that we shouldn't
        # redefine them (although this is permitted).
        #
        self.local_names = dict()

        # This method of enumerating the builtins is probably
        # not portable
        #
        for name in builtins.__dict__:
            self.local_names[name] = CheckScoping.BUILTIN_SCOPE

        if module_names:
            for name in module_names:
                self.local_names[name] = CheckScoping.MODULE_SCOPE

        # How deeply we're nested.  Formal parameters are defined
        # at nesting level PARAM_SCOPE, and assignments in the body
        # of the function are at level LOCAL_SCOPE or greater.
        #
        self.nesting_depth = CheckScoping.LOCAL_SCOPE

        self.name_finder = pyqgl2.inline.NameFinder()

    def visit_FunctionDef(self, node):
        """
        The usual entry point: insert the names used by the
        formal parameters, and then process the body
        """

        for arg in node.args.args:
            name = arg.arg
            if name not in self.local_names:
                self.local_names[name] = CheckScoping.PARAM_SCOPE
            elif self.local_names[name] == CheckScoping.MODULE_SCOPE:
                NodeError.warning_msg(
                        node,
                        'formal parameter masks a module symbol [%s]' % name)
            else:
                NodeError.warning_msg(
                        node,
                        'formal parameter masks a builtin symbol [%s]' % name)

        self.do_body(node.body)

    def visit_If(self, node):
        self.visit(node.test)
        self.do_body(node.body)
        self.do_body(node.orelse)

    def visit_For(self, node):
        self.visit(node.iter)
        self.do_lval(node.target)
        self.do_body(node.body)
        self.do_body(node.orelse)

    def visit_Attribute(self, node):
        """
        We don't examine attributes (yet).  We assume that
        they're OK without actually checking the namespace.

        TODO: check the collapsed name of the attribute
        against the current namespace.
        """

        pass

    def visit_Assign(self, node):

        # Examine the value first, because we evaluate right-to-left
        #
        self.visit(node.value)
        self.do_lval(node.targets[0])

    def visit_AugAssign(self, node):

        # We need the lval to exist prior to the assignment,
        # so examine both the left and right prior to adding the
        # lval bindings
        #
        self.generic_visit(node)
        self.do_lval(node.target)

    def visit_Name(self, node):
        """
        Process an ast.Name node for a symbol reference
        (not a symbol assignment, which should be done
        in do_lval).

        If we find a name that doesn't have a binding in
        the current scope, or that was defined at a higher
        nesting level than we're currently in, then warn
        the user that this might be an error.  (these aren't
        always errors, but they're strange enough that they're
        worth calling out)
        """

        name = node.id

        if name not in self.local_names:
            NodeError.warning_msg(
                    node, 'potentially undefined symbol [%s]' % name)
        elif self.local_names[name] > self.nesting_depth:
            NodeError.warning_msg(
                    node,
                    'symbol [%s] referenced outside defining block' % name)

    def do_lval(self, lval):
        assigned_names, _dotted, _arrays = self.name_finder.find_names(lval)

        for name in assigned_names:
            if name not in self.local_names:
                self.local_names[name] = self.nesting_depth
            elif self.local_names[name] > self.nesting_depth:
                # we permit the nest depth to decrease, but
                # not increase
                #
                self.local_names[name] = self.nesting_depth
            elif self.local_names[name] == CheckScoping.BUILTIN_SCOPE:
                # If the symbol is a builtin, then warn that
                # it's being reassigned
                #
                NodeError.warning_msg(
                        lval, 'reassignment of a builtin symbol [%s]' % name)

    def do_body(self, body):
        """
        Process a statement body: increment the nesting depth,
        process each statement in the body, and then decrement
        the nesting depth again
        """

        self.nesting_depth += 1
        for stmnt in body:
            self.visit(stmnt)
        self.nesting_depth -= 1


if __name__ == '__main__':
    import sys

    t0 = """
def t0(a, b, c):
    if a:
        x, y = alpha(b, c)
    else:
        y, z = beta()
"""

    m0 = """
<unknown>:4:15: warning: potentially undefined symbol [alpha]
<unknown>:6:15: warning: potentially undefined symbol [beta]
"""

    t1 = """
def t1(a, b, c):
    if x:
        x, y = alpha(b, c)
    else:
        y, z = beta()
"""

    m1 = """
<unknown>:3:7: warning: potentially undefined symbol [x]
<unknown>:4:15: warning: potentially undefined symbol [alpha]
<unknown>:6:15: warning: potentially undefined symbol [beta]
"""

    t2 = """
def t2(a, b, c):
    if a:
        x, y = alpha(x, y)
    else:
        y, z = beta()
"""

    m2 = """
<unknown>:4:15: warning: potentially undefined symbol [alpha]
<unknown>:4:21: warning: potentially undefined symbol [x]
<unknown>:4:24: warning: potentially undefined symbol [y]
<unknown>:6:15: warning: potentially undefined symbol [beta]
"""

    t3 = """
def t3(a, b, c):
    if a:
        x, y = alpha(x, y)
    else:
        y, z = beta()

    print(z)
"""

    m3 = """
<unknown>:4:15: warning: potentially undefined symbol [alpha]
<unknown>:4:21: warning: potentially undefined symbol [x]
<unknown>:4:24: warning: potentially undefined symbol [y]
<unknown>:6:15: warning: potentially undefined symbol [beta]
<unknown>:8:10: warning: symbol [z] referenced outside defining block
"""

    t4 = """
def t4(a):
    for b in range(a):
        c = b
"""

    m4 = """
"""

    t5 = """
def t5(a):
    for b in range(a):
        d = b
"""

    m5 = """
"""

    t6 = """
def t6(a, z=1, y=2):
    d = 0
    for b in range(a):
        d += b
"""

    m6 = """
"""

    t7 = """
def t7(a, z=1, y=2):
    d = 0
    for bool in range(a):
        sum += b
"""

    m7 = """
<unknown>:4:8: warning: reassignment of a builtin symbol [bool]
<unknown>:5:15: warning: potentially undefined symbol [b]
<unknown>:5:8: warning: reassignment of a builtin symbol [sum]
"""

    t8 = """
def t8(a, b):
    for a in range(b):
        y = foo(x)
"""

    m8 = """
<unknown>:4:12: warning: potentially undefined symbol [foo]
<unknown>:4:16: warning: potentially undefined symbol [x]
"""

    t9 = """
def t8(a, b):
    for a in range(b):
        y = baz(x)
"""

    m9 = """
<unknown>:4:12: warning: potentially undefined symbol [baz]
<unknown>:4:16: warning: potentially undefined symbol [x]
"""

    module_names = [ 'bar', 'qux' ]

    tests = [t0, t1, t2, t3, t4, t5, t6, t7, t8, t9]
    msgs = [m0, m1, m2, m3, m4, m5, m6, m7, m8, m9]

    err_cnt = 0
    for ind in range(len(tests)):
        test = tests[ind]
        expected_msg = msgs[ind].strip()

        # Forget the current NodeError state, if any, prior to
        # each test.
        #
        NodeError.reset()
        NodeError.LAST_N = 20

        t = ast.parse(test, mode='exec').body[0]
        print('---- ---- ---- ----')
        scope_check(t, module_names=module_names)

        actual_msg = ('\n'.join(NodeError.LAST_MSGS)).strip()
        if expected_msg != actual_msg:
            print('ERROR in test %d' % ind)
            print('Expected:\n%s' % expected_msg)
            print('Got:\n%s' % actual_msg)
            err_cnt += 1

    if err_cnt:
        print('%s FAILED' % sys.argv[0])
        sys.exit(1)
    else:
        print('%s SUCCESS' % sys.argv[0])
        sys.exit(0)
