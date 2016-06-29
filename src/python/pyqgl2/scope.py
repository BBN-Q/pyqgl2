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

from pyqgl2.ast_util import NodeError
from pyqgl2.inline import NameFinder


class CheckScoping(ast.NodeVisitor):
    """
    """

    def __init__(self, namespace=None):

        self.namespace = namespace

        self.formal_names = set()

        # mapping from name to nesting level (the nesting level
        # is 1-based: formal parameters are at nesting level 0).
        # Python builtins are -1, which means that we shouldn't
        # redefine them (although this is permitted).
        #
        self.local_names = dict()

        # This method of enumerating the builtins is probably
        # not portable
        #
        for name in builtins.__dict__:
            self.local_names[name] = -1

        # How deeply we're nested.  Formal parameters are defined
        # at nesting level 0, and assignments in the body of the
        # function are at level 1.
        #
        self.nesting_depth = 1

        self.name_finder = NameFinder()

    def visit_FunctionDef(self, node):
        """
        The usual entry point: insert the names used by the
        formal parameters, and then process the body
        """

        for arg in node.args.args:
            name = arg.arg
            if name not in self.local_names:
                self.local_names[arg.arg] = 0
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
        assigned_names, _dotted_names = self.name_finder.find_names(lval)

        for name in assigned_names:
            if name not in self.local_names:
                self.local_names[name] = self.nesting_depth
            elif self.local_names[name] > self.nesting_depth:
                # we permit the nest depth to decrease, but
                # not increase
                #
                self.local_names[name] = self.nesting_depth
            elif self.local_names[name] < 0:
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
    t0 = """
def t0(a, b, c):
    if a:
        x, y = bar(b, c)
    else:
        y, z = qux()
"""

    t1 = """
def t1(a, b, c):
    if x:
        x, y = bar(b, c)
    else:
        y, z = qux()
"""

    t2 = """
def t2(a, b, c):
    if a:
        x, y = bar(x, y)
    else:
        y, z = qux()
"""

    t3 = """
def t3(a, b, c):
    if a:
        x, y = bar(x, y)
    else:
        y, z = qux()

    print(z)
"""

    t4 = """
def t4(a):
    for b in range(a):
        c = b
"""

    t5 = """
def t5(a):
    for b in range(a):
        d = b
"""

    t6 = """
def t5(a, z=1, y=2):
    d = 0
    for b in range(a):
        d += b
"""

    t7 = """
def t6(a, z=1, y=2):
    d = 0
    for bool in range(a):
        sum += b
"""

    tests = [t0, t1, t2, t3, t4, t5, t6, t7]

    for test in tests:
        # Forget the current error state, if any, prior to
        # each test.
        #
        NodeError.reset()

        print('---- ---- ---- ----')
        t = ast.parse(test, mode='exec')
        CheckScoping().visit(t)
