# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved

import os
import traceback

"""
Convenience class for managing debugging messages

Each debugging message can have a level and/or a tag;
the user can control the level of debugging messages
printed, and what tags are active/inactive

The "active level" defines the default behavior for
tags that do not have a specific level assigned.
All messages that have a level less than or equal to
the active level will be printed, unless they have
a tag with a level that would indicate otherwise.
The default active level is 0, which means that only
messages at level 0 will be printed.  The active
level can be changed via set_level().

The "active tags" defines a mapping between tag names
and levels.  For example, if the tag 'foo' is bound
to level 2, then only messages with a level of 2 or
lower will be printed; all other messages with a tag
of 'foo' will be discarded.

To completely suppress all messages, the active
level (or the level on a tag) can be set to -1.

Examples:

    If 10 is your highest active level, and you want
    to turn off all but the most urgent messages
    (i.e. the level 0 messages), but still show all
    the messages tagged with 'foo':

        set_level(0)
        add_tag('foo', 10)

    If 10 is your highest active level, and you want
    to turn on all messages except those tagged as
    'foo' (except for those at level 0):

        set_level(10)
        add_tag('foo', 0)

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
    assert level >= -1, 'level must be >= -1'

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
    assert level >= -1, 'level must be >= -1'

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

    # level cannot be less than 0; set to 0 if lower.
    #
    if level < 0:
        level = 0

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

