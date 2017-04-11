# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# QGL2 clean versions for T1T2.py

from qgl2.qgl2 import qgl2decl, qbit, QRegister
from qgl2.basic_sequences.helpers import create_cal_seqs
from qgl2.util import init
from qgl2.qgl1 import X, Id, MEAS, U90, X90
import numpy as np
from numpy import pi

@qgl2decl
def doInversionRecovery(q:qbit, delays, calRepeats):
    for d in delays:
        init(q)
        X(q)
        Id(q, length=d)
        MEAS(q)

    # Tack on calibration
    create_cal_seqs(q, calRepeats)

@qgl2decl
def doRamsey(q:qbit, delays, TPPIFreq, calRepeats):
    # Create the phases for the TPPI
    phases = 2*pi*TPPIFreq*delays

    # Create the basic Ramsey sequence
    for d,phase in zip(delays, phases):
        init(q)
        X90(q)
        Id(q, length=d)
        U90(q, phase=phase)
        MEAS(q)

    # Tack on calibration
    create_cal_seqs(q, calRepeats)
