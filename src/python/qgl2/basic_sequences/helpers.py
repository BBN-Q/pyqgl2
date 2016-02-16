# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit_list

from functools import reduce
from itertools import product
import operator

from QGL.PulsePrimitives import Id, X, MEAS
from QGL.ControlFlow import qwait

@qgl2decl
def create_cal_seqs(qubits: qbit_list, numRepeats, measChans: qbit_list = None, waitcmp=False):
    """
    Helper function to create a set of calibration sequences.

    Parameters
    ----------
    qubits : logical channels, e.g. (q1,) or (q1,q2) (tuple) 
    numRepeats = number of times to repeat calibration sequences (int)
    waitcmp = True if the sequence contains branching
    """
    # Make all combinations for qubit calibration states for n qubits and repeat

    # Original:
    # calSeqs = [reduce(operator.mul, [p(q) for p,q in zip(pulseSet, qubits)]) for pulseSet in product(calSet, repeat=len(qubits)) for _ in range(numRepeats)]
    # return [[seq, MEAS(*measChans), qwait('CMP')] if waitcmp else [seq, MEAS(*measChans)] for seq in calSeqs] 

    if measChans is None:
        measChans = qubits

    # Calibrate using Id and X pulses
    calSet = [Id, X]

    # For QGL1
#    calSeqs = []

    # Create iterator with the right number of Id and X pulses
    for pulseSet in product(calSet, repeat=len(qubits)):
        # Repeat the whole numRepeats times
        for _ in range(numRepeats):
            # then do each pulse on each qubit concurrently

            # For QGL1
 #           seqs = []
 #           # Get all combinations of the pulses and qubits
 #           # doing the pulse on the qubit
 #           for pulse,qubit in zip(pulseSet, qubits):
 #               seqs.append(pulse(qubit))
 #           # Do the pulses concurrently for this pulseSet
 #           calSeqs.append(reduce(operator.mul, seqs))

            # For QGL2
            # Get all combinations of the pulses and qubits
            # doing the pulse on the qubit
            # Do the pulses concurrently for this pulseSet
            with concur:
                for pulse,qubit in zip(pulseSet, qubits):
                    pulse(qubit)
            # Add on the measurement pulses (done concurrently)
            with concur:
                for chan in measChans:
                    MEAS(chan)
            # Optionally wait here
            if waitcmp:
                qwait('CMP') # How will QGL2 do with this ControlInstruction?

    # QGL1 only here:
#    # Add on the measurement operator, optionally waiting
#    newCalSeqs = []
#    for seq in calSeqs:
#        if waitcmp:
#            newCalSeqs.append([seq, MEAS(*measChans), qwait('CMP')])
#        else:
#            newCalSeqs.append([seq, MEAS(*measChans)])
#    return newCalSeqs
