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
All messages that have a level higher than or equal to
the active level will be printed, unless they have
a tag with a level that would indicate otherwise.
The levels are given mnemonic names with the
following values:

    NONE = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1
    ALL = 0

NONE is a reserved value.

Messages can be assigned any level ALL..HIGH.
Messages with higher values that HIGH will be
silently rounded down to HIGH, and messages with
lower values than ALL will have their levels
silently rounded up to ALL.

The default active level is NONE, which means
that no messages will be printed.  The active
level can be changed via set_level().

The "active tags" defines a mapping between tag names
and levels.  For example, if the tag 'foo' is bound
to level MEDIUM, then for messages with a tag of
'foo' only messages with a level of MEDIUM or higher
will be printed.  (other messages will be filtered
according to the global active level)

To completely suppress all messages, the active
level (or the level on a tag) can be set to NONE.

Examples:

    To discard all messages except for those with
    the tag 'foo', and to print all messages
    with tag 'foo':

        set_level(NONE)
        add_tag('foo', ALL)

    To print all messages, except those with tag
    'foo', which should all be discarded:

        set_level(ALL)
        add_tag('foo', NONE)

"""

class DebugMsg(object):
    """
    Encapsulates the state of the debug message module:
    the active tags, and the active level
    """

    NONE = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1
    ALL = 0

    ACTIVE_TAGS = dict()
    ACTIVE_LEVEL = NONE

    @staticmethod
    def reset():
        DebugMsg.ACTIVE_TAGS = dict()
        DebugMsg.ACTIVE_LEVEL = DebugMsg.NONE

    @staticmethod
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

        # truncate the level, if necessary
        #
        if level < DebugMsg.ALL:
            level = DebugMsg.ALL
        elif level > DebugMsg.HIGH:
            level = DebugMsg.HIGH

        assert level >= -1, 'level must be >= -1'

        DebugMsg.ACTIVE_TAGS[tag] = level

    @staticmethod
    def set_level(level):
        """
        Set the debugging level to the given level

        The level must be an integer greater than or equal to zero
        """

        assert isinstance(level, int), 'level must be an int'

        old_level = DebugMsg.ACTIVE_LEVEL

        # truncate the level, if necessary
        #
        if level < DebugMsg.ALL:
            level = DebugMsg.ALL
        elif level > DebugMsg.NONE:
            level = DebugMsg.NONE

        DebugMsg.ACTIVE_LEVEL = level

        return old_level

    @staticmethod
    def log(msg, level=ALL, tag=None):
        """
        Print a debug msg, labeled with the filename, line number, and
        function name that invoked debug_msg

        Debug messages can be suppressed so that only messages that
        match one of a set of tags, or that at a level greater than or
        equal to a global threshold, are printed.
        """

        # truncate the level, if necessary
        #
        if level < DebugMsg.ALL:
            level = DebugMsg.ALL
        elif level > DebugMsg.HIGH:
            level = DebugMsg.HIGH

        # If there's a level for this tag, then use it as the
        # active level; otherwise, use the general active level
        #
        if tag and (tag in DebugMsg.ACTIVE_TAGS):
            active_level = DebugMsg.ACTIVE_TAGS[tag]
        else:
            active_level = DebugMsg.ACTIVE_LEVEL

        # if the active level is higher than the given level,
        # then drop the message
        #
        if level < active_level:
            return

        (fname, lineno, funcname, code) = traceback.extract_stack(limit=2)[0]

        text = ('DEBUG-%d: %s:%d (%s) %s' %
                (level, os.path.relpath(fname), lineno, funcname, msg))

        print('%s' % text)

