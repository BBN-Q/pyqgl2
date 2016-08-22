# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# QGL2 versions of Rabi.py functions.
# These work around QGL2 constraints, such as only doing sequence generation and
# not compilation, or not taking arguments.

import QGL.PulseShapes
from qgl2.qgl2 import qgl2decl, qbit, sequence, concur
from qgl2.qgl1 import QubitFactory, Utheta, MEAS, X, Id
from qgl2.util import init
import numpy as np

# 7/25/16: Currently fails
@qgl2decl
def doRabiWidth() -> sequence:
    q = QubitFactory("q1")
    for l in np.linspace(0, 5e-6, 11):
        init(q)
        # FIXME: QGL2 loses the import needed for this QGL function
        Utheta(q, length=l, amp=1, phase=0, shapeFun=QGL.PulseShapes.tanh)
        MEAS(q)

# For use with pyqgl2.main
# Note hard coded amplitudes and phase
@qgl2decl
def doRabiAmp() -> sequence:
    q = QubitFactory('q1') # Default qubit that will be replaced

    for amp in np.linspace(0,5e-6,11):
        init(q)
        Utheta(q, amp=amp, phase=0)
        MEAS(q)

# An example of multiple expansions (a call to np.linspace, and
# the parameters to np.linspace)
@qgl2decl
def doRabiAmp3() -> sequence:
    steps = 3
    zero = 0
    phase = 0
    q = QubitFactory('q1')
    for l in np.linspace(zero, 5e-6, steps):
        init(q)
        Utheta(q, amp=l, phase=phase)
        MEAS(q)

# FIXME: Giving args to this makes it fail,
# but want amps & phase as args
@qgl2decl
def doRabiAmp4() -> sequence:
    q = QubitFactory('q1')

    steps = 3
    zero = 0
    phase=0

    # This fails to import np.linspace
    # - in check_qbit assign_simple I think
    amps=np.linspace(zero, 5e-6, steps)
    for l in amps:
        init(q)
        Utheta(q, amp=l, phase=phase)
        MEAS(q)

# FIXME: As above, want to pass in amps, phase, qbits
@qgl2decl
def doRabiAmpPi() -> sequence:
    q1 = QubitFactory('q1')
    q2 = QubitFactory('q2')
    # FIXME: This fails to import np.linspace
    # - in check_qbit assign_simple I think
#    amps=np.linspace(0, 5e-6, 3)
    phase=0
    for l in np.linspace(0, 5e-6, 3):
        with concur:
            init(q1)
            init(q2)
        X(q2)
        Utheta(q1, amp=l, phase=phase)
        X(q2)
        MEAS(q2)

@qgl2decl
def doSingleShot() -> sequence:
    q = QubitFactory('q1')
    init(q)
    Id(q)
    MEAS(q)
    init(q)
    X(q)
    MEAS(q)

@qgl2decl
def doPulsedSpec() -> sequence:
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
