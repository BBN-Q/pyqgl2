#!/usr/bin/env python3
#
# Copyright 2019 by Raytheon BBN Technologies Corp.  All Rights Reserved.
"""
Create a test ChannelLibrary. 3 qubits, with a bidirectional edge between q1 and q2.
If we're assigning to HW (default not), do something APS2ish spreading across APS1-10.
Stores in an in-memory ChannelLibrary.
"""

def set_awg_dir():
    """If there is no AWGDir set, create a temp dir for it,
    and ensure the AWGDir exists
    """
    import QGL
    import os
    if QGL.config.AWGDir is None:
        QGL.config.load_config()

    if QGL.config.AWGDir is None:
        QGL.config.AWGDir = tempfile.TemporaryDirectory()
        logger.warning("Creating temporary AWG dir at {QGL.config.AWGDir}")

    if not os.path.isdir(QGL.config.AWGDir):
        os.makedirs(QGL.config.AWGDir)

def assign_to_hw(channels):
    """Assign the channels to physical channels, returning modified channels.
    Use APS1-10. (1 for q1, digitizer, slave; 2 for M-q1, 3=q2, 4=M-q2, 5=cr,...."""
    from QGL.Channels import PhysicalQuadratureChannel, PhysicalMarkerChannel
    for name in ['APS1', 'APS2', 'APS3', 'APS4', 'APS5', 'APS6',
                 'APS7', 'APS8', 'APS9', 'APS10']:
        channelName = name + '-1'
        channel = PhysicalQuadratureChannel(label=channelName, channel=0)
        channel.sampling_rate = 1.2e9
        channel.instrument = name
        channel.translator = 'APS2Pattern'
        channels[channelName] = channel

        for m in range(1, 5):
            channelName = "{0}-m{1}".format(name, m)
            channel = PhysicalMarkerChannel(label=channelName, channel=m-1)
            channel.sampling_rate = 1.2e9
            channel.instrument = name
            channel.translator = 'APS2Pattern'
            channels[channelName] = channel
            # FIXME: Needs a sequence_file and channel somehow?

    mapping = {'digitizerTrig': 'APS1-m1',
               'slave_trig': 'APS1-m2',
               'q1': 'APS1-1',
               'q1-gate': 'APS1-m3',
               'M-q1': 'APS2-1',
               'M-q1-gate': 'APS2-m1',
               'q2': 'APS3-1',
               'q2-gate': 'APS3-m1',
               'M-q2': 'APS4-1',
               'M-q2-gate': 'APS4-m1',
               'cr': 'APS5-1',
               'cr-gate': 'APS5-m1',
               'M-q1q2': 'APS6-1',
               'M-q1q2-gate': 'APS6-m1',
               'q3'            : 'APS7-1',
               'q3-gate'       : 'APS7-m1',
               'M-q3'          : 'APS8-1',
               'M-q3-gate'     : 'APS8-m1',
               'cr2'           : 'APS9-1',
               'cr2-gate'      : 'APS9-m1',
               'M-q2q1'        : 'APS10-1',
               'M-q2q1-gate'   : 'APS10-m1'}
    
    for name, value in mapping.items():
        channels[name].phys_chan = channels[value]
    return channels

def save_in_library(channels, new=False, libName=":memory:"):
    """Store this constructed set of channels in a fresh (if new=True) in-memory (default) or as named channel library"""
    import QGL
    cl = QGL.ChannelLibraries.ChannelLibrary(db_resource_name=libName)
    if new:
        cl.clear()
    cl.session.add_all(channels.values())
    for chan in channels.values():
        chan.channel_db = cl.channelDatabase

    cl.update_channelDict()
    QGL.ChannelLibraries.channelLib = cl

# FIXME: Put in separate file for cleanliness?
# Control whether cr2/q3 are included?
# doHW: Should we assign to specific APS devices?
def create_default_channelLibrary(doHW=False, new=False, clName=":memory:"):
    '''
    Create a default ChannelLibrary for testing / constructing sequences.
    Contains 3 qubits ('q1','q2','q3'), with a bidirectional edge between q1 and q2 ('cr' and 'cr2'),
    including physical channel assignments if doHw=True (default false).
    Saves the CL in the named library (default in memory).
    If new=True, clears that library of any previous channels.
    Available afterwards as QGL.ChannelLibraries.channelLib
    '''
    import QGL
    from QGL.Channels import LogicalMarkerChannel, PhysicalQuadratureChannel, PhysicalMarkerChannel
    from QGL.Channels import Edge, Measurement, Qubit
    from math import pi
    import os
    channels = {}
    # assign_channels()
    qubit_names = ['q1', 'q2', 'q3']
    logical_names = ['digitizerTrig', 'slave_trig']
    
    # assign_logical_channels()
    for name in logical_names:
        channels[name] = LogicalMarkerChannel(label=name)

    for name in qubit_names:
        mName = 'M-' + name
        mgName = 'M-' + name + '-gate'
        qgName = name + '-gate'

        mg = LogicalMarkerChannel(label=mgName)
        qg = LogicalMarkerChannel(label=qgName)

        # FIXME: Use MeasFactory in case it already exists??
        m = Measurement(label=mName,
                        gate_chan=mg,
                        trig_chan=channels['digitizerTrig'],
                        meas_type='autodyne')

        # FIXME: Use QubitFactory in case this channel already exists??
        q = Qubit(label=name, gate_chan=qg)
        q.pulse_params['length'] = 30e-9
        q.pulse_params['phase'] = pi / 2

        channels[name] = q
        channels[mName] = m
        channels[mgName] = mg
        channels[qgName] = qg

    # this block depends on the existence of q1 and q2
    channels['cr-gate'] = LogicalMarkerChannel(label='cr-gate')

    cr = None
    try:
        cr = EdgeFactory(q1, q2)
    except:
        cr = Edge(label="cr",
              source=channels['q1'],
              target=channels['q2'],
              gate_chan=channels['cr-gate'])
    cr.pulse_params['length'] = 30e-9
    cr.pulse_params['phase'] = pi / 4
    channels["cr"] = cr

    mq1q2g = LogicalMarkerChannel(label='M-q1q2-gate')
    channels['M-q1q2-gate'] = mq1q2g
    channels['M-q1q2'] = Measurement(
        label='M-q1q2',
        gate_chan=mq1q2g,
        trig_chan=channels['digitizerTrig'],
        meas_type='autodyne')
    
    # Add a 2nd edge from q2 back to q1 to support edgeTest4 (which is weird)
    channels['cr2-gate'] = LogicalMarkerChannel(label='cr2-gate')
    cr2 = None
    try:
        cr2 = EdgeFactory(q2, q1)
    except:
        cr2 = Edge(label="cr2", source = channels['q2'], target = channels['q1'], gate_chan = channels['cr2-gate'] )
    cr2.pulse_params['length'] = 30e-9
    cr2.pulse_params['phase'] = pi/4
    channels["cr2"] = cr2

    mq2q1g = LogicalMarkerChannel(label='M-q2q1-gate')
    channels['M-q2q1-gate']  = mq2q1g
    channels['M-q2q1']       = Measurement(label='M-q2q1', gate_chan = mq2q1g, trig_chan=channels['digitizerTrig'], meas_type='autodyne')
    
    if (doHW):
        # finalizeMapping() for APS2; assign physical channels
        # NOTE: APS7-10 added to support q3 and cr2
        # FIXME: old unit tests used name-12 instead of name-1
        channels = assign_to_hw(channels);

    set_awg_dir()

    # Store this constructed set of channels in a fresh in-memory or as named channel library
    # FIXME: Could also have this full CL predefined in a file I read from disk
    # FIXME: ChannelLibrary has helpers that do a check_for_duplicates that I want
    # like cl.new_qubit(...). To use this I'd have to initialize the channel first, but then how does the add work?    
    save_in_library(channels, new, clName)
