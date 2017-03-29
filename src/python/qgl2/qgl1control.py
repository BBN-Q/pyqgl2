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
    # ctr is an opaque string, unique per channel
    # (but appearing once for the program for each channel
    # in chanlist)
    def __init__(self, ctr, chanlist):
        super(Barrier, self).__init__("BARRIER", value=ctr)
        # Consider adding a start/end marker,
        # to help line up barriers across sequences.
        self.chanlist = chanlist

    def __str__(self):
        base = super(Barrier, self).__str__()
        base += " on Channels: %s" % str(self.chanlist)
        return base
