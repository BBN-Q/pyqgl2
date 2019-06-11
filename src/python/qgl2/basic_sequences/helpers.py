# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qreg
from qgl2.qgl1 import Id, X, MEAS, Barrier
from qgl2.util import init

from itertools import product

@qgl2decl
def create_cal_seqs(qubits: qreg, numRepeats):
    """
    Helper function to create a set of calibration sequences.

    Parameters
    ----------
    qubits : a QRegister of channels to calibrate
    numRepeats : number of times to repeat calibration sequences (int)
    """
    # Make all combinations for qubit calibration states for n qubits and repeat

    # Assuming numRepeats=2 and qubits are q1, q2
    # Produces 2 ^ #qubits * numRepeats sequences of Id, X, MEAS,
    # something like
    # [[Id(q1)*Id(q2), M(q1)*M(q2)], [Id(q1)*Id(q2), M(q1)*M(q2)],
    #  [Id(q1)*X(q2), M(q1)*M(q2)],  [Id(q1)*X(q2), M(q1)*M(q2)],
    #  [X(q1)*Id(q2), M(q1)*M(q2)],  [X(q1)*Id(q2), M(q1)*M(q2)],
    #  [X(q1)*X(q2), M(q1)*M(q2)],   [X(q1)*X(q2), M(q1)*M(q2)]]

    # Calibrate using Id and X pulses
    calSet = [Id, X]

    for pulseSet in product(calSet, repeat=len(qubits)):
        # Repeat each calibration numRepeats times
        for _ in range(numRepeats):
            init(qubits)
            for pulse, qubit in zip(pulseSet, qubits):
                pulse(qubit)
            Barrier(qubits)
            MEAS(qubits)
