'''
Utilities for creating a basic channel configuration for testing.
'''

from pyqgl2.main import mapQubitsToSequences
from pyqgl2.evenblocks import replaceBarriers

from QGL.ChannelLibrary import EdgeFactory, MeasFactory, QubitFactory
from QGL import ChannelLibrary
from QGL.Channels import Edge, Measurement
from QGL.PulseSequencer import Pulse, CompositePulse
from QGL.PatternUtils import flatten

import collections
from math import pi

def channel_setup():
    # TODO have this stash the current channel library, and unconditionally
    # create the test configuration
    if len(ChannelLibrary.channelLib.keys()) == 0:
        create_channel_library()
        ChannelLibrary.channelLib.write_to_file()
    else:
        create_channel_library(new=True)

# Create a basic channel library
# Code stolen from QGL's test_Sequences
# It creates channels that are taken from test_Sequences APS2Helper
def create_channel_library(channels=dict(), new=False):
    from QGL.Channels import LogicalMarkerChannel, PhysicalQuadratureChannel, PhysicalMarkerChannel
    qubit_names = ['q1','q2','q3']
    logical_names = ['digitizerTrig', 'slaveTrig']

    for name in logical_names:
        channels[name] = LogicalMarkerChannel(label=name)

    for name in qubit_names:
        mName = 'M-' + name
        mgName = 'M-' + name + '-gate'
        qgName = name + '-gate'

        mg = LogicalMarkerChannel(label=mgName)
        qg = LogicalMarkerChannel(label=qgName)

        m = MeasFactory(label=mName, gateChan = mg, trigChan=channels['digitizerTrig'])

        q = QubitFactory(label=name, gateChan=qg)
        q.pulseParams['length'] = 30e-9
        q.pulseParams['phase'] = pi/2

        channels[name] = q
        channels[mName] = m
        channels[mgName]  = mg
        channels[qgName]  = qg

    # this block depends on the existence of q1 and q2
    channels['cr-gate'] = LogicalMarkerChannel(label='cr-gate')

    q1, q2 = channels['q1'], channels['q2']
    cr = None
    try:
        cr = EdgeFactory(q1, q2)
    except:
        cr = Edge(label="cr", source = q1, target = q2, gateChan = channels['cr-gate'] )
    cr.pulseParams['length'] = 30e-9
    cr.pulseParams['phase'] = pi/4
    channels["cr"] = cr

    mq1q2g = LogicalMarkerChannel(label='M-q1q2-gate')
    channels['M-q1q2-gate']  = mq1q2g
    channels['M-q1q2']       = Measurement(label='M-q1q2', gateChan = mq1q2g, trigChan=channels['digitizerTrig'])

    # Add a 2nd edge from q2 back to q1 to support edgeTest4 (which is weird)
    channels['cr2-gate'] = LogicalMarkerChannel(label='cr2-gate')
    cr2 = None
    try:
        cr2 = EdgeFactory(q2, q1)
    except:
        cr2 = Edge(label="cr2", source = q2, target = q1, gateChan = channels['cr2-gate'] )
    cr2.pulseParams['length'] = 30e-9
    cr2.pulseParams['phase'] = pi/4
    channels["cr2"] = cr2

    mq2q1g = LogicalMarkerChannel(label='M-q2q1-gate')
    channels['M-q2q1-gate']  = mq2q1g
    channels['M-q2q1']       = Measurement(label='M-q2q1', gateChan = mq2q1g, trigChan=channels['digitizerTrig'])

    # Now assign physical channels
    for name in ['APS1', 'APS2', 'APS3', 'APS4', 'APS5', 'APS6',
                 'APS7', 'APS8', 'APS9', 'APS10']:
        channelName = name + '-12'
        channel = PhysicalQuadratureChannel(label=channelName)
        channel.samplingRate = 1.2e9
        channel.AWG = name
        channel.translator = 'APS2Pattern'
        channels[channelName] = channel

        for m in range(1,5):
            channelName = "{0}-12m{1}".format(name,m)
            channel = PhysicalMarkerChannel(label=channelName)
            channel.samplingRate = 1.2e9
            channel.AWG = name
            channel.translator = 'APS2Pattern'
            channels[channelName] = channel

    mapping = {	'digitizerTrig' : 'APS1-12m1',
                'slaveTrig'     : 'APS1-12m2',
                'q1'            : 'APS1-12',
                'q1-gate'       : 'APS1-12m3',
                'M-q1'          : 'APS2-12',
                'M-q1-gate'     : 'APS2-12m1',
                'q2'            : 'APS3-12',
                'q2-gate'       : 'APS3-12m1',
                'M-q2'          : 'APS4-12',
                'M-q2-gate'     : 'APS4-12m1',
                'q3'            : 'APS7-12',
                'q3-gate'       : 'APS7-12m1',
                'M-q3'          : 'APS8-12',
                'M-q3-gate'     : 'APS8-12m1',
                'cr'            : 'APS5-12',
                'cr-gate'       : 'APS5-12m1',
                'M-q1q2'        : 'APS6-12',
                'M-q1q2-gate'   : 'APS6-12m1',
                'cr2'           : 'APS9-12',
                'cr2-gate'      : 'APS9-12m1',
                'M-q2q1'        : 'APS10-12',
                'M-q2q1-gate'   : 'APS10-12m1'}

    finalize_map(mapping, channels, new)
    return channels

# Store the given channels in the QGL ChannelLibrary
def finalize_map(mapping, channels, new=False):
    for name,value in mapping.items():
        channels[name].physChan = channels[value]

    if new:
        ChannelLibrary.channelLib = ChannelLibrary.ChannelLibrary()
    ChannelLibrary.channelLib.channelDict = channels
    ChannelLibrary.channelLib.build_connectivity_graph()

def discard_zero_Ids(seqs):
    # assume seqs has a structure like [[entry0, entry1, ..., entryN]]
    for seq in seqs:
        ct = 0
        while ct < len(seq):
            entry = seq[ct]
            if isinstance(entry, Pulse) and entry.label == "Id" and entry.length == 0:
                del seq[ct]
            else:
                ct += 1

# Things like echoCR create lists of pulses that need to be flattened
# before calling compile_to_hardware
def flattenSeqs(seqs):
    nseqs = []
    for seq in seqs:
        hasList = False
        for el in seq:
            if isinstance(el, collections.Iterable) and not isinstance(el, (str, Pulse, CompositePulse)) :
                hasList = True
                break
        if hasList:
            newS = []
            for el in flatten(seq):
                newS.append(el)
            nseqs.append(newS)
        else:
            nseqs.append(seq)
    return nseqs

def testable_sequence(seqs):
    '''
    Transform a QGL2 result function output into something more easily testable,
    by replacing barriers and discarding zero length Id's and
    flattening pulse lists.
    '''
    seqIdxToChannelMap, _ = mapQubitsToSequences(seqs)
    seqs = replaceBarriers(seqs, seqIdxToChannelMap)
    discard_zero_Ids(seqs)
    seqs = flattenSeqs(seqs)
    return seqs
