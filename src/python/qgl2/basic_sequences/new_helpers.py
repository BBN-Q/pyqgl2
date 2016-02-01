# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit_list, qbit

from .helpers import create_cal_seqs

from QGL.PulsePrimitives import MEAS
from QGL.Compiler import compile_to_hardware
from QGL.PulseSequencePlotter import plot_pulse_files

import copy
import functools
import operator

@qgl2decl
def addMeasPulse(listOfSequencesOn1Qubit, q: qbit):
    '''Add a MEAS(q) to each sequence in the given list of sequences.'''
    return [listOfSequencesOn1Qubit[ind] + [MEAS(q)] for ind in range(len(listOfSequencesOn1Qubit))]

# Variant of above to add a MEAS for each qbit used in the sequences, not just 1
@qgl2decl
def addMeasPulses(listOfSequencesOnNQubits, listNQubits: qbit_list):
    '''Add (one MEAS(qn) for each qubit qn in listNQubits) to each sequence in the given list of sequences.'''
    return [listOfSequencesOnNQubits[ind] + [functools.reduce(operator.mul, [MEAS(q) for q in listNQubits])] for ind in range(len(listOfSequencesOnNQubits))]

@qgl2decl
def repeatSequences(listOfSequences, repeat=2):
    '''Repeat each sequence in the given list of sequences repeat times.

    For example, `[[a, 1], [b, 2]]` becomes `[[a, 1], [a, 1], [b, 2], [b, 2]]`.'''
    # You must copy the element before repeating it. Otherwise strange things happen later
    return [copy.copy(listOfSequences[ind]) for ind in range(len(listOfSequences)) for i in range(repeat)]

@qgl2decl
def compileAndPlot(listOfSequences, filePrefix, showPlot=False):
    '''Compile the listOfSequences to hardware using the given filePrefix, 
    print the filenames, and optionally plot the pulse files.'''
    fileNames = compile_to_hardware(listOfSequences, filePrefix)
    print(fileNames)

    if showPlot:
        plot_pulse_files(fileNames)

# FIXME: Should that be a tuple or explicitly 1 qbit or 2?
@qgl2decl
def addCalibration(listOfSequences, tupleOfQubits: qbit_list, numRepeats=2):
    '''Add on numRepeats calibration sequences of the given tople of qubits to the given
    list of sequences.'''
    # Tack on the calibration sequences
    listOfSequences += create_cal_seqs((tupleOfQubits), numRepeats)
    return listOfSequences
