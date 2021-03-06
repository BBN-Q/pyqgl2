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
        NODE_ERROR_NONE: 'diag',
        NODE_ERROR_WARNING: 'warning',
        NODE_ERROR_ERROR: 'error',
        NODE_ERROR_FATAL: 'fatal'
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

    # Keep track of all messages emitted, so that we don't
    # emit messages more than once (we might encounter the
    # same error during multiple passes through the source,
    # but we only want to inform the user once.
    #
    ALL_PRINTED = set()

    # Record most recent LAST_N messages created, even if they
    # are NOT printed (either because they've already been
    # printed, or because they are filtered by level, etc).
    #
    # Used by unit tests, where we want to check that the right
    # messages are created.  (if the test expects to create a
    # large number of messages, it can make LAST_N larger, but
    # the default is small in order to reduce overhead)
    #
    LAST_N = 8
    LAST_MSGS = list()

    def __init__(self):
        NodeError.MAX_ERR_LEVEL = NodeError.NODE_ERROR_NONE
        NodeError.MUTE_ERR_LEVEL = NodeError.NODE_ERROR_WARNING

    @staticmethod
    def reset():
        """
        Reset the state of created/emitted messages completely,
        returning to the initial state.

        Does not reset MUTE_ERR_LEVEL, or LAST_N.
        """

        NodeError.LAST_DIAG_MSG = ''
        NodeError.LAST_WARNING_MSG = ''
        NodeError.LAST_ERROR_MSG = ''
        NodeError.LAST_FATAL_MSG = ''
        NodeError.ALL_PRINTED = set()
        NodeError.LAST_MSGS = list()
        NodeError.MAX_ERR_LEVEL = NodeError.NODE_ERROR_NONE

    @staticmethod
    def error_detected():
        return NodeError.MAX_ERR_LEVEL >= NodeError.NODE_ERROR_ERROR

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

        if NodeError.error_detected():
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
    def _create_msg(node, level, msg=None):
        """
        Helper function that does all the real work of formatting
        the messages

        Does not add the message to the list of messages; may
        be used to create messages speculatively.
        """

        # Detect improper usage, and bomb out
        if node:
            assert isinstance(node, ast.AST), 'got %s' % str(type(node))

        assert level in NodeError.NODE_ERROR_LEGAL_LEVELS

        if not msg:
            msg = '?'

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

        return text

    @staticmethod
    def _emit_msg(level, text):
        """
        Emit a message: update the max error level seen,
        record the new text in the list of last N messages,
        then check to see whether it should be printed (according
        to its level), and if so then print it and add it to the
        set of all printed messages (which is used to ensure that
        duplicates of the message won't be printed)
        """

        if level > NodeError.MAX_ERR_LEVEL:
            NodeError.MAX_ERR_LEVEL = level

        # FIXME: slightly awkward: changes to LAST_N don't "take effect"
        # until a message is created
        #
        if NodeError.LAST_N <= 0:
            NodeError.LAST_MSGS = list()
        else:
            NodeError.LAST_MSGS.append(text)
            if len(NodeError.LAST_MSGS) > NodeError.LAST_N:
                NodeError.LAST_MSGS = NodeError.LAST_MSGS[-NodeError.LAST_N:]

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

    @staticmethod
    def _make_msg(node, level, msg=None):
        """
        Helper function that uses _create_msg and _emit_msg,
        and then  all the real work of creating
        the messages, updating the max error level observed, and
        exiting when a fatal error is encountered

        Does basic sanity checking on its inputs to make sure that
        the function is called correctly
        """

        # Detect improper usage, and bomb out
        if node:
            assert isinstance(node, ast.AST), 'got %s' % str(type(node))

        assert level in NodeError.NODE_ERROR_LEGAL_LEVELS

        text = NodeError._create_msg(node, level, msg=msg)

        NodeError._emit_msg(level, text)

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

    assert isinstance(new_node, ast.AST), 'got %s' % str(type(new_node))
    assert isinstance(old_node, ast.AST), 'got %s' % str(type(old_node))

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


def expr2ast(expr_text):
    """
    Parse the given text as a module, and then return the
    first element in the body of that module.

    This is shorthand for the idiom of parsing a single
    expression, but it doesn't check that the string is
    a single expression (it could be any number of
    valid statements)
    """

    return ast.parse(expr_text, mode='exec').body[0]


def value2ast(value):
    """
    Attempt to express the value AST.

    This is done by converting the value to its string
    representation using its repr, and then parsing
    that string to create AST.  Note that this is NOT
    generally possible, because

    a) there are many Python structures whose pretty-printed
        form fails to capture its full semantic

    b) parsed AST trees are acyclic

    c) many repr implementations are half-baked

    d) some comparisons (i.e. for floating point numbers) may
        lose precision during conversion

    This function detects when AST conversion causes
    and exception to be raised, but doesn't try harder
    than that.  It's up to the caller to apply the
    proper heuristics/tests for success.

    Returns an ast node if successful, None if not
    """

    try:
        candidate_str = repr(value)
        # print('GOT candidate_str [%s]' % candidate_str)
        candidate_ast = ast.parse(candidate_str, mode='eval')
        # print('GOT candidate_ast [%s]' % ast.dump(candidate_ast))
    except BaseException as exc:
        print('failure in value2ast_check: %s' % str(exc))
        return None

    # We want the actual body, not an Expression
    final_ast = candidate_ast.body

    return final_ast

def contains_type(node_or_list, ast_type):
    """
    Return True if the given node or any of its descendants is
    of the given ast_type, False otherwise

    For the sake of convenience, this function can also
    take a list of AST nodes instead of a single node.
    """

    if isinstance(node_or_list, list):
        return any(contains_type(node, ast_type)
                for node in node_or_list)

    for subnode in ast.walk(node_or_list):
        if isinstance(subnode, ast_type):
            return True

    return False
