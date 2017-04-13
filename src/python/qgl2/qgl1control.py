# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# QGL1 Control instructions that either should never
# be used in real QGL1 programs, or don't work yet in QGL1 programs.

from QGL.ControlFlow import ControlInstruction

# For use within QGL2 only
# Marks a barrier at start or end of blocks
# that can be run concurrently (with concur blocks)
# Should be replaced by QGL2 with the proper length Id pulse,
# or a Sync then a Wait if the block is of indeterminate length.
class Barrier(ControlInstruction):
    # chanlist is a list of Channel instances
    def __init__(self, *chanlist):
        super(Barrier, self).__init__("BARRIER")
        # Consider adding a start/end marker,
        # to help line up barriers across sequences.
        self.chanlist = chanlist

    def __str__(self):
        base = "BARRIER({0})".format(self.chanlist)
        return base
