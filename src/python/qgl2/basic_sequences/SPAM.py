# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# See SPAMMin for cleaner QGL2 versions

from qgl2.qgl2 import qgl2decl, qreg, qgl2main, pulse

from QGL.PulsePrimitives import X, U, Y90, X90, MEAS, Id
from QGL.Compiler import compile_to_hardware
from QGL.PulseSequencePlotter import plot_pulse_files

#from qgl2.basic_sequences.new_helpers import compileAndPlot, addMeasPulse
from qgl2.util import init

from itertools import chain
from numpy import pi

@qgl2decl
def spam_seqs(angle, qubit: qreg, maxSpamBlocks=10):
    """ Helper function to create a list of sequences increasing SPAM blocks with a given angle. """
    #SPAMBlock = [X(qubit), U(qubit, phase=pi/2+angle), X(qubit), U(qubit, phase=pi/2+angle)]
    #return [[Y90(qubit)] + SPAMBlock*rep + [X90(qubit)] for rep in range(maxSpamBlocks)]
    for rep in range(maxSpamBlocks):
        init(qubit)
        Y90(qubit)
        for _ in range(rep):
            X(qubit)
            U(qubit, phase=pi/2+angle)
            X(qubit)
            U(qubit, phase=pi/2+angle)
        X90(qubit)
        MEAS(qubit)

@qgl2decl
def SPAM(qubit: qreg, angleSweep, maxSpamBlocks=10, showPlot=False):
    """
    X-Y sequence (X-Y-X-Y)**n to determine quadrature angles or mixer correction.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    angleSweep : angle shift to sweep over
    maxSpamBlocks : maximum number of XYXY block to do
    showPlot : whether to plot (boolean)
    """
    # Original:
    # def spam_seqs(angle):
    #     """ Helper function to create a list of sequences increasing SPAM blocks with a given angle. """
    #     SPAMBlock = [X(qubit), U(qubit, phase=pi/2+angle), X(qubit), U(qubit, phase=pi/2+angle)]
    #     return [[Y90(qubit)] + SPAMBlock*rep + [X90(qubit)] for rep in range(maxSpamBlocks)]

    # # Insert an identity at the start of every set to mark them off
    # seqs = list(chain.from_iterable([[[Id(qubit)]] + spam_seqs(angle) for angle in angleSweep]))

    # # Add a final pi for reference
    # seqs.append([X(qubit)])

    # # Add the measurment block to every sequence
    # measBlock = MEAS(qubit)
    # for seq in seqs:
    #     seq.append(measBlock)

    # fileNames = compile_to_hardware(seqs, 'SPAM/SPAM')
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)

    # Insert an identity at the start of every set to mark them off
    for angle in angleSweep:
        init(qubit)
        Id(qubit)
        MEAS(qubit)
        spam_seqs(angle, qubit, maxSpamBlocks)

    # Add a final pi for reference
    init(qubit)
    X(qubit)
    MEAS(qubit)

    # FIXME: Do this in caller
    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
#    compileAndPlot('SPAM/SPAM', showPlot)

def SPAMq1(qubit: qreg, angleSweep, maxSpamBlocks=10, showPlot=False):
    """
    X-Y sequence (X-Y-X-Y)**n to determine quadrature angles or mixer correction.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    angleSweep : angle shift to sweep over
    maxSpamBlocks : maximum number of XYXY block to do
    showPlot : whether to plot (boolean)
    """
    # Original:
    # def spam_seqs(angle):
    #     """ Helper function to create a list of sequences increasing SPAM blocks with a given angle. """
    #     SPAMBlock = [X(qubit), U(qubit, phase=pi/2+angle), X(qubit), U(qubit, phase=pi/2+angle)]
    #     return [[Y90(qubit)] + SPAMBlock*rep + [X90(qubit)] for rep in range(maxSpamBlocks)]

    # # Insert an identity at the start of every set to mark them off
    # seqs = list(chain.from_iterable([[[Id(qubit)]] + spam_seqs(angle) for angle in angleSweep]))

    # # Add a final pi for reference
    # seqs.append([X(qubit)])

    # # Add the measurment block to every sequence
    # measBlock = MEAS(qubit)
    # for seq in seqs:
    #     seq.append(measBlock)

    # fileNames = compile_to_hardware(seqs, 'SPAM/SPAM')
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)

    def spam_seqs(angle):
        """ Helper function to create a list of sequences increasing SPAM blocks with a given angle. """
        #SPAMBlock = [X(qubit), U(qubit, phase=pi/2+angle), X(qubit), U(qubit, phase=pi/2+angle)]
        #return [[Y90(qubit)] + SPAMBlock*rep + [X90(qubit)] for rep in range(maxSpamBlocks)]
        seqs = []
        for rep in range(maxSpamBlocks):
            seq = []
            seq.append(Y90(qubit))
            for _ in range(rep):
                seq.append(X(qubit))
                seq.append(U(qubit, phase=pi/2+angle))
                seq.append(X(qubit))
                seq.append(U(qubit, phase=pi/2+angle))
            seq.append(X90(qubit))
            seqs.append(seq)
        return seqs

    # Insert an identity at the start of every set to mark them off
    seqs = []
    for angle in angleSweep:
        seqs.append([Id(qubit)])
        spams = spam_seqs(angle)
        for elem in spams:
            seqs.append(elem)

    # Add a final pi for reference
    seqs.append([X(qubit)])

    # # Add the measurment block to every sequence
#    seqs = addMeasPulse(seqs, qubit)

    # Be sure to un-decorate this function to make it work without the
    # QGL2 compiler
#    compileAndPlot(seqs, 'SPAM/SPAM', showPlot)

# Imports for testing only
from QGL.Channels import Qubit, LogicalMarkerChannel
from qgl2.qgl1 import Qubit, QubitFactory
import numpy as np
from math import pi

@qgl2main
def main():
    # Set up 1 qbit, following model in QGL/test/test_Sequences

    # FIXME: Cannot use these in current QGL2 compiler, because
    # a: QGL2 doesn't understand creating class instances, and 
    # b: QGL2 currently only understands the fake Qbits
#    qg1 = LogicalMarkerChannel(label="q1-gate")
#    q1 = Qubit(label='q1', gate_chan=qg1)
#    q1.pulse_params['length'] = 30e-9
#    q1.pulse_params['phase'] = pi/2

    # Use stub Qubits, but comment this out when running directly.
    q1 = QubitFactory("q1")
    SPAM(q1, np.linspace(0, pi/2, 11))

if __name__ == "__main__":
    main()
