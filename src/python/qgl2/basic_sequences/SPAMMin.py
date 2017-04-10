# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# Cleaned up version of SPAM.py for QGL2

from qgl2.qgl2 import qgl2decl, qbit, QRegister
from qgl2.qgl1 import Y90, X, U, X90, MEAS, Id
from qgl2.util import init
from numpy import pi
import numpy as np

@qgl2decl
def spam_seqs(angle, q: qbit, maxSpamBlocks=10):
    for rep in range(maxSpamBlocks):
        init(q)
        Y90(q)
        for _ in range(rep):
            X(q)
            U(q, phase=pi/2+angle)
            X(q)
            U(q, phase=pi/2+angle)
        X90(q)
        MEAS(q)

#def doSPAM(angleSweep, maxSpamBlocks=10) -> sequence:
@qgl2decl
def doSPAM(q:qbit, angleSweep, maxSpamBlocks):

    # Insert an identity at the start of every set to mark them off
    for angle in angleSweep:
        init(q)
        Id(q)
        MEAS(q)
        spam_seqs(angle, q, maxSpamBlocks)

    # Add a final pi for reference
    init(q)
    X(q)
    MEAS(q)
