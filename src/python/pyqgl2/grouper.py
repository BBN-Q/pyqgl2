# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
Group nodes by the qbits they operate on
"""

import ast
import os
import sys

from copy import deepcopy

import pyqgl2.ast_util

from pyqgl2.ast_util import ast2str, expr2ast, value2ast
from pyqgl2.ast_util import copy_all_loc
from pyqgl2.ast_util import NodeError
from pyqgl2.debugmsg import DebugMsg
from pyqgl2.flatten import is_with_label
from pyqgl2.importer import collapse_name
from pyqgl2.inline import BarrierIdentifier
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

def is_infunc(node):
    """
    Return True if the node is a with-infunc block,
    otherwise False
    """

    if not node:
        return False

    if not isinstance(node, ast.With):
        return False

    item = node.items[0].context_expr

    if not isinstance(item, ast.Call):
        return False
    elif not item.func.id == 'infunc':
        return False
    else:
        return True

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

class MarkReferencedQbits(ast.NodeVisitor):
    """
    NodeVisitor that initializes a member named qgl2_referenced_qbits
    to be the set of qbit names referenced by each node in a given AST

    Assumed to be used after the inlining and evaluation has been done.
    Does not treat qbit creation specially (at least not yet): this
    is handled elsewhere right now.
    """

    def __init__(self, local_vars=None, force_recursion=False):

        if local_vars:
            self.local_vars = local_vars
        else:
            self.local_vars = dict()

        self.force_recursion = force_recursion

    def visit_Name(self, node):

        # Ugly hard-coded assumption about channel names: FIXME
        #
        # Also look for bindings to QubitPlaceholders
        #

        referenced_qbits = set()

        if node.id.startswith('QBIT_'):
            referenced_qbits.add(node.id)
        elif node.id.startswith('EDGE_'):
            referenced_qbits.add(node.id)
        elif ((node.id in self.local_vars) and
                (isinstance(self.local_vars[node.id], QubitPlaceholder))):
            referenced_qbits.add(self.local_vars[node.id].use_name)

        node.qgl2_referenced_qbits = referenced_qbits

    def visit(self, node):

        referenced_qbits = set()

        # If we've already run over this subtree, then we don't need
        # to examine it again.  (this assumes that any modifications
        # and reinvocations of this traversal happen at the root of
        # of the AST)
        #
        # TODO: provide some way to check this assumption
        #
        if ((not self.force_recursion) and
                hasattr(node, 'qgl2_referenced_qbits')):
            return

        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.Name):
                self.visit_Name(child)
            else:
                self.visit(child)

            if hasattr(child, 'qgl2_referenced_qbits'):
                referenced_qbits.update(child.qgl2_referenced_qbits)

        node.qgl2_referenced_qbits = referenced_qbits

    @staticmethod
    def marker(node, local_vars=None):
        """
        Helper function: creates a MarkReferencedQbits instance
        with the given local variables, the uses this instance to
        visit each AST element of the node and mark it with the
        set of qbits it references, and then returns the set of
        all qbits referenced by the root node
        """

        marker_obj = MarkReferencedQbits(local_vars=local_vars) 
        marker_obj.visit(node)

        return node.qgl2_referenced_qbits

class AddSequential(ast.NodeTransformer):
    """
    Insert barriers to implement sequentiality when in the
    outermost block (the @qgl2main) or inside an expanded function
    and not inside a with-concur.
    statements.

    By default, statements that are not directly within a 
    with-concur block are treated as sequential.  For example,
    if a function is invoked inside a with-concur block,
    the statements of that function are not "directly" within
    that with-concur and therefore are executed sequentially
    unless the body of the function is itself a with-concur
    block.
    """

    def __init__(self):

        # in_concur is True if we're in a point in the traversal
        # where we're within a with-concur block but not inside a
        # a with-infunc that is a descendant of that with-concur.
        #
        self.in_concur = False
        self.referenced_qbits = set()

    @staticmethod
    def add_barriers(node):
        """
        Destructively add barriers to the given node (which must be
        a function definition) to enforce sequential execution,
        where necessary.
        """

        assert isinstance(node, ast.FunctionDef), 'node must be a FunctionDef'

        new_preamble = list()
        new_body = list()

        # Split the statements into the preamble and the
        # "real" body
        #
        # if it's a qbit_creation, or it doesn't appear to
        # have any qbit references in it, then put it in
        # the preamble
        #
        # otherwise, put it in the candidate new body,
        #
        for stmnt in node.body:
            if (isinstance(stmnt, ast.Assign) and
                    stmnt.targets[0].qgl_is_qbit):
                new_preamble.append(stmnt)
            elif not stmnt.qgl2_referenced_qbits:
                new_preamble.append(stmnt)
            else:
                new_body.append(stmnt)

        # Use expand_body to add barriers to the body recursively
        #
        add_seq = AddSequential()
        add_seq.in_concur = False
        add_seq.referenced_qbits = node.qgl2_referenced_qbits

        new_body = add_seq.expand_body(new_body)

        node.body = new_preamble + new_body

        return node

    def visit(self, node):

        if not hasattr(node, 'qgl2_referenced_qbits'):
            return node

        # Special case: if we're called on a function def,
        # then use add_barriers instead, because function
        # definitions are different than ordinary statements
        #
        if isinstance(node, ast.FunctionDef):
            return self.add_barriers(node)

        # Save a copy of the current state, so we can
        # restore it later (even if we don't actually
        # modify the state)
        #
        prev_state = self.in_concur
        prev_qbits = self.referenced_qbits

        # Figure out if we might be entering a new execution mode
        # (with-concur or with-infunc).  If we are, then we need
        # to change the state variables before recursing.
        #
        entering_concur = is_concur(node)
        entering_infunc = is_infunc(node)

        if entering_concur or entering_infunc:
            self.referenced_qbits = node.qgl2_referenced_qbits

        if entering_concur:
            self.in_concur = True
        elif entering_infunc:
            self.in_concur = False

        if hasattr(node, 'body'):
            node.body = self.expand_body(node.body)

            if entering_concur:
                beg_barrier = self.make_barrier_ast(
                        self.referenced_qbits, node, name='concur_b')
                end_barrier = self.make_barrier_ast(
                        self.referenced_qbits, node, name='concur_e')
                node.body = [beg_barrier] + node.body + [end_barrier]

        if hasattr(node, 'orelse'):
            node.orelse = self.expand_body(node.orelse)

        # put things back the way they were (even if we didn't
        # change anything)
        #
        self.in_concur = prev_state
        self.referenced_qbits = prev_qbits

        return node

    def expand_body(self, body):
        """
        We need to set the qgl2_referenced_qbits properly
        in the new with-concur nodes correctly in order to ensure
        that statements that operate on distinct sets of qbits
        are still made sequential, even though they don't "conflict".
        In essence, we must make them conflict.
        """

        new_body = list()
        cnt = 0

        # If the statement is any sort of "with", then pass it
        # straight through, because this means that it's a
        # container of some sort.  We only insert barriers around
        # "simple" statements.
        #
        # If it's a qbit creation, then let it go through without
        # serializing; these statements will all be moved to the
        # preamble anyway.
        #
        for stmnt in body:
            # We don't put barriers around with statements;
            # we only put them around "primitive" statements
            # or as the side effect of with statements
            #
            new_stmnt = self.visit(stmnt)

            if self.is_with_container(new_stmnt):
                new_body.append(new_stmnt)
            elif self.in_concur:
                new_body.append(new_stmnt)
            else:
                barrier_ast = self.make_barrier_ast(
                        self.referenced_qbits, stmnt, name='seq')

                new_body.append(barrier_ast)
                new_body.append(new_stmnt)

        if not (self.in_concur or self.is_with_container(new_stmnt)):
            barrier_ast = self.make_barrier_ast(
                    self.referenced_qbits, stmnt, name='eseq')
            new_body.append(barrier_ast)

        return new_body

    def is_with_container(self, node):
        """
        Return True if the node is a "with" statement that
        we use in the preprocessor as a container for loops
        or iterations of loops, False otherwise.

        These containers are for bookkeeping and therefore
        are not subject to barriers.

        In some cases, we add extra barriers for the sake
        of readability -- otherwise readers are confused
        about why they're missing, even though the "obvious"
        barriers often turn out to be redundant.  Most of
        the time, we try to get rid of redundant barriers
        because they just obscure what's going on.
        """

        if not isinstance(node, ast.With):
            return False
        # elif is_with_label(node, 'Qfor'):
        #     return True
        elif is_with_label(node, 'Qiter'):
            return True
        else:
            return False

    def make_barrier_ast(self, qbits, node, name='seq'):

        bid = BarrierIdentifier.next_bid()
        arg_names = sorted(list(qbits))
        arg_list = '[%s]' % ', '.join(arg_names)

        barrier_ast = expr2ast(
                'Barrier(\'%s_c_%d\', %s)' % (name, bid, arg_list))

        # TODO: make sure that this gets all of the qbits.
        # It might need local scope info as well, which we don't
        # have here.
        #
        MarkReferencedQbits.marker(barrier_ast)

        print('MARKED [%s] %s' %
                (str(barrier_ast.qgl2_referenced_qbits), str(qbits)))

        copy_all_loc(barrier_ast, node, recurse=True)

        return barrier_ast


class AddBarriers(ast.NodeTransformer):
    """
    NodeTransformer that replaces with-infunc and with-concur nodes
    with the corresponding barriers.

    This was done in the flattener, but that's an awkward place,
    and we might want to move it around again so it make sense
    to break it out into its own transformer.

    In order to "inline" a with statement into a pair of
    barriers surrounding the body of the with statement,
    we need to actually modify the body of the parent of the
    with node.  This makes this class look different from
    an ordinary type-based transformer, because we search
    all bodies and orelse statement lists for withs, and
    process them that way (as well, of course, as recursing
    to expand embedded with statements as well).
    """

    def __init__(self, local_vars=None):

        if not local_vars:
            local_vars = dict()

        self.local_vars = local_vars

    def visit(self, node):
        """
        The ordinary visit: recurse on all children,
        and then scan through any 'body' or 'orelse'
        lists, looking for with statements we can
        expand inline.
        """

        new_node = self.generic_visit(node)

        if hasattr(new_node, 'body'):
            new_node.body = self.expand_body(new_node.body)

        if hasattr(new_node, 'orelse'):
            new_node.orelse = self.expand_body(new_node.orelse)

        return new_node

    def expand_body(self, body):

        new_body = list()

        for stmnt in body:
            if is_concur(stmnt):
                new_body += self.transform_concur(stmnt)
            elif is_infunc(stmnt):
                new_body += self.transform_infunc(stmnt)
            else:
                new_body.append(stmnt)

        return new_body

    def transform_concur(self, node):

        qbits = node.qgl2_referenced_qbits
        bid = BarrierIdentifier.next_bid()

        arg_names = sorted(list(qbits))
        arg_list = '[%s]' % ', '.join(arg_names)

        b1_ast = expr2ast('Barrier(\'beg_c_%d\', %s)' % (bid, arg_list))
        b2_ast = expr2ast('Barrier(\'end_c_%d\', %s)' % (bid, arg_list))

        MarkReferencedQbits.marker(b1_ast, local_vars=self.local_vars)
        MarkReferencedQbits.marker(b2_ast, local_vars=self.local_vars)

        return [b1_ast] + node.body + [b2_ast]

    def transform_infunc(self, node):
        """
        Essentially identical to transform_concur, except uses
        a different name for the barrier (TBD).
        """

        # I think this will work because the original with-infunc
        # pseudo-call should reference all the qbits we care about

        qbits = node.qgl2_referenced_qbits
        bid = BarrierIdentifier.next_bid()

        arg_names = sorted(list(qbits))
        arg_list = '[%s]' % ', '.join(arg_names)

        b1_ast = expr2ast('Barrier(\'beg_i_%d\', %s)' % (bid, arg_list))
        b2_ast = expr2ast('Barrier(\'end_i_%d\', %s)' % (bid, arg_list))

        MarkReferencedQbits.marker(b1_ast, local_vars=self.local_vars)
        MarkReferencedQbits.marker(b2_ast, local_vars=self.local_vars)

        return [b1_ast] + node.body + [b2_ast]


class QbitPruner(ast.NodeTransformer):
    """
    NodeTransformer that prunes out statements that do not reference
    any members of a given set of qbits.  Note that we should not prune
    out anything below the statement level.

    If the body or the orelse of a statement is reduced to the
    empty list by this pruning, then it is replaced with a "pass"
    statement.

    Assumed to be used after the inlining and evaluation has been done,
    and after MarkReferencedQbits.visit() has been used to detect
    which qbits are used by each node.

    Does not treat qbit creation specially (at least not yet): this
    is handled elsewhere right now.
    """

    def __init__(self, active_qbits):

        self.active_qbits = active_qbits

    def visit(self, node):

        if not node.qgl2_referenced_qbits.intersection(self.active_qbits):
            return None

        if hasattr(node, 'body'):
            new_body = self.prune_body(node.body)
            if not new_body:
                new_body = list([ast.Pass()]) # bogus! debugging
            node.body = new_body

        if hasattr(node, 'orelse'):
            node.orelse = self.prune_body(node.orelse)

        return node

    def prune_body(self, old_body):
        """
        Prune out statements that don't reference the active qbits.
        """

        new_body = list()

        for old_stmnt in old_body:
            if old_stmnt.qgl2_referenced_qbits.intersection(self.active_qbits):
                new_stmnt = self.visit(old_stmnt)
                if new_stmnt:
                    new_body.append(new_stmnt)

        return new_body

class SeqAddBarriers(ast.NodeTransformer):
    """
    Insert barriers within the code to implement sequential
    instructions, and with-concur

    Assumes that the qbit annotations have already been done
    """

    def __init__(self):

        self.qbits_stack = list()

    def visit(self, node):
        # if node is an ast.With, then call visit_With.
        # otherwise, recurse on the descendants

        return node

    def visit_With(self, node):

        if is_concur(node):
            # 1. find the set of referenced qbits within the concur
            # block (by looking at the annotation already calculated)
            # 2. push this set onto qbits_stack
            # 3. Recurse on each subnode in the body
            # 4. pop the set from qbits_stack
            # 5. add start and end barriers before/after the body
            # 6. return the new node.
            return node

        elif is_infunc(node):
            # 1. push the set of parameter qbits onto qbits_stack
            # 2. recurse on each subnode in the body
            # 3. make the body sequential, by inserting barriers
            # between each statement, and before/after barriers
            # 4. pop the set of parameter qbits from qbits_stack
            # 5. replace the body with the new barrier-filled body
            # 6. return the new node
            return node

        else:
            # no new barriers at this level; just recurse on children
            return node

    @staticmethod
    def add_barriers(node):
        """
        Convenience function
        """

        barriers = SeqAddBarriers()
        return barriers.visit(node)

class QbitGrouper2(ast.NodeTransformer):
    """
    """

    def __init__(self, local_vars=None):

        if not local_vars:
            local_vars = dict()

        self.local_vars = local_vars

    def visit_FunctionDef(self, node):
        """
        The grouper should only be used on a function def,
        and there shouldn't be any nested functions, so this
        should effectively be the top-level call.

        Note that the initial qbit creation/assignment is
        treated as a special case: these statements are
        purely classical bookkeeping, even though they look
        like quantum operations, and are left alone.
        """

        all_qbits = MarkReferencedQbits.marker(
                node, local_vars=self.local_vars)

        print('REFERENCED: %s' % str(all_qbits))

        qbit_seqs = list()

        for qbit in all_qbits:
            scratch = deepcopy(node)

            pruned = QbitPruner(set([qbit])).visit(scratch)
            if pruned:
                qbit_seqs.append(pruned)

        for seq in qbit_seqs:
            print('XX:\n%s' % ast2str(seq))

    @staticmethod
    def group(node, local_vars=None):

        new_node = deepcopy(node)

        all_qbits = MarkReferencedQbits.marker(node, local_vars=local_vars)

        # TODO: need to check that it's a FunctionDef

        alloc_stmnts = list()
        body_stmnts = list()

        # Divide between qbit allocation and ordinary
        # statements.  This is ugly: it would be better
        # to move qbit allocation outside qgl2main. TODO
        # 
        for stmnt in node.body:
            if (isinstance(stmnt, ast.Assign) and
                    stmnt.targets[0].qgl_is_qbit):
                alloc_stmnts.append(stmnt)
            else:
                body_stmnts.append(stmnt)

        new_groups = list()

        for qbit in sorted(all_qbits):
            scratch_body = deepcopy(body_stmnts)

            pruned_body = QbitPruner(set([qbit])).prune_body(scratch_body)
            if not pruned_body:
                continue

            with_group = expr2ast('with group(%s): pass' % qbit)
            copy_all_loc(with_group, node, recurse=True)

            with_group.body = pruned_body
            with_group.qbit = qbit
            MarkReferencedQbits.marker(with_group, local_vars=local_vars)

            new_groups.append(with_group)

        with_grouped = expr2ast('with grouped: pass')
        copy_all_loc(with_grouped, node, recurse=True)
        MarkReferencedQbits.marker(with_grouped, local_vars=local_vars)

        with_grouped.body = new_groups

        new_node.body = alloc_stmnts + list([with_grouped])

        return new_node

