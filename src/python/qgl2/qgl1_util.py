# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# TODO this should be part of QGL, not in QGL2

from QGL.ChannelLibrary import EdgeFactory
from QGL.ControlFlow import Sync, Wait
from QGL.PulsePrimitives import flat_top_gaussian

def init_real(q):
    return Wait()

def flat_top_gaussian_edge_impl(
        source, target, riseFall, length, amp, phase=0):

    CRchan = EdgeFactory(source, target)
    return flat_top_gaussian(CRchan, riseFall, length, amp, phase=0)
