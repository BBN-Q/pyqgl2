# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qreg, pulse, QRegister
from qgl2.qgl1 import Id, X, MEAS, Barrier, qwait
from qgl2.util import init

from itertools import product
import operator
from functools import reduce

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

    # QGL2 will warn here:
    # warning: parameter [measChans] overwritten by assignment
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

# Copied from QGL/BasicSequences/helpers
def cal_descriptor(qubits, numRepeats, partition=2, states = ['0', '1']):
    # generate state set in same order as we do above in create_cal_seqs()
    state_set = [reduce(operator.add, s) for s in product(states, repeat=len(qubits))]
    descriptor = {
        'name': 'calibration',
        'unit': 'state',
        'partition': partition,
        'points': []
    }
    for state in state_set:
        descriptor['points'] += [state] * numRepeats
    return descriptor

# Copied from QGL/BasicSequences/helpers
def delay_descriptor(delays, desired_units="us"):
    if desired_units == "s":
        scale = 1
    elif desired_units == "ms":
        scale = 1e3
    elif desired_units == "us" or desired_units == u"μs":
        scale = 1e6
    elif desired_units == "ns":
        scale = 1e9
    axis_descriptor = {
        'name': 'delay',
        'unit': desired_units,
        'points': list(scale * delays),
        'partition': 1
    }
    return axis_descriptor
