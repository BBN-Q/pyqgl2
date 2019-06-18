# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.
'''
Utilities for creating a basic channel configuration for testing.
'''

from QGL.ChannelLibraries import EdgeFactory, MeasFactory, QubitFactory
from QGL import ChannelLibraries
from QGL.Channels import Edge, Measurement
from QGL.PulseSequencer import Pulse, CompositePulse
from QGL.PatternUtils import flatten
from QGL.PulsePrimitives import Id, X, MEAS
from QGL.ControlFlow import qsync, qwait, ControlInstruction, Goto, Barrier
from QGL.BlockLabel import BlockLabel

from pyqgl2.test_cl import create_default_channelLibrary

import collections
from math import pi

def channel_setup(new=True):
    # new indicates replace any existing library
    # Otherwise if there is an existing library, use it
    # FIXME: For now, supplying first arg false meaning do not create physical channel mappings
    if not new and ChannelLibraries.channelLib is not None and len(ChannelLibraries.channelLib.keys()) != 0:
        create_default_channelLibrary(False, False)
        # create_channel_library(ChannelLibraries.channelLib.channelDict)
    else:
        create_default_channelLibrary(False, True)
        # create_channel_library(new=True)

# # OBE: Create a basic channel library
# # Code stolen from QGL's test_Sequences
# # It creates channels that are taken from test_Sequences APS2Helper
# def create_channel_library(channels=dict(), new=False):
#     from QGL.Channels import LogicalMarkerChannel, PhysicalQuadratureChannel, PhysicalMarkerChannel

#     ChannelLibraries.ChannelLibrary(blank=True)

#     qubit_names = ['q1','q2','q3']
#     logical_names = ['digitizerTrig', 'slaveTrig']

#     for name in logical_names:
#         channels[name] = LogicalMarkerChannel(label=name)

#     for name in qubit_names:
#         mName = 'M-' + name
#         mgName = 'M-' + name + '-gate'
#         qgName = name + '-gate'

#         mg = LogicalMarkerChannel(label=mgName)
#         qg = LogicalMarkerChannel(label=qgName)

#         m = MeasFactory(label=mName, gate_chan = mg, trig_chan=channels['digitizerTrig'])

#         q = QubitFactory(label=name, gate_chan=qg)
#         q.pulse_params['length'] = 30e-9
#         q.pulse_params['phase'] = pi/2

#         channels[name] = q
#         channels[mName] = m
#         channels[mgName]  = mg
#         channels[qgName]  = qg

#     # this block depends on the existence of q1 and q2
#     channels['cr-gate'] = LogicalMarkerChannel(label='cr-gate')

#     q1, q2 = channels['q1'], channels['q2']
#     cr = None
#     try:
#         cr = EdgeFactory(q1, q2)
#     except:
#         cr = Edge(label="cr", source = q1, target = q2, gate_chan = channels['cr-gate'] )
#     cr.pulse_params['length'] = 30e-9
#     cr.pulse_params['phase'] = pi/4
#     channels["cr"] = cr

#     mq1q2g = LogicalMarkerChannel(label='M-q1q2-gate')
#     channels['M-q1q2-gate']  = mq1q2g
#     channels['M-q1q2']       = Measurement(label='M-q1q2', gate_chan = mq1q2g, trig_chan=channels['digitizerTrig'])

#     # Add a 2nd edge from q2 back to q1 to support edgeTest4 (which is weird)
#     channels['cr2-gate'] = LogicalMarkerChannel(label='cr2-gate')
#     cr2 = None
#     try:
#         cr2 = EdgeFactory(q2, q1)
#     except:
#         cr2 = Edge(label="cr2", source = q2, target = q1, gate_chan = channels['cr2-gate'] )
#     cr2.pulse_params['length'] = 30e-9
#     cr2.pulse_params['phase'] = pi/4
#     channels["cr2"] = cr2

#     mq2q1g = LogicalMarkerChannel(label='M-q2q1-gate')
#     channels['M-q2q1-gate']  = mq2q1g
#     channels['M-q2q1']       = Measurement(label='M-q2q1', gate_chan = mq2q1g, trig_chan=channels['digitizerTrig'])

#     # Now assign physical channels
#     for name in ['APS1', 'APS2', 'APS3', 'APS4', 'APS5', 'APS6',
#                  'APS7', 'APS8', 'APS9', 'APS10']:
#         channelName = name + '-12'
#         channel = PhysicalQuadratureChannel(label=channelName)
#         channel.sampling_rate = 1.2e9
#         channel.instrument = name
#         channel.translator = 'APS2Pattern'
#         channels[channelName] = channel

#         for m in range(1,5):
#             channelName = "{0}-12m{1}".format(name,m)
#             channel = PhysicalMarkerChannel(label=channelName)
#             channel.sampling_rate = 1.2e9
#             channel.instrument = name
#             channel.translator = 'APS2Pattern'
#             channels[channelName] = channel

#     mapping = {	'digitizerTrig' : 'APS1-12m1',
#                 'slaveTrig'     : 'APS1-12m2',
#                 'q1'            : 'APS1-12',
#                 'q1-gate'       : 'APS1-12m3',
#                 'M-q1'          : 'APS2-12',
#                 'M-q1-gate'     : 'APS2-12m1',
#                 'q2'            : 'APS3-12',
#                 'q2-gate'       : 'APS3-12m1',
#                 'M-q2'          : 'APS4-12',
#                 'M-q2-gate'     : 'APS4-12m1',
#                 'q3'            : 'APS7-12',
#                 'q3-gate'       : 'APS7-12m1',
#                 'M-q3'          : 'APS8-12',
#                 'M-q3-gate'     : 'APS8-12m1',
#                 'cr'            : 'APS5-12',
#                 'cr-gate'       : 'APS5-12m1',
#                 'M-q1q2'        : 'APS6-12',
#                 'M-q1q2-gate'   : 'APS6-12m1',
#                 'cr2'           : 'APS9-12',
#                 'cr2-gate'      : 'APS9-12m1',
#                 'M-q2q1'        : 'APS10-12',
#                 'M-q2q1-gate'   : 'APS10-12m1'}

#     finalize_map(mapping, channels, new)
#     return channels

# # OBE: Store the given channels in the QGL ChannelLibraries
# def finalize_map(mapping, channels, new=False):
#     for name,value in mapping.items():
#         channels[name].phys_chan = channels[value]

#     if new:
#         ChannelLibraries.channelLib = ChannelLibraries.ChannelLibrary(blank=True)
#     ChannelLibraries.channelLib.channelDict = channels
#     ChannelLibraries.channelLib.build_connectivity_graph()



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
def flattenSeqs(seq):
    hasList = False
    for el in seq:
        if isinstance(el, collections.Iterable) and not isinstance(el, (str, Pulse, CompositePulse)) :
            hasList = True
            break
    if hasList:
        newS = []
        for el in flatten(seq):
            newS.append(el)
        return newS
    else:
        return seq

def testable_sequence(seqs):
    '''
    Transform a QGL2 result function output into something more easily testable
    by flattening pulse lists.
    '''
    seqs = flattenSeqs(seqs)
    return seqs

# Adapted from unittest.case.py: assertSequenceEqual
# Except use difflib.unified_diff instead of ndiff - much faster (less detail)
def assertPulseSequenceEqual(test, seq1, seq2, msg=None):
    """An equality assertion for ordered sequences of pulses.

    For the purposes of this function, a valid ordered sequence type is one
    which can be indexed, has a length, and has an equality operator.

    Args:
    seq1: The first sequence to compare.
    seq2: The second sequence to compare.
    msg: Optional message to use on failure instead of a list of
                    differences.
    """
    import difflib
    import pprint
    from unittest.util import safe_repr, _common_shorten_repr
    seq_type = list
    if seq_type is not None:
        seq_type_name = seq_type.__name__
        if not isinstance(seq1, seq_type):
            raise test.failureException('First sequence is not a %s: %s'
                                        % (seq_type_name, safe_repr(seq1)))
        if not isinstance(seq2, seq_type):
            raise test.failureException('Second sequence is not a %s: %s'
                                        % (seq_type_name, safe_repr(seq2)))
    else:
        seq_type_name = "sequence"

    differing = None
    try:
        len1 = len(seq1)
    except (TypeError, NotImplementedError):
        differing = 'First %s has no length.    Non-sequence?' % (
            seq_type_name)

    if differing is None:
        try:
            len2 = len(seq2)
        except (TypeError, NotImplementedError):
            differing = 'Second %s has no length.    Non-sequence?' % (
                seq_type_name)

    if differing is None:
        if seq1 == seq2:
            return

        differing = '%ss differ: %s != %s\n' % (
            (seq_type_name.capitalize(),) +
            _common_shorten_repr(seq1, seq2))

        for i in range(min(len1, len2)):
            try:
                item1 = seq1[i]
            except (TypeError, IndexError, NotImplementedError):
                differing += ('\nUnable to index element %d of first %s\n' %
                              (i, seq_type_name))
                break

            try:
                item2 = seq2[i]
            except (TypeError, IndexError, NotImplementedError):
                differing += ('\nUnable to index element %d of second %s\n' %
                                 (i, seq_type_name))
                break

            if item1 != item2:
                differing += ('\nFirst differing element %d:\n%s\n%s\n' %
                                 (i, str(item1), str(item2)))
                break
        else:
            if (len1 == len2 and seq_type is None and
                type(seq1) != type(seq2)):
                # The sequences are the same, but have differing types.
                return


        if len1 > len2:
            differing += ('\nFirst %s contains %d additional '
                          'elements.\n' % (seq_type_name, len1 - len2))
            try:
                differing += ('First extra element %d:\n%s\n' %
                              (len2, seq1[len2]))
            except (TypeError, IndexError, NotImplementedError):
                differing += ('Unable to index element %d '
                                  'of first %s\n' % (len2, seq_type_name))
        elif len1 < len2:
            differing += ('\nSecond %s contains %d additional '
                          'elements.\n' % (seq_type_name, len2 - len1))
            try:
                differing += ('First extra element %d:\n%s\n' %
                              (len1, seq2[len1]))
            except (TypeError, IndexError, NotImplementedError):
                differing += ('Unable to index element %d '
                                  'of second %s\n' % (len1, seq_type_name))
    standardMsg = differing
    diffMsg = '\n' + '\n'.join(
#            difflib.ndiff(pprint.pformat(seq1).splitlines(),
# FIXME: I wish I could get pprint.pformat to use str on pulses not repr
        difflib.unified_diff(pprint.pformat(seq1).splitlines(),
                             pprint.pformat(seq2).splitlines()))

    standardMsg = test._truncateMessage(standardMsg, diffMsg)
    msg = test._formatMessage(msg, standardMsg)
    test.fail(msg)

def get_cal_seqs_1qubit(qubit, calRepeats=2):
    '''
    Note: return may include 0 length Id pulses.
    EG:
    qwait
    Id(q1)
    MEAS(q1),
    qwait
    Id(q1)
    MEAS(q1),
    qwait
    X(q1)
    MEAS(q1),
    qwait
    X(q1)
    MEAS(q1)
    '''
    calSeq = []
    for pulse in [Id, X]:
        for _ in range(calRepeats):
            calSeq += [
                qwait(channels=(qubit,)),
                pulse(qubit),
                Barrier(qubit),
                MEAS(qubit)
            ]
    return calSeq

def get_cal_seqs_2qubits(q1, q2, calRepeats=2):
    '''
    Prepare all computational 2-qubit basis states and measure them.
    '''

    calseq = []
    for pulseSet in [(Id, Id), (Id, X), (X, Id), (X, X)]:
        for _ in range(calRepeats):
            calseq += [
                qwait(channels=(q1, q2)),
                pulseSet[0](q1),
                pulseSet[1](q2),
                Barrier(q1, q2),
                MEAS(q1),
                MEAS(q2)
            ]

    return calseq

def match_labels(seq1, seq2):
    '''
    Returns a copy of seq1 which replaces BlockLabels in seq1 with
    corresponding BlockLabels in seq2
    '''
    new_seq = []
    label_map = {}
    for s1, s2 in zip(seq1, seq2):
        if (isinstance(s1, BlockLabel) and isinstance(s2, BlockLabel)):
            new_seq.append(s2)
            label_map[s1] = s2
        else:
            new_seq.append(s1)

    for entry in new_seq:
        if isinstance(entry, Goto) and entry.target:
            entry.target = label_map[entry.target]
    return new_seq
