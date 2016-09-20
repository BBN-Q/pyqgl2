'''
Utilities for creating a basic channel configuration for testing.
'''
from math import pi

from pyqgl2.main import mapQubitsToSequences
from pyqgl2.evenblocks import replaceBarriers
from QGL import *

def channel_setup():
    # TODO have this stash the current channel library, and unconditionally
    # create the test configuration
    if len(ChannelLibrary.channelLib.keys()) == 0:
        create_channel_library()
        ChannelLibrary.channelLib.write_to_file()

# Create a basic channel library
# Code stolen from QGL's test_Sequences
# It creates channels that are taken from test_Sequences APS2Helper
def create_channel_library(channels=dict()):
    from QGL.Channels import LogicalMarkerChannel, PhysicalQuadratureChannel, PhysicalMarkerChannel
    qubit_names = ['q1','q2']
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

    # Now assign physical channels
    for name in ['APS1', 'APS2', 'APS3', 'APS4', 'APS5', 'APS6']:
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
                'cr'            : 'APS5-12',
                'cr-gate'       : 'APS5-12m1',
                'M-q1q2'        : 'APS6-12',
                'M-q1q2-gate'   : 'APS6-12m1'}

    finalize_map(mapping, channels)
    return channels

# Store the given channels in the QGL ChannelLibrary
def finalize_map(mapping, channels):
    for name,value in mapping.items():
        channels[name].physChan = channels[value]

    # ChannelLibrary.channelLib = ChannelLibrary.ChannelLibrary()
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

def testable_sequence(seqs):
    '''
    Transform a QGL2 result function output into something more easily testable,
    by replacing barriers and discarding zero length Id's.
    '''
    seqIdxToChannelMap, _ = mapQubitsToSequences(seqs)
    seqs = replaceBarriers(seqs, seqIdxToChannelMap)
    discard_zero_Ids(seqs)
    return seqs
