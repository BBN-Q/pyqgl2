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

3) If a name appears anywhere else (not the lval) in a
    statement, and is not in the global scope nor a formal
    parameter nor has appeared in an earlier assignment
    (in order of appearance) then consider it an potential
    error.

4) If a name first appears at a nesting level X and then
    is referenced at any nesting level smaller than X,
    consider it a potential error.

"""


import ast

from copy import deepcopy

import pyqgl2.ast_util

from pyqgl2.inline import NameFinder

from pyqgl2.ast_qgl2 import is_with_label
from pyqgl2.ast_qgl2 import is_concur, is_infunc
from pyqgl2.ast_util import ast2str, expr2ast
from pyqgl2.ast_util import copy_all_loc
from pyqgl2.ast_util import NodeError
from pyqgl2.inline import BarrierIdentifier
from pyqgl2.inline import QubitPlaceholder

class CheckScoping(ast.NodeVisitor):
    """
    """

    def __init__(self, namespace=None):

        self.namespace = namespace

        self.formal_names = set()

        # mapping from name to nesting level (the nesting level
        # is 1-based: formal parameters are at nesting level 0).
        #
        self.local_names = dict()

        # How deeply we're nested.  Formal parameters are defined
        # at nesting level 0, and assignments in the body of the
        # function are at level 1.
        #
        self.nesting_depth = 1

        self.name_finder = NameFinder()

    def visit_If(self, node):
        self.visit(node.test)
        self.do_body(node.body)
        self.do_body(node.orelse)

    def visit_For(self, node):
        self.visit(node.iter)
        self.do_lval(node.target)
        self.do_body(node.body)
        self.do_body(node.orelse)

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
        assert False, 'Dan, implement me'

    def visit_Name(self, node):
        if node.id not in self.local_names:
            NodeError.warning_msg(node,
                    'potentially undefined symbol [%s]' % node.id)

    def do_lval(self, lval):
        local_names, _dotted_names = self.name_finder.find_names(lval)

        # we permit the nest depth to decrease, but not increase
        for name in local_names:
            if not name in self.local_names:
                self.local_names[name] = self.nesting_depth
            elif self.local_names[name] > self.nesting_depth:
                self.local_names[name] = self.nesting_depth

    def do_body(self, body):

        self.nesting_depth += 1

        for stmnt in body:
            self.visit(stmnt)

        self.nesting_depth -= 1

def find_all_names(node):
    names = set()

    print('FAN %s' % ast.dump(node))

    if isinstance(node, list):
        for elem in node:
            print('E: %s' % ast.dump(elem))
            names = names.union(find_all_names(elem))
    else:
        for subnode in ast.walk(node):
            if isinstance(subnode, ast.Name):
                names.add(subnode.id)

    print('NAMES: %s' % str(names))

    return names


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

    tests = [t0, t1, t2, t3, t4, t5]

    for test in tests:
        # Forget the current error state, if any, prior to
        # each test.
        #
        NodeError.reset()

        print('---- ---- ---- ----')
        t = ast.parse(test, mode='exec')
        CheckScoping().visit(t)
