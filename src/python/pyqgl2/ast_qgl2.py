# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
AST utilities related to QGL2 nodes (primarily with-statements)
"""

import ast
import os
import sys

from pyqgl2.debugmsg import DebugMsg
from pyqgl2.lang import QGL2

def is_with_label(node, label):
    """
    Return True if the given node is a with-statement that has
    as its "item", an ast.Name with the given label, else False

    A with-statement may have multiple items, but we ignore
    this and only consider the first.

    TODO: we should reject with-statements that have more than
    one item (although they are perfectly valid to Python, they
    cannot be valid as QGL2 statements).
    """

    if not node:
        DebugMsg.log('unexpected None node', level=DebugMsg.ALL)
        return False
    elif not isinstance(node, ast.With):
        # DebugMsg.log('unexpected non-With node', level=DebugMsg.ALL)
        return False

    item = node.items[0].context_expr

    if not isinstance(item, ast.Name):
        return False
    elif item.id != label:
        return False
    else:
        return True

def is_with_call(node, funcname):
    """
    Return True if the given node is a with-statement that has
    as its "item", an ast.Call to a function with the given
    funcname, else False

    A with-statement may have multiple items, but we ignore
    this and only consider the first.

    TODO: we should reject with-statements that have more than
    one item (although they are perfectly valid to Python, they
    cannot be valid as QGL2 statements).
    """

    if not node:
        DebugMsg.log('unexpected None node', level=DebugMsg.ALL)
        return False
    elif not isinstance(node, ast.With):
        # DebugMsg.log('unexpected non-With node', level=DebugMsg.ALL)
        return False

    item = node.items[0].context_expr

    if not isinstance(item, ast.Call):
        return False
    elif not isinstance(item.func, ast.Name):
        return False
    elif item.func.id != funcname:
        return False
    else:
        return True

def is_concur(node):
    """
    Returns True if the node is a with-concur statement,
    False otherwise.

    A convenience wrapper for is_with_label.
    """

    return is_with_label(node, QGL2.QCONCUR)

def is_infunc(node):
    """
    Return True if the node is a with-infunc statement,
    False otherwise.

    A convenience wrapper for is_with_call.
    """

    return is_with_call(node, QGL2.QINFUNC)

def is_seq(node):
    """
    Return True if the node is a with-seq statement,
    False otherwise.

    TODO: determine whetehr this is still used anywhere.
    It's probably dead.
    """

    return is_with_label(node, QGL2.QSEQ)
