# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
Group nodes by the qbits they operate on
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

    def __init__(self, local_vars=None):

        if local_vars:
            self.local_vars = local_vars
        else:
            self.local_vars = dict()

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
            with_group.body = pruned_body
            with_group.qbit = qbit

            # TODO: copy location info into with_group
            # TODO: update qbit references in with_group

            new_groups.append(with_group)

        with_grouped = expr2ast('with grouped: pass')
        with_grouped.body = new_groups

        # TODO: copy location info into with_grouped
        # TODO: update qbit references in with_grouped

        # TODO: this is not correct; doesn't have the alloc
        # statements yet!
        # TODO: does not reconstruct the original function!

        print('ALT GROUP\n%s' % ast2str(with_grouped))

        return with_grouped # THIS IS NOT THE funcdef!


