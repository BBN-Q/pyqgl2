# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# Most of these are no longer used.
# Some of these are used in AllXY

from qgl2.qgl2 import qgl2decl, qbit_list, qbit, concur, pulse, sequence

# from qgl2.basic_sequences.helpers import create_cal_seqs

from qgl2.qgl1 import Id, X, Y, X90, Y90, MEAS

import copy
import functools
import inspect
import operator

# This one is qgl1 style
# FIXME: Remove sequence_list for now as QGL2 compiler dislikes it
#def addMeasPulse(listOfSequencesOn1Qubit: sequence_list, q: qbit):
def addMeasPulse(listOfSequencesOn1Qubit, q: qbit):
    '''Add a MEAS(q) to each sequence in the given list of sequences.'''
    return [sequence + [MEAS(q)] for sequence in listOfSequencesOn1Qubit]

# Copied to CRMin.py
@qgl2decl
def measConcurrently(listNQubits: qbit_list) -> pulse:
    '''Concurrently measure each of the given qubits.'''
    with concur:
        for q in listNQubits:
            MEAS(q)

# This one is qgl1 style
# Variant of above to add a MEAS for each qbit used in the sequences, not just 1
# FIXME: Remove sequence_list for now as QGL2 compiler dislikes it
#def addMeasPulses(listOfSequencesOnNQubits: sequence_list, listNQubits: qbit_list):
def addMeasPulses(listOfSequencesOnNQubits, listNQubits: qbit_list):
    '''Add (one MEAS(qn) for each qubit qn in listNQubits) to each sequence in the given list of sequences.'''
    measurements = None
    for q in listNQubits:
        if measurements == None:
            measurements = MEAS(q)
        else:
            measurements *= MEAS(q)

    for sequence in listOfSequencesOnNQubits:
        sequence.append(measurements)
    return listOfSequencesOnNQubits

# What would a QGL2 style repeat look like? Is it just for _ in range?
# QGL1 style
# FIXME: Remove sequence_list for now as QGL2 compiler dislikes it
#def repeatSequences(listOfSequences: sequence_list, repeat=2):
def repeatSequences(listOfSequences, repeat=2):
    '''Repeat each sequence in the given list of sequences repeat times.

    For example, `[[a, 1], [b, 2]]` becomes `[[a, 1], [a, 1], [b, 2], [b, 2]]`.
    Note this could be a list of function names that then get executed.'''
    return [copy.copy(sequence) for sequence in listOfSequences for i in range(repeat)]

# QGL1 style method
# For QGL2, simply do create_cal_seqs((tupleOfQubits), numRepeats)
# FIXME: Remove sequence_list for now as QGL2 compiler dislikes it
#def addCalibration(listOfSequences: sequence_list, tupleOfQubits: qbit_list, numRepeats=2):
def addCalibration(listOfSequences, tupleOfQubits: qbit_list, numRepeats=2):
    '''Add on numRepeats calibration sequences of the given tuple of qubits to the given
    list of sequences.'''
    # Tack on the calibration sequences
    listOfSequences += create_cal_seqs((tupleOfQubits), numRepeats)
    return listOfSequences
