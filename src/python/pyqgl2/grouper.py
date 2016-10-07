# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
Group nodes by the qbits they operate on
"""

import ast

import pyqgl2.ast_util

from pyqgl2.ast_qgl2 import is_with_label
from pyqgl2.ast_qgl2 import is_concur, is_infunc
from pyqgl2.ast_util import ast2str, expr2ast
from pyqgl2.ast_util import copy_all_loc
from pyqgl2.ast_util import NodeError
from pyqgl2.inline import BarrierIdentifier
from pyqgl2.inline import QubitPlaceholder
from pyqgl2.debugmsg import DebugMsg
from pyqgl2.quickcopy import quickcopy

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
            elif subnode.id in local_vars:
                print('SYM IN LOCAL_VARS %s' % subnode.id)
                if isinstance(local_vars[subnode.id], QubitPlaceholder):
                    all_channels.add(local_vars[subnode.id].use_name())

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
            referenced_qbits.add(self.local_vars[node.id].use_name())

        node.qgl2_referenced_qbits = referenced_qbits

    def visit(self, node):

        referenced_qbits = set()

        # Some ancillary nodes related to assignment or name resolution
        # cause issues later, and have no effect on qbit refs, so
        # skip them.  Right now Load seems to be the only troublemaker
        #
        if isinstance(node, ast.Load):
            return

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

        # If this is an inline expansion of a function, then
        # make sure that qbits passed to that call are
        # marked and added to the referenced qbits for this node.
        #
        if hasattr(node, 'qgl2_orig_call'):
            orig_call = node.qgl2_orig_call
            self.visit(orig_call)
            referenced_qbits.update(orig_call.qgl2_referenced_qbits)

        node.qgl2_referenced_qbits = referenced_qbits

    @staticmethod
    def marker(node, local_vars=None, force_recursion=False):
        """
        Helper function: creates a MarkReferencedQbits instance
        with the given local variables, the uses this instance to
        visit each AST element of the node and mark it with the
        set of qbits it references, and then returns the set of
        all qbits referenced by the root node
        """

        marker_obj = MarkReferencedQbits(
                local_vars=local_vars, force_recursion=force_recursion)
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
            # if (isinstance(stmnt, ast.Assign) and
            #         stmnt.targets[0].qgl_is_qbit):
            if isinstance(stmnt, ast.Assign):
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

        new_body, new_refs = add_seq.expand_body(new_body)
        if new_refs:
            node.qgl2_referenced_qbits = new_refs

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
            node.body, new_refs = self.expand_body(node.body)
            if new_refs:
                node.qgl2_referenced_qbits = new_refs

            for stmnt in node.body:
                if not stmnt.qgl2_referenced_qbits:
                    stmnt.qgl2_referenced_qbits = new_refs

            # if we're entering a concur block and have
            # more than one qbit to protect, then add a
            # begin and end barrier
            #
            if entering_concur and len(self.referenced_qbits) > 0:
                bid = BarrierIdentifier.next_bid()

                beg_barrier = self.make_barrier_ast(
                        self.referenced_qbits, node,
                        name='concur_beg', bid=bid)
                end_barrier = self.make_barrier_ast(
                        self.referenced_qbits, node,
                        name='concur_end', bid=bid)
                node.body = [beg_barrier] + node.body + [end_barrier]

        if hasattr(node, 'orelse') and node.orelse:
            node.orelse, new_refs = self.expand_body(node.orelse)
            if new_refs:
                node.qgl2_referenced_qbits = new_refs

        if DebugMsg.ACTIVE_LEVEL < 3:
            print('NODE %s => %s %s' %
                  (ast2str(node).strip(),
                   str(node.qgl2_referenced_qbits),
                   str(self.referenced_qbits)))

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

        updated_qbit_refs = None

        # This shouldn't happen, but deal with it if it does
        #
        if len(body) == 0:
            return new_body, updated_qbit_refs

        # If the statement is any sort of "with", then pass it
        # straight through, because this means that it's a
        # container of some sort.  We only insert barriers around
        # "simple" statements.
        #
        # If it's a qbit creation, then let it go through without
        # serializing; these statements will all be moved to the
        # preamble anyway.
        #

        bid = BarrierIdentifier.next_bid()

        for ind in range(len(body)):
            stmnt = body[ind]

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
                if len(self.referenced_qbits) > 1:
                    barrier_ast = self.make_barrier_ast(
                            self.referenced_qbits, stmnt,
                            name='seq_%d' % ind, bid=bid)
                    new_body.append(barrier_ast)

                new_body.append(new_stmnt)

                updated_qbit_refs = self.referenced_qbits

        if not (self.in_concur or self.is_with_container(new_stmnt)):
            if len(self.referenced_qbits) > 1:
                barrier_ast = self.make_barrier_ast(
                        self.referenced_qbits, stmnt,
                        name='eseq_%d' % len(body), bid=bid)
                new_body.append(barrier_ast)

            updated_qbit_refs = self.referenced_qbits

        return new_body, updated_qbit_refs

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

        if is_with_label(node, 'Qiter'):
            return True
        else:
            return False

    @staticmethod
    def make_barrier_ast(qbits, node, name='seq', bid=None):

        if not bid:
            bid = BarrierIdentifier.next_bid()

        arg_names = sorted(list(qbits))
        arg_list = '[%s]' % ', '.join(arg_names)
        barrier_name = '%s_%d' % (name, bid)

        barrier_ast = expr2ast(
                'Barrier(\'%s\', %s)' % (barrier_name, arg_list))

        # TODO: make sure that this gets all of the qbits.
        # It might need local scope info as well, which we don't
        # have here.
        #
        MarkReferencedQbits.marker(barrier_ast)

        copy_all_loc(barrier_ast, node, recurse=True)

        # Add an "implicit import" for the Barrier function
        #
        barrier_ast.value.qgl_implicit_import = (
                'Barrier', 'qgl2.qgl1control', 'Barrier')

        # print('MARKED %s [%s] %s' %
        #         (barrier_name,
        #             str(barrier_ast.qgl2_referenced_qbits), str(qbits)))

        return barrier_ast


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


class QbitGrouper2(object):
    """
    """

    def __init__(self, local_vars=None):

        if not local_vars:
            local_vars = dict()

        self.local_vars = local_vars

    @staticmethod
    def group(node, local_vars=None):

        new_node = quickcopy(node)

        all_qbits = MarkReferencedQbits.marker(
                node, local_vars=local_vars, force_recursion=True)

        # TODO: need to check that it's a FunctionDef

        alloc_stmnts = list()
        body_stmnts = list()

        # Divide between qbit allocation and ordinary
        # statements.  This is ugly: it would be better
        # to move qbit allocation outside qgl2main. TODO
        # 
        for stmnt in node.body:
            # if (isinstance(stmnt, ast.Assign) and
            #         stmnt.targets[0].qgl_is_qbit):
            if isinstance(stmnt, ast.Assign):
                alloc_stmnts.append(stmnt)
            else:
                body_stmnts.append(stmnt)

        new_groups = list()

        for qbit in sorted(all_qbits):
            scratch_body = quickcopy(body_stmnts)

            pruned_body = QbitPruner(set([qbit])).prune_body(scratch_body)
            if not pruned_body:
                continue

            with_group = expr2ast('with group(%s): pass' % qbit)
            copy_all_loc(with_group, node, recurse=True)

            # Insert a special Barrier named "group_marker..."
            # at the start of each per-qbit group.
            # The compiler later looks for this to know
            # which sequence is for which Qubit.
            bid = BarrierIdentifier.next_bid()
            beg_barrier = AddSequential.make_barrier_ast(
                [qbit], with_group,
                name='group_marker', bid=bid)
            if DebugMsg.ACTIVE_LEVEL < 3:
                print("For qbit %s, inserting group_marker: %s" % (qbit, ast2str(beg_barrier)))

            with_group.body = [beg_barrier] + pruned_body

            with_group.qbit = qbit
            MarkReferencedQbits.marker(with_group, local_vars=local_vars)

            new_groups.append(with_group)

        with_grouped = expr2ast('with grouped: pass')
        copy_all_loc(with_grouped, node, recurse=True)
        MarkReferencedQbits.marker(with_grouped, local_vars=local_vars)

        with_grouped.body = new_groups

        new_node.body = alloc_stmnts + list([with_grouped])

        return new_node

