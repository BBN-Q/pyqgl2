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
    return [sequence + [MEAS(q)] for sequence in listOfSequencesOn1Qubit]

# Variant of above to add a MEAS for each qbit used in the sequences, not just 1
@qgl2decl
def addMeasPulses(listOfSequencesOnNQubits, listNQubits: qbit_list):
    '''Add (one MEAS(qn) for each qubit qn in listNQubits) to each sequence in the given list of sequences.'''
    # Note operator.mul means do the MEAS concurrently
    # FIXME: Use with concur? What would that look like?
    
    # Option 1:
    # return [sequence + [functools.reduce(operator.mul, [MEAS(q) for q in listNQubits])] for sequence in listOfSequencesOnNQubits]

    # Option 2:
    # return [sequence + [MEAS(*listNQubits)] for sequence in listOfSequencesOnNQubits]

    # Option 3:
    measurements = None
    for q in listNQubits:
        if measurements == None:
            measurements = MEAS(q)
        else:
            measurements *= MEAS(q)
    for sequence in listOfSequencesOnNQubits:
        sequence.append(measurements)

    return listOfSequencesOnNQubits


    # How about using with concur?
    # That doesn't return anything, so how does this work?
    # Typical with is somthing like this
    # with func() and var:
    #    do something, presuambly involving var
    # And any variable assignment is inside that block, so that's where we'd have to add to the list

    # Dan says wthat with QGL2 I need everything to be a function.
    # A QGL1 list of operations turns into a block, where each element is a single statement
    # and if that element is a produce of 2 things, that's with concur
    # So I need the list of lists that is a list of sequences to be a block of blocks, where each element in the block is the
    # relevant function, and the MEAS*MEAS with with concur MEAS() MEAS()

    # Option 4:
    # Use with concur
    # def measConcurrently(listNQubits: qbit_list):
    #     with concur:
    #         for q in listNQubits:
    #             MEAS(q)
    # measurements = measConcurrently(listNQubits)

    # for sequence in listOfSequencesOnNQubits:
    #     sequence.append(measurements)

    # return listOfSequencesOnNQubits

    #for sequence in listOfSequencesOnNQubits:
    #    sequence.append(
    #        with concur:
    #            for q in listNQubits:
    #                MEAS(q)
    #        )
    #return listOfSequencesOnNQubits

@qgl2decl
def repeatSequences(listOfSequences, repeat=2):
    '''Repeat each sequence in the given list of sequences repeat times.

    For example, `[[a, 1], [b, 2]]` becomes `[[a, 1], [a, 1], [b, 2], [b, 2]]`.'''
    # You must copy the element before repeating it. Otherwise strange things happen later
    return [copy.copy(sequence) for sequence in listOfSequences for i in range(repeat)]

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
