# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# Simplified version of Decoupling.py for QGL2

from math import pi
import numpy as np

from qgl2.qgl2 import qgl2decl, qreg, pulse, QRegister
from qgl2.qgl1 import X90, Id, Y, U90, MEAS, X90
from qgl2.util import init
from qgl2.basic_sequences.helpers import create_cal_seqs

@qgl2decl
def doHahnEcho(q:qreg, pulseSpacings, periods, calRepeats):

    for k in range(len(pulseSpacings)):
        init(q)
        X90(q)

        # FIXME 9/28/16: Must name the length arg
        Id(q, length=pulseSpacings[k])
        Y(q)
        Id(q, length=pulseSpacings[k])
        U90(q, phase=2*pi*periods/len(pulseSpacings)*k)
        MEAS(q)

    create_cal_seqs(q, calRepeats)

@qgl2decl
def doCPMG(q:qreg, numPulses, pulseSpacing, calRepeats):
    # delay = (pulseSpacing - q.pulseParams['length']) / 2
    delay = pulseSpacing / 2

    for rep in numPulses:
        init(q)
        X90(q)
        # Repeat the t-180-t block rep times
        for _ in range(rep):
            Id(q, length=delay)
            Y(q)
            Id(q, length=delay)
        X90(q)
        MEAS(q)

    # Tack on calibration
    create_cal_seqs(q, calRepeats)
