from qgl2.qgl2 import qgl2decl, sequence, qbit
from qgl2.control import *
from qgl2.qgl1 import QubitFactory, Y90, X, U, X90, MEAS, Id
from qgl2.util import init
from numpy import pi
import numpy as np

@qgl2decl
def spam_seqs(angle) -> sequence:
#        for rep in range(maxSpamBlocks):
    for rep in range(10):
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
def doSPAM() -> sequence:
    q = QubitFactory('q1')
#    angleSweep = np.linspace(0, pi/2, 11)
#    angleSweep = [ 0.        ,  0.15707963,  0.31415927,  0.4712389 ,  0.62831853,
#                   0.78539816,  0.9424778 ,  1.09955743,  1.25663706,  1.41371669,
#                   1.57079633]

    # Insert an identity at the start of every set to mark them off
    for angle in [ 0.        ,  0.15707963,  0.31415927,  0.4712389 ,  0.62831853,
                   0.78539816,  0.9424778 ,  1.09955743,  1.25663706,  1.41371669,
                   1.57079633]:
        init(q)
        Id(q)
        MEAS(q)
        spam_seqs(angle)

    # Add a final pi for reference
    init(q)
    X(q)
    MEAS(q)
