# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qreg, pulse, QRegister
from qgl2.qgl1 import Id, X, MEAS, Barrier, qwait
from qgl2.util import init

from itertools import product

# FIXME: measChans should be declared a qreg, but the inliner isn't handling that
@qgl2decl
def create_cal_seqs(qubits: qreg, numRepeats, measChans=None, waitcmp=False, delay=None):
    """
    Helper function to create a set of calibration sequences.

    Parameters
    ----------
    qubits : a QRegister of channels to calibrate
    numRepeats : number of times to repeat calibration sequences (int)
    measChans : QRegister of channels to measure; default is to use qubits
    waitcmp = True if the sequence contains branching; default False
    delay: optional time between state preparation and measurement (s)
    """
    # Allows supplying a tuple as is usually done in QGL1
    qubitreg = QRegister(qubits)

    if measChans is None:
        measChans = qubitreg

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

    for pulseSet in product(calSet, repeat=len(qubitreg)):
        # Repeat each calibration numRepeats times
        for _ in range(numRepeats):
            init(qubitreg)
            for pulse, qubit in zip(pulseSet, qubitreg):
                pulse(qubit)
            if delay:
                # Add optional delay before measurement
                Id(qubitreg(0), length=delay)
            Barrier(measChans)
            MEAS(measChans)
            # If branching do wait
            if waitcmp:
                qwait(kind='CMP')

@qgl2decl
def measConcurrently(listNQubits: qreg) -> pulse:
    '''Concurrently measure given QRegister of qubits.
    Note: Includes a Barrier on the input qreg to force measurements
    to be concurrent; QGL1 does Pulse*Pulse == PulseBlock(pulses), which is equivalent.'''
    qr = QRegister(listNQubits)
    Barrier(qr)
    MEAS(qr)
