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

def is_concur(node):
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


class Unroller(ast.NodeTransformer):
    """
    A more general form of the ConcurUnroller, which knows how to
    "unroll" FOR loops and IF statements in more general contexts.

    TODO: document the subset of all possible cases that this
    code actually recognizes/handles
    """

    def __init__(self):

        self.bindings_stack = list()
        self.change_cnt = 0

    def unroll_body(self, body):
        """
        Look through the body of a block statement, and expand
        whatever statements can be expanded/unrolled within the block

        TODO: combine with the logic for inlining functions
        """

        while True:
            old_change_cnt = self.change_cnt

            new_outer_body = list()

            for outer_stmnt in body:
                if isinstance(outer_stmnt, ast.For):
                    unrolled = self.for_unroller(outer_stmnt)
                    new_outer_body += unrolled
                elif isinstance(outer_stmnt, ast.If):
                    unrolled = self.if_unroller(outer_stmnt)
                    new_outer_body += unrolled

                # TODO: add cases for handling other things we
                # can unroll, like ifs or possibly list comprehensions:
                # basically any control flow where we can anticipate
                # exactly what's going to happen

                else:
                    new_outer_body.append(self.visit(outer_stmnt))

            body = new_outer_body

            # If we made changes in the last iteration,
            # then the resulting code might have more changes
            # we can make.  Keep trying until we manage to
            # iterate without making any changes.
            #
            if self.change_cnt == old_change_cnt:
                break

        return body

    def visit_While(self, node):
        node.body = self.unroll_body(node.body)
        return node

    def visit_With(self, node):
        node.body = self.unroll_body(node.body)
        return node

    def visit_FunctionDef(self, node):
        node.body = self.unroll_body(node.body)
        return node

    def visit_Name(self, node):
        """
        If the name has a binding in any local scope (which may
        be nested), then substitute that binding
        """

        name_id = node.id

        for ind in range(len(self.bindings_stack) -1, -1, -1):
            if name_id in self.bindings_stack[ind]:
                self.change_cnt += 1
                return self.bindings_stack[ind][name_id]

        return node

    def if_unroller(self, if_node):

        # Figure out whether we have a constant predicate (of the
        # types of constants we understant) and then what the value
        # of the predicate is:
        #
        # If the test is a Num, check whether it is non-zero.
        # If the test is a NameConstant, then check whether its
        # value is True, False, or None.
        # If the test is a String, then check whether it's the
        # empty string.
        #
        if isinstance(if_node.test, ast.Num):
            const_predicate = True
            predicate = if_node.test.n
        elif isinstance(if_node.test, ast.NameConstant):
            const_predicate = True
            predicate = if_node.test.value
        elif isinstance(if_node.test, ast.Str):
            const_predicate = True
            predicate = if_node.test.s
        else:
            const_predicate = False

        if const_predicate:
            if predicate:
                return self.unroll_body(if_node.body)
            else:
                return self.unroll_body(if_node.orelse)
        else:
            if_node.body = self.unroll_body(if_node.body)
            if_node.orelse = self.unroll_body(if_node.orelse)

            return list([if_node])

    def expand_range(self, for_node):
        """
        If the iter for the ast.For node is a call to range(),
        then attempt to expand it into a list of integers,
        and return the resulting new ast.For node.

        If the expansion fails, return the original node (and
        in some cases print diagnostics).
        """

        assert isinstance(for_node, ast.For)

        if not isinstance(for_node.iter, ast.Call):
            return for_node
        elif not isinstance(for_node.iter.func, ast.Name):
            return for_node
        elif for_node.iter.func.id != 'range':
            return for_node

        args = for_node.iter.args

        start = 0
        stop = 0
        step = 1

        ast_start = None
        ast_step = None

        arg_cnt = len(args)

        if arg_cnt == 0:
            NodeError.error_msg(for_node.iter,
                    'not enough parameters to range()')
            return for_node
        if arg_cnt == 1:
            ast_stop = args[0]
        elif arg_cnt == 2:
            ast_start = args[0]
            ast_stop = args[1]
        elif arg_cnt == 3:
            ast_start = args[0]
            ast_stop = args[1]
            ast_step = args[2]
        else:
            NodeError.error_msg(for_node.iter,
                    'too many parameters to range()')
            return for_node

        # Once we do constant propogation correctly,
        # this should be less of an issue, but right now
        # we can only handle calls to range with numeric
        # parameters
        #
        if ast_start:
            if isinstance(ast_start, ast.Num):
                start = ast_start.n
            else:
                NodeError.warning_msg(ast_start,
                        'cannot use as range start; not a constant')
                return for_node

        if ast_stop:
            if isinstance(ast_stop, ast.Num):
                stop = ast_stop.n
            else:
                NodeError.warning_msg(ast_stop,
                        'cannot use as range stop; not a constant')
                return for_node

        if ast_step:
            if isinstance(ast_step, ast.Num):
                step = ast_step.n
            else:
                NodeError.warning_msg(ast_step,
                        'cannot use as range step; not a constant')
                return for_node

        # Finally, we can do the expansion.

        new_for_node = deepcopy(for_node)

        new_for_node.iter = ast.List()
        pyqgl2.ast_util.copy_all_loc(new_for_node.iter, for_node.iter)

        new_elts = list()
        for val in range(start, stop, step):
            new_elt = ast.Num(n=val)
            pyqgl2.ast_util.copy_all_loc(new_elt, for_node.iter)
            new_elts.append(new_elt)

        new_for_node.iter.elts = new_elts

        return new_for_node

    def for_unroller(self, for_node, unroll_inner=True):
        """
        Unroll a for loop, if possible, returning the resulting
        list of statements that replace the original "for" expression

        TODO: does it make sense to try to unroll elements of the
        loop, if the loop itself can't be unrolled?  If we reach a
        top-level loop that we can't unroll, that usually means
        that the compilation is going to fail to linearize things
        (although it can be OK if a "leaf" loop can't be unrolled).
        I'm going to leave this as a parameter (unroll_inner) with
        a default value of True, which we can change if it's a bad
        idea.
        """

        # The iter has to be an ordinary ast.List, or a range expression.
        # expression.  Except for range expressions, it is not enough
        # for it to be an expression that evaluates to a list or
        # collection--it has to be a real, naked list, so we know
        # exactly how long it is.
        #
        # Right now we need it to consist of literals (possibly grouped
        # in tuples or similar simple structures).  Hopefully we'll relax
        # this to include things like range() expressions where the
        # parameters are known.

        if for_node.orelse:
            NodeError.warning_msg(for_node.orelse,
                    'cannot expand for with orelse')
            return list([for_node])

        # if the iter element of the for loop is a range expression,
        # and we can evaluate it to a constant list, do so now.
        # When we do so, we may alter the for loop itself, so
        # expand_range will make a copy of the for loop node and
        # return that, rather than just the iterator.
        #
        for_node = self.expand_range(for_node)

        if not isinstance(for_node.iter, ast.List):
            if unroll_inner:
                # even if we can't unroll this loop, we might
                # be able to unroll statements in the body of
                # the loop, so give that try
                #
                new_body = self.unroll_body(for_node.body)
                for_node.body = new_body
            return list([for_node])

        # check that the list contains simple expressions:
        # numbers, symbols, or other constants.  If there's
        # anything else in the list, then bail out because
        # we can't do a simple substitution.
        #
        # TODO: There are cases where we can't use names; if
        # the body of the loop modifies the value bound to a
        # symbol mentioned in iter.elts, then this may break.
        # This case is hard to analyze but we could warn the
        # programmer that something risky is happening.
        #
        # TODO: For certain idempotent exprs, we can do more
        # inlining than for arbitrary expressions.  We don't
        # have a mechanism for determining whether an expression
        # is idempotent yet.
        #
        simple_expr_types = set(
                [ast.Num, ast.Str, ast.Name, ast.NameConstant])
        all_simple = True
        for elem in for_node.iter.elts:
            if type(elem) not in simple_expr_types:
                all_simple = False
                break

        if not all_simple:
            NodeError.diag_msg(for_node, 'not all loop elements are consts')

            if unroll_inner:
                # even if we can't unroll this loop, we might
                # be able to unroll statements in the body of
                # the loop, so give that try
                #
                new_body = self.unroll_body(for_node.body)
                for_node.body = new_body
            return list([for_node])

        # TODO more checking for consistency/fit

        new_stmnts = list()

        vals = for_node.iter.elts
        for index in range(len(vals)):

            try:
                bindings = self.make_bindings(for_node.target, vals[index])
            except TypeError as exc:
                NodeError.error_msg(vals[index], str(exc))
                return new_stmnts # return partial results; bail out later

            # Things to think about: should all the statements that
            # come from the expansion of one pass through the loop
            # be grouped in some way (such as a 'with seq' block)?
            # Or should they just be dumped onto the end, as we do now?

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
        don't detect/handle many of them yet

        There's some deliberate sloppiness permitted: the loop target
        can be a list (which is weird style) and the parameters can
        be a combination of lists and tuples.  As long as the target
        and each element of the values can be indexed, things will
        work out.  We could be stricter, because if these types are
        mixed it's almost certainly an error of some kind.
        """

        bindings = dict()

        if isinstance(targets, ast.Name):
            bindings[targets.id] = values
        elif isinstance(targets, ast.Tuple) or isinstance(targets, ast.List):

            # If the target is a list or tuple, then the values must
            # be as well
            #
            if (not isinstance(values, ast.List) and
                    not isinstance(values, ast.Tuple)):
                NodeError.error_msg(values,
                        'if loop vars are a tuple, params must be list/tuple')
                return bindings

            # The target and the values must be the same length
            #
            if len(targets.elts) != len(values.elts):
                NodeError.error_msg(values,
                        'mismatch between length of loop variables and params')
                return bindings

            for index in range(len(targets.elts)):
                name = targets.elts[index].id
                value = values.elts[index]

                bindings[name] = value
        else:
            NodeError.error_msg(targets,
                    'loop target variable must be a name or tuple')

        return bindings

    def replace_bindings(self, bindings, stmnts):

        new_stmnts = list()

        for stmnt in stmnts:
            new_stmnt = self.visit(stmnt)
            new_stmnts.append(new_stmnt)

        return new_stmnts


class QbitGrouper(ast.NodeTransformer):
    """
    TODO: this is just a prototype and needs some refactoring
    """

    def __init__(self):
        pass

    def visit_With(self, node):

        if not is_concur(node):
            return self.generic_visit(node) # check

        # Hackish way to create a seq node to use
        seq_item_node = deepcopy(node.items[0])
        seq_item_node.context_expr.id = 'seq'
        seq_node = ast.With(items=list([seq_item_node]), body=list())

        groups = self.group_stmnts(node.body)
        new_body = list()

        for qbits, stmnts in groups:
            new_seq = deepcopy(seq_node)
            new_seq.body = stmnts
            new_body.append(new_seq)

        node.body = new_body

        # print('Final:\n%s' % pyqgl2.ast_util.ast2str(node))

        return node

    @staticmethod
    def find_qbits(stmnt):

        qbits = set()

        for node in ast.walk(stmnt):
            if isinstance(node, ast.Name):

                # This is an ad-hoc way to find QBITS, which
                # requires that the substituter has already run
                #
                # TODO: mark names as qbits (and with channel info)
                # without rewriting the names, or keep the original
                # names after rewriting: keep both the original name
                # intact and the qbit assignment so that both can
                # be observed.  This requires changes in the substituter,
                # as well as here.
                #
                if node.id.startswith('QBIT_'):
                    qbits.add(node.id)

        # print('FOUND QBITS [%s] %s' %
        #         (pyqgl2.ast_util.ast2str(stmnt).strip(), str(qbits)))

        return list(qbits)

    @staticmethod
    def group_stmnts(stmnts, find_qbits_func=None):
        """
        Return a list of statement groups, where each group is a tuple
        (qbit_list, stmnt_list) where qbit_list is a list of all of
        the qbits referenced in the statements in stmnt_list.

        The stmnts list is partitioned such that each qbit is referenced
        by statements in exactly one partition (with a special partition
        for statements that don't reference any qbits).

        TODO: Independence is defined ad-hoc here, and will need
        to be something more sophisticated that understands the
        interdependencies between qbits/channels.

        For example, assuming that "x", "y", and "z" refer to
        qbits on non-conflicting channels, the statements:

                X90(x)
                Y90(y)
                Id(z)
                Y90(x)
                X180(z)

        can be grouped into:

                [ [ X90(x), Y90(x) ], [ Y90(y) ], [ Id(z), X180(z) ] ]

        which would result in a returned value of:

        [ ([x], [X90(x), Y90(x)]), ([y], [Y90(y)]), ([z], [Id(z), X180(z)]) ]

        If there are operations over multiple qbits, then the
        partitioning may fail.
        """

        if find_qbits_func is None:
            find_qbits_func = QbitGrouper.find_qbits

        qbit2list = dict()

        for stmnt in stmnts:
            qbits_referenced = find_qbits_func(stmnt)

            if len(qbits_referenced) == 0:
                # print('unexpected: no qbit referenced')

                # Not sure whether this should be an error;
                # for now we'll add this to a special 'no qbit'
                # bucket.

                if 'no_qbit' not in qbit2list:
                    qbit2list['no_qbit'] = list([stmnt])
                else:
                    qbit2list['no_qbit'].append(stmnt)

            elif len(qbits_referenced) == 1:
                qbit = qbits_referenced[0]
                if qbit not in qbit2list:
                    qbit2list[qbit] = list([stmnt])
                else:
                    qbit2list[qbit].append(stmnt)
            else:
                # There are multiple qbits referenced by the stmnt,
                # then we need to find any other stmnt lists that
                # we've built up for each of the qbits, and combine
                # them into one sequence of statments, and then
                # map each qbit to the resulting sequence.
                #
                # This would be more elegant if we could have a set
                # of lists, but in Python lists aren't hashable,
                # so we need to fake a set implementation with a list.
                #
                stmnt_set = list()
                stmnt_list = list()

                for qbit in qbits_referenced:
                    if qbit in qbit2list:
                        curr_list = qbit2list[qbit]

                        if curr_list not in stmnt_set:
                            stmnt_set.append(curr_list)

                for seq in stmnt_set:
                    stmnt_list += seq

                stmnt_list.append(stmnt)

                for qbit in qbits_referenced:
                    qbit2list[qbit] = stmnt_list

        # neaten up qbit2list to eliminate duplicates;
        # present the result in a more useful manner

        tmp_groups = dict()

        for qbit in qbit2list.keys():
            # this is gross, but we can't use a mutable object as a key
            # in a table, so we use a string representation

            stmnts_str = str(qbit2list[qbit])
            if stmnts_str in tmp_groups:
                (qbits, stmnts) = tmp_groups[stmnts_str]
                qbits.append(qbit)
            else:
                tmp_groups[stmnts_str] = (list([qbit]), qbit2list[qbit])

        groups = [ (sorted(tmp_groups[key][0]), tmp_groups[key][1])
                for key in tmp_groups.keys() ]

        return sorted(groups)

if __name__ == '__main__':

    basic_tests = [
            [ """ Basic test """,
"""
with concur:
    for x in [QBIT_1, QBIT_2, QBIT_3]:
        foo(x)
""",
"""
with concur:
    foo(QBIT_1)
    foo(QBIT_2)
    foo(QBIT_3)
"""
            ],

            [ """ Double Nested loops """,
"""
with concur:
    for x in [QBIT_1, QBIT_2, QBIT_3]:
        for y in [4, 5, 6]:
            foo(x, y)
""",
"""
with concur:
    foo(QBIT_1, 4)
    foo(QBIT_1, 5)
    foo(QBIT_1, 6)
    foo(QBIT_2, 4)
    foo(QBIT_2, 5)
    foo(QBIT_2, 6)
    foo(QBIT_3, 4)
    foo(QBIT_3, 5)
    foo(QBIT_3, 6)
"""
            ],

            [ """ Triple Nested loops """,
"""
with concur:
    for x in [QBIT_1, QBIT_2]:
        for y in [QBIT_3, QBIT_4]:
            for z in [5, 6]:
                foo(x, y, z)
""",
"""
with concur:
    foo(QBIT_1, QBIT_3, 5)
    foo(QBIT_1, QBIT_3, 6)
    foo(QBIT_1, QBIT_4, 5)
    foo(QBIT_1, QBIT_4, 6)
    foo(QBIT_2, QBIT_3, 5)
    foo(QBIT_2, QBIT_3, 6)
    foo(QBIT_2, QBIT_4, 5)
    foo(QBIT_2, QBIT_4, 6)
"""
            ],
            [ """ Basic compound test """,
"""
with concur:
    for x in [QBIT_1, QBIT_2, QBIT_3]:
        foo(x)
        bar(x)
""",
"""
with concur:
    foo(QBIT_1)
    bar(QBIT_1)
    foo(QBIT_2)
    bar(QBIT_2)
    foo(QBIT_3)
    bar(QBIT_3)
"""
            ],
            [ """ Nested compound test """,
"""
with concur:
    for x in [1, 2]:
        for y in [3, 4]:
            foo(x)
            bar(y)
""",
"""
with concur:
    foo(1)
    bar(3)
    foo(1)
    bar(4)
    foo(2)
    bar(3)
    foo(2)
    bar(4)
"""
            ],
            [ """ Simple tuple test """,
"""
with concur:
    for x, y in [(1, 2), (3, 4)]:
        foo(x, y)
""",
"""
with concur:
    foo(1, 2)
    foo(3, 4)
"""
            ],
            [ """ Simple tuple test 2 """,
"""
with concur:
    for x, y in [(QBIT_1, QBIT_2), (QBIT_3, QBIT_4)]:
        foo(x)
        foo(y)
""",
"""
with concur:
    foo(QBIT_1)
    foo(QBIT_2)
    foo(QBIT_3)
    foo(QBIT_4)
"""
            ],
            [ """ Compound test 2 """,
"""
with concur:
    for x in [QBIT_1, QBIT_2]:
        for y in [3, 4]:
            foo(x, y)

            for z in [5, 6]:
                bar(x, y, z)
""",
"""
with concur:
    foo(QBIT_1, 3)
    bar(QBIT_1, 3, 5)
    bar(QBIT_1, 3, 6)
    foo(QBIT_1, 4)
    bar(QBIT_1, 4, 5)
    bar(QBIT_1, 4, 6)
    foo(QBIT_2, 3)
    bar(QBIT_2, 3, 5)
    bar(QBIT_2, 3, 6)
    foo(QBIT_2, 4)
    bar(QBIT_2, 4, 5)
    bar(QBIT_2, 4, 6)
"""
            ],

            [ """ expression test """,
"""
with concur:
    for x in [1, 2]:
        for y in [3, 4]:
            foo(x + y)
""",
# extra level of parens needed for the pretty-printer
"""
with concur:
    foo((1 + 3))
    foo((1 + 4))
    foo((2 + 3))
    foo((2 + 4))
"""
            ],

        ]


    def test_case(description, in_txt, out_txt):
        ptree = ast.parse(in_txt, mode='exec')
        unroller = ConcurUnroller()
        new_ptree = unroller.visit(ptree)
        new_txt = pyqgl2.ast_util.ast2str(new_ptree)

        body = new_ptree.body[0].body
        # print('body %s' % ast.dump(body))

        grouper = QbitGrouper()
        redo = grouper.visit(new_ptree)

        partitions = grouper.group_stmnts(body)
        print('partitions: %s' % str(partitions))
        # for pid in partitions:
        #     print('[%s]\n%s' %
        #             (pid, pyqgl2.ast_util.ast2str(partitions[pid]).strip()))


        if out_txt.strip() != new_txt.strip():
            print('FAILURE: %s\n:[%s]\n----\n[%s]' %
                    (description, out_txt, new_txt))
            return False
        else:
            print('SUCCESS: %s' % description)
            return True

    def preprocess(fname):
        text = open(fname, 'r').read()
        ptree = ast.parse(text, mode='exec')

        print('INITIAL PTREE:\n%s' % pyqgl2.ast_util.ast2str(ptree))

        unroller = ConcurUnroller()
        new_ptree = unroller.visit(ptree)

        print('NEW PTREE:\n%s' % pyqgl2.ast_util.ast2str(new_ptree))

        # Now do the transformation

    def test_grouping1():

        def simple_find_qbits(stmnt):
            """
            debugging impl of find_qbits, for simple quasi-statements.

            Assumes that the stmnt is a tuple consisting of a list
            (of qbit numbers) and a string (the description of the statement)
            So finding the qbits is done by returning the first element
            of the tuple.

            See simple_stmnt_list below for an example.
            """

            return stmnt[0]

        simple_stmnt_list = [
                ( [1], 'one-1' ),
                ( [1], 'one-2' ),
                ( [2], 'two-1' ),
                ( [1], 'one-3' ),
                ( [2], 'two-2' ),
                ( [3], 'three-1' ),
                ( [4], 'four-1' ),
                ( [3, 4], 'threefour-1' )
                ]

        res = QbitGrouper.group_stmnts(simple_stmnt_list,
                find_qbits_func=simple_find_qbits)

        for stmnt_list in res:
            print('STMNT_LIST %s' % str(stmnt_list))

    def main():

        test_grouping1()

        for (description, in_txt, out_txt) in basic_tests:
            test_case(description, in_txt, out_txt)

        if len(sys.argv) > 1:
            for fname in sys.argv[1:]:
                preprocess(fname)

    main()
