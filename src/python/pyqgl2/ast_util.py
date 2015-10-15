# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved

"""
Convenience classes that simplify creating useful warning/error
messages when using the standard Python ast module to examine,
transform, or create a Python parse tree
"""

import ast
import sys

from copy import deepcopy

class NodeError(object):
    """
    A mix-in to make it simplify the generation of
    consistent, meaningful error and warning messages
    within the ast.NodeTransformer and ast.NodeVisitor
    classes

    Assumes that the node parameter to its methods is
    an instance of an ast.AST.
    """

    NODE_ERROR_NONE = 0
    NODE_ERROR_WARNING = 1
    NODE_ERROR_ERROR = 2
    NODE_ERROR_FATAL = 3

    NODE_ERROR_LEGAL_LEVELS = {
        NODE_ERROR_NONE : 'diag',
        NODE_ERROR_WARNING : 'warning',
        NODE_ERROR_ERROR : 'error',
        NODE_ERROR_FATAL : 'fatal'
    }

    def __init__(self, fname):
        self.fname = fname
        self.max_err_level = self.NODE_ERROR_NONE

    def diag_msg(self, node, msg=None):
        """
        Print a diagnostic message associated with the given node
        """

        self._make_msg(node, self.NODE_ERROR_NONE, msg)

    def warning_msg(self, node, msg=None):
        """
        Print a warning message associated with the given node
        """

        self._make_msg(node, self.NODE_ERROR_WARNING, msg)

    def error_msg(self, node, msg=None):
        """
        Print an error message associated with the given node
        """

        self._make_msg(node, self.NODE_ERROR_ERROR, msg)

    def fatal_msg(self, node, msg=None):
        """
        Print an fatal error message associated with the given node
        """

        self._make_msg(node, self.NODE_ERROR_FATAL, msg)

    def _make_msg(self, node, level, msg=None):
        """
        Helper function that does all the real work of formatting
        the messages, updating the max error level observed, and
        exiting when a fatal error is encountered

        Does basic sanity checking on its inputs to make sure that
        the function is called correctly
        """

        # Detect improper usage, and bomb out
        assert isinstance(node, ast.AST)
        assert level in self.NODE_ERROR_LEGAL_LEVELS

        if not msg:
            msg = '?'

        if level > self.max_err_level:
            self.max_err_level = level

        if level in self.NODE_ERROR_LEGAL_LEVELS:
            level_str = self.NODE_ERROR_LEGAL_LEVELS[level]
        else:
            level_str = 'weird'

        print ('%s:%d:%d: %s: %s' % (
            self.fname, node.lineno, node.col_offset, level_str, msg))

        # If we've encountered a fatal error, then there's no
        # point in continuing: exit immediately.
        if self.max_err_level == self.NODE_ERROR_FATAL:
            sys.exit(1)


class NodeTransformerWithFname(ast.NodeTransformer, NodeError):
    """
    ast.NodeTransformer with NodeError mixed in
    """

    def __init__(self, fname):
        super(NodeTransformerWithFname, self).__init__(fname)


class NodeVisitorWithFname(ast.NodeVisitor, NodeError):
    """
    ast.NodeVisitor with NodeError mixed in
    """

    def __init__(self, fname):
        super(NodeVisitorWithFname, self).__init__(fname)

def copy_node(node):
    """
    Make a copy of the given ast node and its descendants
    so that the copy can be manipulated without altering
    the original

    Hopefully deepcopy() is sufficient
    """

    return deepcopy(node)

