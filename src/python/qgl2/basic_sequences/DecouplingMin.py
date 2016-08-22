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
    q = QubitFactory('q1')
    steps = 11
    # FIXME: Can't do arguments yet
    periods = 0
    # FIXME 7/25/16: Can't do variable assignment yet with expansion of np.linspace
#    pulseSpacings = np.linspace(0, 5e-6, steps)
    for k in range(steps):
#    for k in range(len(pulseSpacings)):
        init(q)
        X90(q)
        # FIXME 7/25/16: np.linspace doesn't get expanded by QGL2,
        # and so we get an import error: NameError: name 'np' is not defined
#        Id(q, np.linspace(0, 5e-6, steps)[k])
        Id(q, 0)
        Y(q)
#        Id(q, np.linspace(0, 5e-6, steps)[k])
#        Id(q, length=spacing)
        Id(q, 0)
        # FIXME 7/25/16: pi doesn't get imported
#        U90(q, phase=2*pi*periods/len(pulseSpacings)*k)
#        U90(q, phase=2*pi*periods/steps*k)
#        U90(q, phase=2*3.14159265*periods/steps*k)
#        U90(q, phase=0)
        MEAS(q)

    calRepeats = 2
    # FIXME: create_cal_seqs will not yet work in QGL2
#    create_cal_seqs((q,), calRepeats)


# qgl2 functions cannot be nested; otherwise this goes inside CPMG
@qgl2decl
def idPulseCPMG(q: qbit, pulseSpacing) -> pulse:
    # FIXME: arg confuses QGL2 compiler if not a kwarg
# FIXME: q.pulseParams results in "name 'q' is not defined"
#    qPulseLength = q.pulseParams['length']
    qPulseLength = 4e-9
#    Id(q, length=(pulseSpacing - q.pulseParams['length'])/2)
    Id(q, length=(pulseSpacing - qPulseLength)/2)

@qgl2decl
def doCPMG() -> sequence:
    q = QubitFactory('q1')

    # FIXME: Can't have arguments; otherwise want these next 3 as args

    # Create numPulses sequences
    numPulses = [0, 2, 4, 6]
    calRepeats = 2
    pulseSpacing = 500e-9
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
    # FIXME: create_cal_seqs will not yet work in QGL2
#    create_cal_seqs((q,), calRepeats)
