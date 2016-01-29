# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
Unroll for loops (and possibly other conditional/iterative statements) 
within a "with concur" block.
"""

import ast
import os
import sys

from copy import deepcopy

import pyqgl2.ast_util

from pyqgl2.ast_util import NodeError
from pyqgl2.lang import QGL2


class ConcurUnroller(ast.NodeTransformer):
    """
    TODO: document the subset of all possible cases that this
    code actually recognizes/handles
    """

    def __init__(self):

        self.bindings_stack = list()

    def visit_With(self, node):

        if not self.is_concur(node):
            print('NOT CONCUR') # debug
            return self.visit(node) # check

        print('CONCUR') # debug

        # for now, we're going to address only the simplest case:
        # for loops at the top level of the block.

        new_outer_body = list()

        for outer_stmnt in node.body:
            if isinstance(outer_stmnt, ast.For): 
                unrolled = self.for_unroller(outer_stmnt)
                new_outer_body += unrolled
            else:
                new_outer_body.append(outer_stmnt)

        node.body = new_outer_body

        return node

    def visit_Name(self, node):
        """
        If the name has a binding in any local scope (which may
        be nested), then substitute that binding
        """

        name_id = node.id

        for ind in range(len(self.bindings_stack) -1, -1, -1):
            if name_id in self.bindings_stack[ind]:
                return self.bindings_stack[ind][name_id]

        return node

    def is_concur(self, node):
        """
        Return True if the node is a with-concur block,
        otherwise False
        """

        if not node:
            return False

        if not isinstance(node, ast.With):
            return False

        for item in node.items:
            if (isinstance(item.context_expr, ast.Name) and
                    (item.context_expr.id == QGL2.QCONCUR)):
                return True

        return False

    def for_unroller(self, for_node):

        # The iter has to be an ordinary ast.List.  It is not enough
        # for it to be an expression that evaluates to a list or
        # collection--it has to be a real, naked list, so we know
        # exactly how long it is.
        #
        # Right now we need it to consist of literals (possibly grouped
        # in tuples or similar simple structures).  Hopefully we'll relax
        # this.

        if for_node.orelse:
            print('WARNING: cannot expand for with orelse') # FIXME
            return list([for_node])

        if not isinstance(for_node.iter, ast.List):
            return list([for_node])

        # TODO more checking for consistency/fit

        new_stmnts = list()

        vals = for_node.iter.elts
        for index in range(len(vals)):

            bindings = self.make_bindings(for_node.target, vals[index])

            # Things to think about: should all the statements that
            # come from the expansion of one pass through the loop
            # be grouped in some way (such as a 'with seq' block)?
            # Or should they just be dumped onto the end, as we do now?

            print('BINDINGS %s' % str(bindings))

            self.bindings_stack.append(bindings)

            new_body = deepcopy(for_node.body)

            new_stmnts += self.replace_bindings(bindings, new_body)

            self.bindings_stack.pop()

        return new_stmnts

    def make_bindings(self, targets, values):
        """
        make a dictionary of bindings for the "loop variables"

        If the target is a single name, then just assign the values
        to it as a tuple.  If the target is a tuple, then try to match
        up the values to the names in the tuple.

        There are a lot of things that could go wrong here, but we
        don't detect/handle many of them yet TODO: fix this
        """

        bindings = dict()

        if isinstance(targets, ast.Name):
            bindings[targets.id] = values
        elif isinstance(targets, ast.Tuple):
            for index in range(len(targets.elts)):
                # TODO: check!
                bindings[targets.elts[index].id] = values[index]
        else:
            # TODO: oopsy!
            pass

        return bindings

    def replace_bindings(self, bindings, stmnts):
        
        new_stmnts = list()

        for stmnt in stmnts:
            new_stmnt = self.visit(stmnt)
            new_stmnts.append(new_stmnt)

        return new_stmnts

if __name__ == '__main__':

    def preprocess(fname):
        text = open(fname, 'r').read()
        ptree = ast.parse(text, mode='exec')

        print('INITIAL PTREE:\n%s' % pyqgl2.ast_util.ast2str(ptree))

        unroller = ConcurUnroller()
        new_ptree = unroller.visit(ptree)

        print('NEW PTREE:\n%s' % pyqgl2.ast_util.ast2str(new_ptree))

        # Now do the transformation

    preprocess(sys.argv[1])
