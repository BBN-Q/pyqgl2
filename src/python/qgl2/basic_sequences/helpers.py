# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit_list, concur
from qgl2.qgl1 import Id, X, MEAS
from qgl2.util import init

from itertools import product

# 9/27/16:
# FIXME: measChans argument re-assignment if it was None is failing
# Callers that supply measChans will fail (see Reset and RabiAmp_NQubits)

# FIXME: 2 generators in here get turned into lists to make this work

@qgl2decl
def create_cal_seqs(qubits: qbit_list, numRepeats, measChans: qbit_list = None):
    """
    Helper function to create a set of calibration sequences.

    Parameters
    ----------
    qubits : logical channels, e.g. (q1,) or (q1,q2) (tuple)
    numRepeats = number of times to repeat calibration sequences (int)
    """
    # Make all combinations for qubit calibration states for n qubits and repeat

    # Assuming numRepeats=2 and qubits are q1, q2
    # Produces 2 ^ #qubits * numRepeats sequences of Id, X, MEAS,
    # something like
    # [[Id(q1)*Id(q2), M(q1)*M(q2)], [Id(q1)*Id(q2), M(q1)*M(q2)],
    #  [Id(q1)*X(q2), M(q1)*M(q2)],  [Id(q1)*X(q2), M(q1)*M(q2)],
    #  [X(q1)*Id(q2), M(q1)*M(q2)],  [X(q1)*Id(q2), M(q1)*M(q2)],
    #  [X(q1)*X(q2), M(q1)*M(q2)],   [X(q1)*X(q2), M(q1)*M(q2)]]

    # Original:
    # calSeqs = [reduce(operator.mul, [p(q) for p,q in zip(pulseSet, qubits)]) for pulseSet in product(calSet, repeat=len(qubits)) for _ in range(numRepeats)]
    # return [[seq, MEAS(*measChans), qwait('CMP')] if waitcmp else [seq, MEAS(*measChans)] for seq in calSeqs]

    # FIXME: This if block fails. It still evaluates as None. Issue #90
    # if measChans is None:
    #     measChans = qubits
    measChans = qubits

    # Calibrate using Id and X pulses
    calSet = [Id, X]

    # FIXME: product is a generator, and we don't handle those
    # yet to iterate over, except by wrapping in a list
    for pulseSet in list(product(calSet, repeat=len(qubits))):
        # Repeat each calibration numRepeats times
        for _ in range(numRepeats):
            # then do each pulse on each qubit concurrently

            # Initialize each sequence / experiment
            with concur:
                for q in qubits:
                    init(q)
            # Get all combinations of the pulses and qubits
            # doing the pulse on the qubit
            # Do the pulses concurrently for this pulseSet
            # FIXME 7/25/16: we have trouble with zip currently
            with concur:
                for pulse,qubit in list(zip(pulseSet, qubits)):
                    pulse(qubit)
            with concur:
                for chan in measChans:
                    MEAS(chan)
