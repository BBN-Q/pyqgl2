# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# TODO this should be part of QGL, not in QGL2

from QGL.ChannelLibraries import EdgeFactory
from QGL.ControlFlow import Sync, Wait
from QGL.PulsePrimitives import flat_top_gaussian

def init_real(*args):
    return Wait(args)

def flat_top_gaussian_edge_impl(
        source, target, riseFall, length, amp, phase=0, label="flat_top_gaussian"):
    '''Retrieve the edge from source to target and do a flat_top_gaussian on it'''

    CRchan = EdgeFactory(source, target)
    return flat_top_gaussian(CRchan, riseFall, length, amp, phase, label)
