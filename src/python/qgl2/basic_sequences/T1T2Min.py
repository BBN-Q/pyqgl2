# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# QGL2 clean versions for T1T2.py

from qgl2.qgl2 import qgl2decl, qbit
from qgl2.basic_sequences.helpers import create_cal_seqs
from qgl2.util import init
from qgl2.qgl1 import QubitFactory, X, Id, MEAS, U90, X90
import numpy as np
from numpy import pi

@qgl2decl
def doInversionRecovery():
    # FIXME: No args possible yet
    q = QubitFactory('q1')
    delays = np.linspace(0, 5e-6, 11)
    calRepeats = 2
    for d in delays:
        init(q)
        X(q)
        Id(q, length=d)
        MEAS(q)

    # Tack on calibration
    create_cal_seqs((q,), calRepeats)

@qgl2decl
def doRamsey():
    # FIXME: No args possible yet: TPPIFreq, pulseSpacings, calRepeats
    q = QubitFactory('q1')
    pulseSpacings=np.arange(100e-9, 10e-6, 100e-9)
    TPPIFreq=1e6 # 0
    calRepeats = 2

    # Create the phases for the TPPI
    phases = 2*pi*TPPIFreq*pulseSpacings

    # Create the basic Ramsey sequence
    # FIXME: QGL2 doesn't deal well with this call to zip: make it a list
    for d,phase in list(zip(pulseSpacings, phases)):
        init(q)
        X90(q)
        Id(q, length=d)
        U90(q, phase=phase)
        MEAS(q)

    # Tack on calibration
    create_cal_seqs((q,), calRepeats)
