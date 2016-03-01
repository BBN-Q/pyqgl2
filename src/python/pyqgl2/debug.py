# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved

import os
import traceback

"""
Convenience class for managing debugging messages

Each debugging message can have a level and/or a tag;
the user can control the level of debugging messages
printed, and what tags are active/inactive
"""

class DebugMsgState(object):
    """
    Encapsulates the state of the debug message module:
    the active tags, and the active level
    """

    ACTIVE_TAGS = None
    ACTIVE_LEVEL = 0

    def __init__():
        pass

def add_tag(tag, level):
    """
    Add a tag to the set of active tags

    The tag must be a non-empty string; an assertion will be
    raised on bogus input

    It is not an error to activate a tag that is already active

    Note that it doesn't have any effect to add a tag at level 0,
    since level 0 messages are always printed
    """

    assert isinstance(tag, str), 'tag must be a str'
    assert tag, 'tag must be a non-empty str'

    assert isinstance(level, int), 'level must be an int'
    assert level >= 0, 'level must be >= 0'

    if not DebugMsgState.ACTIVE_TAGS:
        DebugMsgState.ACTIVE_TAGS = dict()

    DebugMsgState.ACTIVE_TAGS[tag] = level

def set_level(level):
    """
    Set the debugging level to the given level

    The level must be an integer greater than or equal to zero

    Everything at level 0 is printed, but higher levels may
    be filtered.  There is no fixed assignment to the levels.
    A common convention is to have a small number of levels
    (i.e. 0..3) with decreasing levels of verbosity.
    """

    assert isinstance(level, int), 'level must be an int'
    assert level >= 0, 'level must be >= 0'

    old_level = DebugMsgState.ACTIVE_LEVEL
    DebugMsgState.ACTIVE_LEVEL = level

    return old_level

def debug_msg(msg, level=0, tag=None):
    """
    Print a debug msg, labeled with the filename, line number, and
    function name that invoked debug_msg

    Debug messages can be suppressed so that only messages that
    match one of a set of tags, or that at a level greater than or
    equal to a global threshold, are printed.

    TODO: tags and levels are not supported yet; all messages are
    printed
    """

    # If there's a level for this tag, then use it as the
    # active level; otherwise, use the general active level
    #
    if (tag and DebugMsgState.ACTIVE_TAGS and
            tag in DebugMsgState.ACTIVE_TAGS):
        active_level = DebugMsgState.ACTIVE_TAGS[tag]
    else:
        active_level = DebugMsgState.ACTIVE_LEVEL

    # if the active level is higher than the given level,
    # then drop the message
    #
    if level > active_level:
        return

    (filename, lineno, funcname, code) = traceback.extract_stack(limit=2)[0]

    text = ('DEBUG-%d: %s:%d (%s) %s' %
            (level, os.path.relpath(filename), lineno, funcname, msg))

    print('%s' % text)

