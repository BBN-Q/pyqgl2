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
    Insert with-concur statements that implement sequential
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

        self.all_referenced_qbits = None
        self.level = 0

    def visit(self, node):
        """
        Recurse on all children, and then scan through
        any 'body' or 'orelse' lists, changing each statement
        into its own with-concur block unless it already *is*
        a with concur-block.
        """

        if not self.all_referenced_qbits:
            self.all_referenced_qbits = node.qgl2_referenced_qbits

            print('TOPLEVEL %s' % str(self.all_referenced_qbits))

        new_node = self.generic_visit(node)

        if hasattr(new_node, 'body'):
            new_node.body = self.expand_body(new_node.body)

        if hasattr(new_node, 'orelse'):
            new_node.orelse = self.expand_body(new_node.orelse)

        return new_node

    def expand_body(self, body):
        """
        We need to set the qgl2_referenced_qbits properly
        in the new with-concur nodes correctly in order to ensure
        that statements that operate on distinct sets of qbits
        are still made sequential, even though they don't "conflict".
        In essence, we must make them conflict.
        """

        new_body = list()

        for stmnt in body:
            if is_concur(stmnt):
                new_body.append(stmnt)
            else:
                concur_ast = expr2ast('with concur: pass')
                concur_ast.qgl2_referenced_qbits = self.all_referenced_qbits
                concur_ast.body[0] = stmnt
                new_body.append(concur_ast)

        return new_body


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
        arg_names = sorted(list(qbits))

        barrier_id = BarrierIdentifier.next_bid()
        b1_ast = expr2ast(
                'BarrierBegin(%d, %s)' % (barrier_id, ', '.join(arg_names)))
        b2_ast = expr2ast(
                'BarrierEnd(%d, %s)' % (barrier_id, ', '.join(arg_names)))

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
        arg_names = sorted(list(qbits))

        barrier_id = BarrierIdentifier.next_bid()
        b1_ast = expr2ast(
                'BarrierBegin(%d, %s)' % (barrier_id, ', '.join(arg_names)))
        b2_ast = expr2ast(
                'BarrierEnd(%d, %s)' % (barrier_id, ', '.join(arg_names)))

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

        for qbit in all_qbits:
            scratch_body = deepcopy(body_stmnts)

            pruned_body = QbitPruner(set([qbit])).prune_body(scratch_body)
            if not pruned_body:
                continue

            with_group = expr2ast('with group: pass')
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

