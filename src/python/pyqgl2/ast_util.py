# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved

"""
Convenience classes that simplify creating useful warning/error
messages when using the standard Python ast module to examine,
transform, or create a Python parse tree
"""

import ast
import meta
import sys

from copy import deepcopy

from pyqgl2.pysourcegen import python_source, dump_python_source

class NodeError(object):
    """
    A mix-in to make it simplify the generation of
    consistent, meaningful error and warning messages
    within the ast.NodeTransformer and ast.NodeVisitor
    classes

    Assumes that the node parameter to its methods is
    an instance of an ast.AST, and has been annotated
    with the name of the source file (as node.qgl_fname)

    The methods are implemented with module methods (below)
    so that they don't need to be called from a
    Visitor/Transformer.
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

    MAX_ERR_LEVEL = NODE_ERROR_NONE

    LAST_DIAG_MSG = ''
    LAST_WARNING_MSG = ''
    LAST_ERROR_MSG = ''
    LAST_FATAL_MSG = ''

    ALL_PRINTED = set()

    def __init__(self):
        NodeError.MAX_ERR_LEVEL = NodeError.NODE_ERROR_NONE

    @staticmethod
    def reset():
        LAST_DIAG_MSG = ''
        LAST_WARNING_MSG = ''
        LAST_ERROR_MSG = ''
        LAST_FATAL_MSG = ''
        ALL_PRINTED = set()

    @staticmethod
    def halt_on_error():
        """
        The ordinary use of NodeError is to continue on after encountering
        an error (in the hope of getting useful additional diagnostics).
        
        At certain points in the program, however, it makes little sense
        to continue if there has been an error in an earlier part of
        the program.  Use halt_on_error() to detect this condition and
        halt.
        """

        if NodeError.MAX_ERR_LEVEL >= NodeError.NODE_ERROR_ERROR:
            sys.exit(1)

    @staticmethod
    def diag_msg(node, msg=None):
        """
        Print a diagnostic message associated with the given node
        """

        LAST_DIAG_MSG = msg
        NodeError._make_msg(node, NodeError.NODE_ERROR_NONE, msg)

    @staticmethod
    def warning_msg(node, msg=None):
        """
        Print a warning message associated with the given node
        """

        LAST_WARNING_MSG = msg
        NodeError._make_msg(node, NodeError.NODE_ERROR_WARNING, msg)

    @staticmethod
    def error_msg(node, msg=None):
        """
        Print an error message associated with the given node
        """

        LAST_ERROR_MSG = msg
        NodeError._make_msg(node, NodeError.NODE_ERROR_ERROR, msg)

    @staticmethod
    def fatal_msg(node, msg=None):
        """
        Print an fatal error message associated with the given node
        """

        LAST_FATAL_MSG = msg
        NodeError._make_msg(node, NodeError.NODE_ERROR_FATAL, msg)

    @staticmethod
    def _make_msg(node, level, msg=None):
        """
        Helper function that does all the real work of formatting
        the messages, updating the max error level observed, and
        exiting when a fatal error is encountered

        Does basic sanity checking on its inputs to make sure that
        the function is called correctly
        """

        # Detect improper usage, and bomb out
        if node:
            assert isinstance(node, ast.AST)

        assert level in NodeError.NODE_ERROR_LEGAL_LEVELS

        if not msg:
            msg = '?'

        if level > NodeError.MAX_ERR_LEVEL:
            NodeError.MAX_ERR_LEVEL = level

        if level in NodeError.NODE_ERROR_LEGAL_LEVELS:
            level_str = NodeError.NODE_ERROR_LEGAL_LEVELS[level]
        else:
            level_str = 'weird'

        if node:
            text = ('%s:%d:%d: ' %
                    (node.qgl_fname, node.lineno, node.col_offset))
        else:
            text = ''

        text += ('%s: %s' % (level_str, msg))

        # Keep track of what we've printed, so we don't
        # print it over and over again (for repeated
        # substitions, inlining, or loop unrolling)
        #
        if text not in NodeError.ALL_PRINTED:
            print('%s' % text)
            NodeError.ALL_PRINTED.add(text)

        # If we've encountered a fatal error, then there's no
        # point in continuing: exit immediately.
        if NodeError.MAX_ERR_LEVEL == NodeError.NODE_ERROR_FATAL:
            sys.exit(1)


# See NodeError above for more description.  These methods
# are deprecated in favor of the NodeError interface, but
# remain for backward compatibility.

def diag_msg(node, msg=None):
    """
    Print a diagnostic message associated with the given node
    """
    NodeError.diag_msg(node, msg)

def warning_msg(node, msg=None):
    """
    Print a warning message associated with the given node
    """
    NodeError.warning_msg(node, msg)

def error_msg(node, msg=None):
    """
    Print an error message associated with the given node
    """
    NodeError.error_msg(node, msg)

def fatal_msg(node, msg=None):
    """
    Print an fatal error message associated with the given node
    """
    NodeError.fatal_msg(node, msg)


class NodeTransformerWithFname(ast.NodeTransformer, NodeError):
    """
    ast.NodeTransformer with NodeError mixed in
    """

    def __init__(self):
        super(NodeTransformerWithFname, self).__init__()


class NodeVisitorWithFname(ast.NodeVisitor, NodeError):
    """
    ast.NodeVisitor with NodeError mixed in
    """

    def __init__(self):
        super(NodeVisitorWithFname, self).__init__()

def copy_node(node):
    """
    Make a copy of the given ast node and its descendants
    so that the copy can be manipulated without altering
    the original

    Hopefully deepcopy() is sufficient
    """

    return deepcopy(node)

def ast2str(ptree):
    """
    Given an AST parse tree, return the equivalent code
    (as a string)
    """

    return dump_python_source(ptree)
