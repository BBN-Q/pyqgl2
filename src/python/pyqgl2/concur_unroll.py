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

from pyqgl2.ast_util import ast2str, expr2ast, NodeError, value2ast
from pyqgl2.debugmsg import DebugMsg
from pyqgl2.importer import collapse_name
from pyqgl2.inline import QubitPlaceholder
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

def is_seq(node):
    """
    Return True if the node is a with-seq block,
    otherwise False
    """

    if not node:
        return False

    if not isinstance(node, ast.With):
        return False

    for item in node.items:
        if (isinstance(item.context_expr, ast.Name) and
                (item.context_expr.id == QGL2.QSEQ)):
            return True

    return False

def find_all_channels(node, local_vars=None):
    """
    Reinitialze the set of all_channels to be the set of
    all channels referenced in the AST rooted at the given
    node.

    This is a hack, because we assume we can identify all
    channels lexically.  FIXME
    """

    if not local_vars:
        local_vars = dict()

    all_channels = set()

    for subnode in ast.walk(node):
        if isinstance(subnode, ast.Name):

            # Ugly hard-coded assumption about channel names: FIXME
            #
            # Also look for bindings to QubitPlaceholders
            #
            if subnode.id.startswith('QBIT_'):
                all_channels.add(subnode.id)
            elif subnode.id.startswith('EDGE_'):
                all_channels.add(subnode.id)
            elif ((subnode.id in local_vars) and
                    (isinstance(local_vars[subnode.id], QubitPlaceholder))):
                all_channels.add(local_vars[subnode.id].use_name)

        # Look for references to inlined calls; dig out any
        # channels that might be hiding there despite being
        # optimized away later.
        #
        if hasattr(subnode, 'qgl2_orig_call'):
            orig_chan = find_all_channels(subnode.qgl2_orig_call, local_vars)
            # print('FAC %s -> %s' %
            #         (ast2str(subnode.qgl2_orig_call).strip(),
            #             str(orig_chan)))
            all_channels.update(orig_chan)

    return all_channels

class Unroller(ast.NodeTransformer):
    """
    A more general form of the ConcurUnroller, which knows how to
    "unroll" FOR loops and IF statements in more general contexts.

    TODO: document the subset of all possible cases that this
    code actually recognizes/handles
    """

    def __init__(self, importer):

        self.bindings_stack = list()
        self.change_cnt = 0

        self.importer = importer

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

    def check_value_types(self, target, values):
        """
        check that the list contains simple expressions:
        numbers, symbols, or other constants.  If there's
        anything else in the list, then bail out because
        we can't do a simple substitution.

        TODO: There are cases where we can't use names; if
        the body of the loop modifies the value bound to a
        symbol mentioned in iter.elts, then this may break.
        This case is hard to analyze but we could warn the
        programmer that something risky is happening.

        TODO: For certain idempotent exprs, we can do more
        inlining than for arbitrary expressions.  We don't
        have a mechanism for determining whether an expression
        is idempotent yet.
        """

        all_simple = True
        simple_expr_types = set(
                [ast.Num, ast.Str, ast.Name, ast.NameConstant])

        if isinstance(target, ast.Tuple):
            target_elts = target.elts
            target_len = len(target_elts)

            # Make sure this is a straightforward tuple of
            # names, and not nested in some way.  We don't
            # handle nested targets yet
            #
            for target_elt in target_elts:
                if not isinstance(target_elt, ast.Name):
                    NodeError.error_msg(target_elt,
                            'expected name, got [%s]' % type(target_elt))
                    return False

            # OK, now that we've determined that the target
            # is good, now check that every value that we need
            # to assign to the target is "compatible" and "simple":
            # it's got to be a list or tuple of the right length,
            # and consist of simple values.
            #
            for ind in range(len(values)):
                value = values[ind]

                if (not isinstance(value, ast.Tuple) and
                        not isinstance(value, ast.List)):
                    NodeError.error_msg(value,
                            'element %d is not a list or tuple' % ind)
                    return False

                if target_len != len(value.elts):
                    NodeError.error_msg(value,
                            ('element %d len != target len (%d != %d)' %
                                (ind, len(value.elts), target_len)))
                    return False

                for elem in value.elts:
                    if type(elem) not in simple_expr_types:
                        all_simple = False
                        break

        else:
            for elem in values:
                if type(elem) not in simple_expr_types:
                    all_simple = False
                    break

        if not all_simple:
            NodeError.diag_msg(target, 'not all loop elements are consts')

        return True # FIXME

    def is_simple_iteration(self, for_node):
        """
        returns (success, count), where success is True if the loop is
        a "simple iteration" (a single loop variable, which is never
        referenced inside the loop), and count is the number of times
        that the loop iterates.

        We could handle loops with multiple targets (as long as
        none of them are ever referenced), but we don't deal with
        this case yet.  The iters either needs to be a literal list
        (ast.List) or a call to the simple form of range().
        """

        assert isinstance(for_node, ast.For)

        if not isinstance(for_node.target, ast.Name):
            return False, 0

        if (isinstance(for_node.iter, ast.Call) and
                isinstance(for_node.iter.func, ast.Name) and
                (collapse_name(for_node.iter.func) == 'range')):

            # We can only handle simple things right now:
            # a simple range, with a simple parameter.
            #
            args = for_node.iter.args
            if len(args) != 1:
                return False, 0

            arg = args[0]
            if not isinstance(arg, ast.Num):
                return False, 0
            elif not isinstance(arg.n, int):
                NodeError.warning_msg(arg, 'range value is not an integer?')
                return False, 0

            iter_cnt = arg.n
        elif isinstance(for_node.iter, ast.List):
            print('EV GOT LIST')
            iter_cnt = len(for_node.iter.elts)
        else:
            return False, 0

        # Search through the body, looking for any of the following:
        #
        # a) a reference to the target name
        # (Omitted) b) a break statement
        # (Omitted) c) a continue statement
        #
        # If we find any of these, then it's not pure iteration; bail out
        #
        target_name = for_node.target.id
        for body_node in for_node.body:
            for subnode in ast.walk(body_node):
                if (isinstance(subnode, ast.Name) and
                        subnode.id == target_name):
                    NodeError.diag_msg(subnode,
                            ('ref to loop var [%s] disables Qrepeat' %
                                subnode.id))
                    return False, 0

        return True, iter_cnt

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
        DebugMsg.log("Unrolling a for loop %s" % for_node)
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

        # check to see if the for loop is a simple repeat.
        # In order for us to detect this, it really does
        # need to be pretty simple: the iter needs to be
        # a range() expression with a counter range, and
        # the target needs to not be referenced anywhere
        # within the body of the loop.
        #
        # If it's simple, then turn the for loop into a
        # "with repeat(N)" block, where N is the number
        # of iterations.  The flattener will turn this
        # into the proper ASP2 code.
        #
        (is_simple, iter_cnt) = self.is_simple_iteration(for_node)
        if is_simple:
            # If is_simple_iteration returns True, then this
            # chain of derefs should just work...
            #
            repeat_txt = 'with Qrepeat(%d):\n    pass' % iter_cnt
            repeat_ast = expr2ast(repeat_txt)

            pyqgl2.ast_util.copy_all_loc(repeat_ast, for_node, recurse=True)

            # even if we can't unroll this loop, we might
            # be able to unroll statements in the body of
            # the loop, so give that try
            #
            if unroll_inner:
                repeat_ast.body = self.unroll_body(for_node.body)
            else:
                repeat_ast.body = for_node.body

            return list([repeat_ast])

        # If we've expanded and evaluated for_node.iter, then
        # we expect it to be a list.  This might not have happened
        # yet, however.

        if not isinstance(for_node.iter, ast.List):
            if unroll_inner:
                # even if we can't unroll this loop, we might
                # be able to unroll statements in the body of
                # the loop, so give that try
                #
                new_body = self.unroll_body(for_node.body)
                for_node.body = new_body
            return list([for_node])

        vals = for_node.iter.elts
        if not self.check_value_types(for_node.target, vals):
            NodeError.diag_msg(for_node, 'not all loop elements are simple')

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

    def __init__(self, local_vars=None):

        if not local_vars:
            local_vars = dict()

        self.local_vars = local_vars

    def visit_With(self, node):

        if not is_concur(node):
            # print('IS NOT a concur node')
            return self.generic_visit(node) # check

        # Hackish way to create a seq node to use
        seq_item_node = deepcopy(node.items[0])
        seq_item_node.context_expr.id = QGL2.QSEQ
        seq_node = ast.With(items=list([seq_item_node]), body=list())
        pyqgl2.ast_util.copy_all_loc(seq_node, node)

        groups = self.group_stmnts2(node.body)
        new_body = list()

        for qbits, stmnts in groups:
            new_seq = deepcopy(seq_node)
            new_seq.body = stmnts
            # Mark an attribute on new_seq naming the qbits
            new_seq.qgl_chan_list = qbits
            NodeError.diag_msg(node,
                    "Adding new with seq marked with qbits %s" % (str(qbits)))
            new_body.append(new_seq)

        node.body = new_body

        # print('Final:\n%s' % pyqgl2.ast_util.ast2str(node))

        return node

    @staticmethod
    def is_qrepeat(node):
        """
        Return True if this is a "with qrepeat()" statement,
        False otherwise

        This is semi-fragile in how it looks into the "With"
        parameters.
        """

        if not isinstance(node, ast.With):
            return False
        elif not isinstance(node.items[0].context_expr, ast.Call):
            return False
        elif not isinstance(node.items[0].context_expr.func, ast.Name):
            return False
        elif node.items[0].context_expr.func.id != 'Qrepeat':
            return False
        else:
            return True

    @staticmethod
    def is_with_label(node, label):
        """
        TODO: there's code in other places that duplicates this;
        combine into a single function
        """

        if not isinstance(node, ast.With):
            return False
        elif not isinstance(node.items[0].context_expr, ast.Name):
            return False
        elif node.items[0].context_expr.id != label:
            return False
        else:
            return True

    def group_stmnts2(self, stmnts, find_qbits_func=None):
        """
        A different approach to grouping statements,
        which (hopefully) will work more cleanly on deep
        structures.  See group_stmnts for a basic overview
        of what this function attempts to do.

        NOTE: this function assumes that each statement
        is associated with exactly one qbit.  Operations
        that involve multiple qbits (like CNOT) are treated
        as having a "source" qbit, and this is the qbit
        associated with the statement.  (this may be
        overly simplistic)

        The basic approach taken by this method is:

        a) find all the qbits referenced by the stmnts

        b) for each qbit referenced:

            i) make a copy of the stmnts

            ii) for each qbit, traverse the copy, removing
                any statement that does not reference that qbit.
                (this is a recursive process, if the statements
                are themselves compound)

            iii) for each copy, remove any statements made
                degenerate by removing substatements (for
                example, you could end up with loops filled with
                "with Qiter: pass" statements, which can be safely
                elided).

        (To make this slightly simpler, we stripe this by
        statement, instead of doing the entire statement list
        at once in steps b.i--b.ii.)

        This consumes more memory than a pure construction,
        but it's simpler.
        """

        if find_qbits_func is None:
            find_qbits_func = find_all_channels

        all_qbits = set()

        for stmnt in stmnts:
            all_qbits.update(find_qbits_func(stmnt, self.local_vars))

        qbit2stmnts = dict()

        for qbit in all_qbits:
            new_stmnts = list()

            for stmnt in stmnts:
                pruned_stmnt = self.keep_qbit(stmnt, qbit, find_qbits_func)
                new_stmnts.append(pruned_stmnt)

            if new_stmnts:
                qbit2stmnts[qbit] = new_stmnts
            else:
                print('GR2: expected to find at least one stmnt? [%s]', qbit)

        """
        for qbit in qbit2stmnts:
            print('GR2 final %s' % qbit)
            for substmnt in qbit2stmnts[qbit]:
                print('   %s' % ast2str(substmnt).strip())
        """

        groups = [ (list([qbit]), qbit2stmnts[qbit])
                for qbit in qbit2stmnts.keys() ]

        return groups

    def keep_qbit(self, stmnt, qbit, finder):
        """
        Fake scaffolding that only looks at the top-level

        NOTE: only looks at the top level and
        determines whether they match the given qbit
        and whether the stmnt contains more than
        one qbit

        TODO: does not examine the internal structure
        of statements in general; the only compound structure
        it considers is the body of top-level Qfor statements

        TODO: add special case (probably to the finder)
        to address the problem of operators that take
        multiple qbits, such as CNOT.
        """

        if self.is_with_label(stmnt, 'Qfor'):
            new_body = list()

            # this is wasteful: we make a copy of the whole
            # thing, and then end up throwing away everything
            # but the header.  Should allocate only the header.
            #
            new_qfor = deepcopy(stmnt)

            # TODO: the only thing that should be in the body of a
            # Qfor is a Qiter, but we don't do anything if this
            # assumption is violated.
            #
            for substmnt in stmnt.body:
                if not self.is_with_label(substmnt, 'Qiter'):
                    print('EXPECTED Qiter')

                if self.keep_qbit(substmnt, qbit, finder):
                    new_body.append(substmnt)

            # We can't have a completely empty body, so add a pass
            # if necessary
            #
            if not new_body:
                new_body = list([ast.Pass()])

            new_qfor.body = new_body
            return new_qfor

        # The general case: it's not a Qfor, at least not at the
        # top level.  It's all or nothing, then.

        qbits = finder(stmnt, self.local_vars)
        n_qbits = len(qbits)
        if n_qbits == 0:
            NodeError.error_msg(stmnt,
                    ('no qbit references in stmnt? [%s]' %
                        ast2str(stmnt).strip()))
            return None
            
        elif n_qbits > 1:
            print('multiple qbit references (%s) in stmnt [%s]' %
                        (str(qbits), ast2str(stmnt).strip()))
            NodeError.error_msg(stmnt,
                    ('multiple qbit references (%s) in stmnt [%s]' %
                        (str(qbits), ast2str(stmnt).strip())))
            return None

        if qbit in qbits:
            return stmnt
        else:
            return None

    def group_stmnts(self, stmnts, find_qbits_func=None):
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

        Note that the first step in the partitioning may result
        in the creation of additional statements, with the goal
        of simplifying the later partitioning.  For example, if
        we have a simple iterative loop with more than one qbit
        referenced within it:

                with qrepeat(3):
                    something(QBIT_1)
                    something(QBIT_2)
                    something(QBIT_3)

        In this example, the with statement references three qbits,
        which is an awkward partition.  We can partition the body
        to create three separate loops:

                with qrepeat(3):
                    something(QBIT_1)
                with qrepeat(3):
                    something(QBIT_2)
                with qrepeat(3):
                    something(QBIT_3)

        This seems to create more work, but since the loops are
        going to run on three disjoint sets of hardware, it's
        actually simpler and closer to the actual instruction
        sequence.
        """

        if find_qbits_func is None:
            find_qbits_func = find_all_channels

        qbit2list = dict()

        expanded_stmnts = list()

        # Make a first pass over the list of statements,
        # looking for any that need to be partitioned by creating
        # new statements, thus creating an expanded list of
        # statements.
        #
        # See above for an example.
        #
        for stmnt in stmnts:

            # If this is a qrepeat statement, then partition
            # its body and then create a new qrepeat statement
            # for each partition.
            #
            # Eventually there may be other kinds of statements
            # that we expand, but qrepeat is the only one we
            # expand now
            #
            if QbitGrouper.is_qrepeat(stmnt):

                rep_groups = self.group_stmnts(stmnt.body)
                for partition, substmnts in rep_groups:
                    # lazy way to create the specialized qrepeat:
                    # copy the whole thing, and then throw away
                    # its body and replace it with the partition.
                    #
                    new_qrepeat = deepcopy(stmnt)
                    new_qrepeat.body = substmnts

                    expanded_stmnts.append(new_qrepeat)
            elif QbitGrouper.is_with_label(stmnt, 'Qfor'):
                # TODO: must deal with Qfor and Qiters here.
                expanded_stmnts.append(stmnt)

            else:
                expanded_stmnts.append(stmnt)

        for stmnt in expanded_stmnts:

            qbits_referenced = list(find_qbits_func(stmnt, self.local_vars))
            # print('GR %s -> %s' %
            #         (ast2str(stmnt).strip(), str(qbits_referenced)))

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
                (qbits, _stmnts) = tmp_groups[stmnts_str]
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
