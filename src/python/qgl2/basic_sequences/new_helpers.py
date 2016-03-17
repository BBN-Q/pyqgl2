# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit_list, qbit, concur, pulse, GATHER_SEQUENCES

from .helpers import create_cal_seqs
#from .qgl2_plumbing import qgl2AddSequences, sequence_list

#from QGL.PulsePrimitives import Id, X, Y, X90, Y90, MEAS
from QGL.Compiler import compile_to_hardware
from qgl2.qgl1 import compile_to_hardware, Id, X, Y, X90, Y90, MEAS
from QGL.PulseSequencePlotter import plot_pulse_files

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

    # You must copy the element before repeating it. Otherwise strange things happen later
    return [copy.copy(sequence) for sequence in listOfSequences for i in range(repeat)]

#def compileAndPlot(listOfSequences: sequence, filePrefix, showPlot=False):
@qgl2decl
def compileAndPlot(filePrefix, showPlot=False, suffix=''):
    """Compile the listOfSequences to hardware using the given filePrefix, 
    print the filenames, and optionally plot the pulse files.

    Maybe soon again but not now: 
    Return a handle to the plot window; caller can hold it to prevent window destruction.

    NOTE: The QGL2 compiler must fill in the listOfSequences for GATHER_SEQUENCES()."""
    fileNames = compile_to_hardware(GATHER_SEQUENCES(), filePrefix, suffix)
    print(fileNames)

    if showPlot:
        plotWin = plot_pulse_files(fileNames)
        # FIXME: QGL2 won't inline this if there is a return statement
#        return plotWin

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

# Helpers here for AllXY that produce pairs of pulses on the same qubit
# Produce the state |0>
@qgl2decl
def IdId(q: qbit) -> sequence:
    # no pulses
    Id(q)
    Id(q)

@qgl2decl
def XX(q: qbit) -> sequence:
    # pulse around same axis
    X(q)
    X(q)

@qgl2decl
def YY(q: qbit) -> sequence:
    # pulse around same axis
    Y(q)
    Y(q)

@qgl2decl
def XY(q: qbit) -> sequence:
    # pulsing around orthogonal axes
    X(q)
    Y(q)

@qgl2decl
def YX(q: qbit) -> sequence:
    # pulsing around orthogonal axes
    Y(q)
    X(q)

# These next produce a |+> or |i> state (equal superposition of |0> + |1>)
@qgl2decl
def X90Id(q: qbit) -> sequence:
    # single pulses
    X90(q)
    Id(q)

@qgl2decl
def Y90Id(q: qbit) -> sequence:
    # single pulses
    Y90(q)
    Id(q)

@qgl2decl
def X90Y90(q: qbit) -> sequence:
    # pulse pairs around orthogonal axes with 1e error sensititivity
    X90(q)
    Y90(q)

@qgl2decl
def Y90X90(q: qbit) -> sequence:
    # pulse pairs around orthogonal axes with 1e error sensititivity
    Y90(q)
    X90(q)

@qgl2decl
def X90Y(q: qbit) -> sequence:
    # pulse pairs with 2e sensitivity
    X90(q)
    Y(q)

@qgl2decl
def Y90X(q: qbit) -> sequence:
    # pulse pairs with 2e sensitivity
    Y90(q)
    X(q)

@qgl2decl
def XY90(q: qbit) -> sequence:
    # pulse pairs with 2e sensitivity
    X(q)
    Y90(q)

@qgl2decl
def YX90(q: qbit) -> sequence:
    # pulse pairs with 2e sensitivity
    Y(q)
    X90(q)

@qgl2decl
def X90X(q: qbit) -> sequence:
    # pulse pairs around common axis with 3e error sensitivity
    X90(q)
    X(q)

@qgl2decl
def XX90(q: qbit) -> sequence:
    # pulse pairs around common axis with 3e error sensitivity
    X(q)
    X90(q)

@qgl2decl
def Y90Y(q: qbit) -> sequence:
    # pulse pairs around common axis with 3e error sensitivity
    Y90(q)
    Y(q)

@qgl2decl
def YY90(q: qbit) -> sequence:
    # pulse pairs around common axis with 3e error sensitivity
    Y(q)
    Y90(q)

# These next create the |1> state
@qgl2decl
def XId(q: qbit) -> sequence:
    # single pulses
    X(q)
    Id(q)

@qgl2decl
def YId(q: qbit) -> sequence:
    # single pulses
    Y(q)
    Id(q)

@qgl2decl
def X90X90(q: qbit) -> sequence:
    # pulse pairs
    X90(q)
    X90(q)

@qgl2decl
def Y90Y90(q: qbit) -> sequence:
    # pulse pairs
    Y90(q)
    Y90(q)
