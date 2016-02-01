# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit_list, qbit

from .helpers import create_cal_seqs

from QGL.PulsePrimitives import MEAS
from QGL.Compiler import compile_to_hardware
from QGL.PulseSequencePlotter import plot_pulse_files

@qgl2decl
def addMeasPulse(listOfSequencesOn1Qubit, q: qbit):
    return [listOfSequencesOn1Qubit[ind] + [MEAS(q)] for ind in range(len(listOfSequencesOn1Qubit))]
# Elsewhere code does this:
# # Add the measurement to all sequences
# for seq in seqsBis:
#     seq.append(functools.reduce(operator.mul, [MEAS(q) for q in qubits]))

@qgl2decl
def repeatSequences(listOfSequences, repeat=2):
    return [listOfSequences[ind] for ind in range(len(listOfSequences)) for i in range(repeat)]

@qgl2decl
def compileAndPlot(listOfSequences, filePrefix, showPlot=False):
    fileNames = compile_to_hardware(listOfSequences, filePrefix)
    print(fileNames)

    if showPlot:
        plot_pulse_files(fileNames)

# FIXME: Should that be a tuple or explicitly 1 qbit or 2?
@qgl2decl
def addCalibration(listOfSequences, tupleOfQubits: qbit_list, numRepeats=2):
    # Tack on the calibration sequences
    listOfSequences += create_cal_seqs((tupleOfQubits), numRepeats)
    return listOfSequences
