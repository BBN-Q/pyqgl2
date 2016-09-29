# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# Simplified version of Decoupling.py for QGL2

from math import pi
import numpy as np

from qgl2.qgl2 import qgl2decl, sequence, qbit, pulse
from qgl2.qgl1 import QubitFactory, X90, Id, Y, U90, MEAS, X90
from qgl2.control import *
from qgl2.util import init
from qgl2.basic_sequences.helpers import create_cal_seqs

@qgl2decl
def doHahnEcho() -> sequence:
    # FIXME: Can't do arguments yet
    q = QubitFactory('q1')
    steps = 11
    pulseSpacings = np.linspace(0, 5e-6, steps)
    periods = 0
    calRepeats = 2

    for k in range(len(pulseSpacings)):
        init(q)
        X90(q)

        # FIXME 9/28/16: Must name the length arg
        Id(q, length=pulseSpacings[k])
        Y(q)
        Id(q, length=pulseSpacings[k])
        U90(q, phase=2*pi*periods/len(pulseSpacings)*k)
        MEAS(q)

    create_cal_seqs((q,), calRepeats)


# qgl2 functions cannot be nested; otherwise this goes inside CPMG
@qgl2decl
def idPulseCPMG(q: qbit, pulseSpacing) -> pulse:
    # FIXME: q.pulseParams results in "name 'q' is not defined"
    qPulseLength = 4e-9
#    Id(q, length=(pulseSpacing - q.pulseParams['length'])/2)
    Id(q, length=(pulseSpacing - qPulseLength)/2)

@qgl2decl
def doCPMG() -> sequence:
    q = QubitFactory('q1')

    # FIXME: Can't have arguments; otherwise want these next 3 as args

    # Create numPulses sequences
    numPulses = [0, 2, 4, 6]
    pulseSpacing = 500e-9
    calRepeats = 2

    for rep in numPulses:
        init(q)
        X90(q)
        # Repeat the t-180-t block rep times
        for _ in range(rep):
            idPulseCPMG(q, pulseSpacing)
            Y(q)
            idPulseCPMG(q, pulseSpacing)
        X90(q)
        MEAS(q)

    # Tack on calibration
    create_cal_seqs((q,), calRepeats)
