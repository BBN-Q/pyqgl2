# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved

"""
Convenience classes that simplify creating useful warning/error
messages when using the standard Python ast module to examine,
transform, or create a Python parse tree
"""

import ast
import sys

from copy import deepcopy

from pyqgl2.pysourcegen import dump_python_source

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

    # The maximum error level observed so far
    #
    MAX_ERR_LEVEL = NODE_ERROR_NONE

    # The minumum error level to display on the screen
    #
    MUTE_ERR_LEVEL = NODE_ERROR_WARNING

    LAST_DIAG_MSG = ''
    LAST_WARNING_MSG = ''
    LAST_ERROR_MSG = ''
    LAST_FATAL_MSG = ''

    ALL_PRINTED = set()

    def __init__(self):
        NodeError.MAX_ERR_LEVEL = NodeError.NODE_ERROR_NONE
        NodeError.MUTE_ERR_LEVEL = NodeError.NODE_ERROR_ERROR

    @staticmethod
    def reset():
        NodeError.LAST_DIAG_MSG = ''
        NodeError.LAST_WARNING_MSG = ''
        NodeError.LAST_ERROR_MSG = ''
        NodeError.LAST_FATAL_MSG = ''
        NodeError.ALL_PRINTED = set()

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

        NodeError.LAST_DIAG_MSG = msg
        NodeError._make_msg(node, NodeError.NODE_ERROR_NONE, msg)

    @staticmethod
    def warning_msg(node, msg=None):
        """
        Print a warning message associated with the given node
        """

        NodeError.LAST_WARNING_MSG = msg
        NodeError._make_msg(node, NodeError.NODE_ERROR_WARNING, msg)

    @staticmethod
    def error_msg(node, msg=None):
        """
        Print an error message associated with the given node
        """

        NodeError.LAST_ERROR_MSG = msg
        NodeError._make_msg(node, NodeError.NODE_ERROR_ERROR, msg)

    @staticmethod
    def fatal_msg(node, msg=None):
        """
        Print an fatal error message associated with the given node
        """

        NodeError.LAST_FATAL_MSG = msg
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
            if hasattr(node, 'qgl_fname'):
                qgl_fname = node.qgl_fname
            else:
                qgl_fname = '<unknown>'

            text = ('%s:%d:%d: ' %
                    (qgl_fname, node.lineno, node.col_offset))
        else:
            text = ''

        text += ('%s: %s' % (level_str, msg))

        # Only print messages that are at level MUTE_ERR_LEVEL
        # or higher
        #
        if level >= NodeError.MUTE_ERR_LEVEL:
            # Keep track of what we've printed, so we don't
            # print it over and over again (for repeated
            # substitions, inlining, or loop unrolling)
            #
            if text not in NodeError.ALL_PRINTED:
                print('%s' % text)
                NodeError.ALL_PRINTED.add(text)

        # If we've encountered a fatal error, then there's no
        # point in continuing (even if we haven't printed the
        # error message): exit immediately.
        #
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

def copy_all_loc(new_node, old_node, recurse=False):
    """
    Like ast.copy_location, but also copies other fields added
    by pyqgl2, if present

    If recurse is not False, then recursively copy the location
    from old_node to each node within new_node

    Currently the only new pyqgl2 field is qgl_fname, but
    there will probably be others
    """

    assert isinstance(new_node, ast.AST)
    assert isinstance(old_node, ast.AST)

    if not recurse:
        ast.copy_location(new_node, old_node)

        if hasattr(old_node, 'qgl_fname'):
            new_node.qgl_fname = old_node.qgl_fname
    else:
        for subnode in ast.walk(new_node):
            ast.copy_location(subnode, old_node)

            if hasattr(old_node, 'qgl_fname'):
                subnode.qgl_fname = old_node.qgl_fname

    return new_node

