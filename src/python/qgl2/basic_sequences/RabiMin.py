# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# QGL2 versions of Rabi.py functions.
# These work around QGL2 constraints, such as only doing sequence generation and
# not compilation, or not taking arguments.

import QGL.PulseShapes
from qgl2.qgl2 import qgl2decl, qbit, sequence, concur
from qgl2.qgl1 import QubitFactory, Utheta, MEAS, X, Id
from qgl2.util import init
from qgl2.basic_sequences.helpers import create_cal_seqs
import numpy as np

# 7/25/16: Currently fails
@qgl2decl
def doRabiWidth():
    # FIXME: No arguments
    q = QubitFactory("q1")
    widths = np.linspace(0, 5e-6, 11)
    amp = 1
    phase = 0
    shapeFun = QGL.PulseShapes.tanh
    for l in widths:
        init(q)
        # FIXME: QGL2 loses the import needed for this QGL function
        Utheta(q, length=l, amp=amp, phase=phase,
               shapeFun=QGL.PulseShapes.tanh)
        # Doing it this way gives: KeyError: 'shapeFun___ass_004'
        # Utheta(q, length=l, amp=amp, phase=phase, shapeFun=shapeFun)
        MEAS(q)

# For use with pyqgl2.main
# Note hard coded amplitudes and phase
@qgl2decl
def doRabiAmp():
    q = QubitFactory('q1')
    steps = 11
    amps = np.linspace(0, 1, steps)
    phase = 0

    for amp in amps:
        init(q)
        Utheta(q, amp=amp, phase=phase)
        MEAS(q)

# FIXME: As above, want to pass in amps, phase, qbits
@qgl2decl
def doRabiAmpPi():
    q1 = QubitFactory('q1')
    q2 = QubitFactory('q2')
    amps = np.linspace(0, 1, 11)
    phase = 0

    for l in amps:
        with concur:
            init(q1)
            init(q2)
        X(q2)
        Utheta(q1, amp=l, phase=phase)
        X(q2)
        MEAS(q2)

@qgl2decl
def doSingleShot():
    q = QubitFactory('q1')
    init(q)
    Id(q)
    MEAS(q)
    init(q)
    X(q)
    MEAS(q)

@qgl2decl
def doPulsedSpec():
    q = QubitFactory('q1')
    # FIXME: Want a specOn arg but that currently doesn't work
# qgl2/basic_sequences/RabiMin.py:80:7: error: eval failure [specOn]: name 'specOn' is not defined
    specOn = True
    init(q)
    if specOn:
        X(q)
    else:
        Id(q)
    MEAS(q)

# Rabi_Amp_NQubits in QGL1 has a bug; it should
# be doing MEAS over the measChans. So something like below.

@qgl2decl
def doRabiAmp_NQubits():
    # FIXME: Can't have args
    q1 = QubitFactory('q1')
    q2 = QubitFactory('q2')
    qubits = [q1, q2]
#    measChans = None
    amps = np.linspace(0, 5e-6, 11)
    p = 0
    docals = False
    calRepeats = 2

    # FIXME: Re-assigning measChans fails.
    # Once it is assigned, you cannot re-assign it
#    if not measChans:
    measChans = qubits
#    measChans = [q2, q1]

    for a in amps:
        with concur:
            # FIXME: Can't handle enumerate generator
            for ct, q in list(enumerate(qubits)):
                init(q)
                Utheta(q, amp=a, phase=p)
                if measChans == qubits:
                    MEAS(q)
                else:
                    MEAS(measChans[ct])

    if docals:
        # FIXME: This isn't working yet
        create_cal_seqs(qubits, calRepeats, measChans=measChans)

# This version allows the Xs and Id pulse to be done in parallel,
# as quick as possible. But we can't tell what the QGL1 method was
# trying to do, so this may be meaningless.
@qgl2decl
def doSwap():
    # FIXME: Args
    q = QubitFactory('q1')
    mq = QubitFactory('q2')
    delays = np.linspace(0, 5e-6, 11)

    for d in delays:
        with concur:
            init(q)
            init(mq)
            X(q)
            X(mq)
            Id(mq, d)
        with concur:
            MEAS(mq)
            MEAS(q)

    # FIXME: This isn't working yet
    # create_cal_seqs((mq, q), 2)

