# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit, qbit_list, pulse, concur

from QGL.PulsePrimitives import MEAS, Id, X, AC
from QGL.PulseSequencePlotter import plot_pulse_files
from QGL.Cliffords import clifford_seq, clifford_mat, inverse_clifford
from QGL.Compiler import compile_to_hardware

from qgl2.basic_sequences.helpers import create_cal_seqs
from qgl2.basic_sequences.new_helpers import compileAndPlot
from qgl2.util import init

from csv import reader
from functools import reduce
import operator
import os

import numpy as np

def create_RB_seqs(numQubits, lengths, repeats=32, interleaveGate=None):
    """
    Create a list of lists of Clifford gates to implement RB.
    """

    # Original:
    # if numQubits == 1:
    #     cliffGroupSize = 24
    # elif numQubits == 2:
    #     cliffGroupSize = 11520
    # else:
    #     raise Exception("Can only handle one or two qubits.")

    # # Create lists of of random integers 
    # # Subtract one from length for recovery gate
    # seqs = []
    # for length in lengths:
    #     seqs += np.random.random_integers(0, cliffGroupSize-1, (repeats, length-1)).tolist()

    # # Possibly inject the interleaved gate
    # if interleaveGate:
    #     newSeqs = []
    #     for seq in seqs:
    #         newSeqs.append(np.vstack((np.array(seq, dtype=np.int), interleaveGate*np.ones(len(seq), dtype=np.int))).flatten(order='F').tolist())
    #     seqs = newSeqs
    # # Calculate the recovery gate
    # for seq in seqs:
    #     if len(seq) == 1:
    #         mat = clifford_mat(seq[0], numQubits)
    #     else:
    #         mat = reduce(lambda x,y: np.dot(y,x), [clifford_mat(c, numQubits) for c in seq])
    #     seq.append(inverse_clifford(mat))

    # return seqs


    # This function seems to just give lists of numbers. So leave it intact

    # Sample output:
    # create_RB_seqs(2,[3,3]):
    # [[8697,5492,1910], [num, num, num], .... for 64 such lists of 3 #s
    # create_RB_seqs(2,[2,2]) gives 64 lists of 2 #s
    # create_RB_seqs(1,[2,2]) gives 64 lists of 2 #s that are smaller
    # create_RB_seqs(1,[2,3]) gives 64 lists, 32 of 2 #s, followed by 32 of 3 #s

    if numQubits == 1:
        cliffGroupSize = 24
    elif numQubits == 2:
        cliffGroupSize = 11520
    else:
        raise Exception("Can only handle one or two qubits.")

    # Create lists of random integers 
    # Subtract one from length for recovery gate
    seqs = []
    for length in lengths:
        seqs += np.random.random_integers(0, cliffGroupSize-1, (repeats, length-1)).tolist()

    # Possibly inject the interleaved gate
    if interleaveGate:
        newSeqs = []
        for seq in seqs:
            newSeqs.append(np.vstack((np.array(seq, dtype=np.int), interleaveGate*np.ones(len(seq), dtype=np.int))).flatten(order='F').tolist())
        seqs = newSeqs
    # Calculate the recovery gate
    for seq in seqs:
        if len(seq) == 1:
            mat = clifford_mat(seq[0], numQubits)
        else:
            mat = reduce(lambda x,y: np.dot(y,x), [clifford_mat(c, numQubits) for c in seq])
        seq.append(inverse_clifford(mat))

    return seqs

@qgl2decl
def SingleQubitRB(qubit: qbit, seqs, showPlot=False):
    """
    Single qubit randomized benchmarking using 90 and 180 generators. 

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel)
    seqs : list of lists of Clifford group integers
    showPlot : whether to plot (boolean)
    """
    # Original:
    # seqsBis = []
    # for seq in seqs:
    #     seqsBis.append(reduce(operator.add, [clifford_seq(c, qubit) for c in seq]))

    # # Add the measurement to all sequences
    # for seq in seqsBis:
    #     seq.append(MEAS(qubit))

    # # Tack on the calibration sequences
    # seqsBis += create_cal_seqs((qubit,), 2)

    # fileNames = compile_to_hardware(seqsBis, 'RB/RB')
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)


    # seqs are result of create_RB_seqs: list of lists of integers
    # clifford_seq() returns a sequence of pulses itself
    # [clifford_seq() for c in seq]
    #   gives a list of len(seq) sequences
    # reduce(operator.add, listOfSequences)
    #   gives a single sequence of all the elements in listOfSequences
    # So the first for loop creates a single list of sequences


    # I assume we're not redoing clifford_seq

    for seq in seqs:
        init(qubit)
        for c in seq:
            clifford_seq(c, qubit)
        MEAS(qubit)

    # Tack on calibration sequences
    create_cal_seqs((qubit,), 2)

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    compileAndPlot('RB/RB', showPlot)

@qgl2decl
def TwoQubitRB(q1: qbit, q2: qbit, seqs, showPlot=False, suffix=""):
    """
    Two qubit randomized benchmarking using 90 and 180 single qubit generators and ZX90 

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel)
    seqs : list of lists of Clifford group integers
    showPlot : whether to plot (boolean)
    """

    # Original:
    # seqsBis = []
    # for seq in seqs:
    #     seqsBis.append(reduce(operator.add, [clifford_seq(c, q1, q2) for c in seq]))

    # # Add the measurement to all sequences
    # for seq in seqsBis:
    #     seq.append(MEAS(q1, q2))

    # # Tack on the calibration sequences
    # seqsBis += create_cal_seqs((q1,q2), 2)

    # fileNames = compile_to_hardware(seqsBis, 'RB/RB', suffix=suffix)
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)

    for seq in seqs:
        with concur:
            init(q1)
            init(q2)
        for c in seq:
            clifford_seq(c, q1, q2)
        with concur:
            MEAS(q1)
            MEAS(q2)

    # Tack on the calibration sequences
    create_cal_seqs((q1,q2), 2)

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    compileAndPlot('RB/RB', showPlot, suffix=suffix)

@qgl2decl
def SingleQubitRB_AC(qubit: qbit, seqs, showPlot=False):
    """
    Single qubit randomized benchmarking using atomic Clifford pulses. 

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel)
    seqFile : file containing sequence strings
    showPlot : whether to plot (boolean)
    """

    # Original:
    # seqsBis = []
    # for seq in seqs:
    #     seqsBis.append([AC(qubit, c) for c in seq])

    # # Add the measurement to all sequences
    # for seq in seqsBis:
    #     seq.append(MEAS(qubit))

    # # Tack on the calibration sequences
    # seqsBis += create_cal_seqs((qubit,), 2)

    # fileNames = compile_to_hardware(seqsBis, 'RB/RB')
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)

    # AC() gives a single pulse on qubit

    for seq in seqs:
        init(qubit)
        for c in seq:
            AC(qubit, c)
        MEAS(qubit)

    # Tack on calibration sequences
    create_cal_seqs((qubit,), 2)

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    compileAndPlot('RB/RB', showPlot)

@qgl2decl
def SingleQubitIRB_AC(qubit: qbit, seqFile, showPlot=False):
    """
    Single qubit interleaved randomized benchmarking using atomic Clifford pulses. 

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel)
    seqFile : file containing sequence strings
    showPlot : whether to plot (boolean)
    """

    # Original:
    # # Setup a pulse library
    # pulseLib = [AC(qubit, cliffNum) for cliffNum in range(24)]
    # pulseLib.append(pulseLib[0])
    # measBlock = MEAS(qubit)

    # with open(seqFile,'r') as FID:
    #     fileReader = reader(FID)
    #     seqs = []
    #     for pulseSeqStr in fileReader:
    #         seq = []
    #         for pulseStr in pulseSeqStr:
    #             seq.append(pulseLib[int(pulseStr)])
    #         seq.append(measBlock)
    #         seqs.append(seq)

    # # Hack for limited APS waveform memory and break it up into multiple files
    # # We've shuffled the sequences so that we loop through each gate length on the inner loop
    # numRandomizations = 36
    # for ct in range(numRandomizations):
    #     chunk = seqs[ct::numRandomizations]
    #     chunk1 = chunk[::2]
    #     chunk2 = chunk[1::2]
    #     # Tack on the calibration scalings
    #     chunk1 += [[Id(qubit), measBlock], [X(qubit), measBlock]]
    #     fileNames = compile_to_hardware(chunk1, 'RB/RB', suffix='_{0}'.format(2*ct+1))
    #     chunk2 += [[Id(qubit), measBlock], [X(qubit), measBlock]]
    #     fileNames = compile_to_hardware(chunk2, 'RB/RB', suffix='_{0}'.format(2*ct+2))

    # if showPlot:
    #     plot_pulse_files(fileNames)

    # FIXME: How do we tell the compiler this should return a list of pulses?
    @qgl2decl
    def doACPulse(qubit: qbit, cliffNum) -> pulse:
        if cliffNum == 24:
            cliffNum = 0
        if cliffNum > 24:
            raise Exception("Max cliffNum 24, got %d" % cliffNum)
        AC(qubit, cliffNum)

    pulseSeqStrs = []
    with open(seqFile, 'r') as FID:
        fileReader = reader(FID)
        # each line in the file is a sequence, but I don't know how many that is
        for pulseSeqStr in fileReader:
            pulseSeqStrs.append(pulseSeqStr)
    numSeqs = len(pulseSeqStrs)

    # FIXME: How do we tell the compiler this should return a sequence of pulses?
    @qgl2decl
    def getPulseSeq(qubit: qbit, seqNum) -> pulse:
        pulseSeqStr = pulseSeqStrs[seqNum]
        init(qubit)
        for pulseStr in pulseSeqStr:
            doACPulse(qubit, int(pulseStr))
        MEAS(qubit)

    # Hack for limited APS waveform memory and break it up into multiple files
    # We've shuffled the sequences so that we loop through each gate length on the inner loop
    numRandomizations = 36
    fileNames = []
    for ct in range(numRandomizations):
        doCt = ct
        isOne = True
        while doCt < numSeqs:
            getPulseSeq(qubit, doCt)

            # Tack on calibration scalings
            if isOne:
                init(qubit)
                Id(qubit)
                MEAS(qubit)
                init(qubit)
                X(qubit)
                meas(qubit)
            else:
                init(qubit)
                Id(qubit)
                meas(qubit)
                init(qubit)
                X(qubit)
                meas(qubit)

            # Now write these sequences
            # FIXME: Then magically get the sequences here....
            # This needs to get refactored....
            fileNames = compile_to_hardware([], 'RB/RB',
                                            suffix='_{0}'.format(2*ct+1+1*(not
                                                                           isOne)),
                                            qgl2=True)

            doCt += numRandomizations
            isOne = not isOne

    if showPlot:
        plot_pulse_Files(fileNames)

@qgl2decl
def SingleQubitRBT(qubit: qbit, seqFileDir, analyzedPulse: pulse, showPlot=False):
    """
    Single qubit randomized benchmarking using atomic Clifford pulses. 

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel)
    seqFile : file containing sequence strings
    showPlot : whether to plot (boolean)
    """

    # Original:
    # # Setup a pulse library
    # pulseLib = [AC(qubit, cliffNum) for cliffNum in range(24)]
    # pulseLib.append(analyzedPulse)
    # measBlock = MEAS(qubit)

    # seqs = []
    # for ct in range(10):
    #     fileName = 'RBT_Seqs_fast_{0}_F1.txt'.format(ct+1)
    #     tmpSeqs = []
    #     with open(os.path.join(seqFileDir, fileName),'r') as FID:
    #         fileReader = reader(FID)
    #         for pulseSeqStr in fileReader:
    #             seq = []
    #             for pulseStr in pulseSeqStr:
    #                 seq.append(pulseLib[int(pulseStr)-1])
    #             seq.append(measBlock)
    #             tmpSeqs.append(seq)
    #         seqs += tmpSeqs[:12]*12 + tmpSeqs[12:-12] + tmpSeqs[-12:]*12

    # seqsPerFile = 100
    # numFiles = len(seqs)//seqsPerFile

    # for ct in range(numFiles):
    #     chunk = seqs[ct*seqsPerFile:(ct+1)*seqsPerFile]
    #     # Tack on the calibration scalings
    #     numCals = 4
    #     chunk += [[Id(qubit), measBlock]]*numCals + [[X(qubit), measBlock]]*numCals
    #     fileNames = compile_to_hardware(chunk, 'RBT/RBT', suffix='_{0}'.format(ct+1))

    # if showPlot:
    #     plot_pulse_files(fileNames)

    # FIXME: How do we tell the compiler this should return a list of pulses?
    @qgl2decl
    def doACPulse(qubit: qbit, cliffNum) -> pulse:
        if cliffNum == 24:
            analyzedPulse
        elif cliffNum > 24:
            raise Exception("Max cliffNum 24, got %d" % cliffNum)
        else: 
            AC(qubit, cliffNum)

    pulseSeqStrs = []
    for ct in range(10):
        fileName = 'RBT_Seqs_fast_{0}_F1.txt'.format(ct+1)
        tmpSeqs = []
        with open(os.path.join(seqFileDir, fileName),'r') as FID:
            fileReader = reader(FID)
            for pulseSeqStr in fileReader:
                tmpSeqs.append(pulseSeqStr)
            pulseSeqStrs = tmpSeqs[:12]*12 + tmpSeqs[12:-12] + tmpSeqs[-12:]*12

    numSeqs = len(pulseSeqStrs)
    seqsPerFile = 100
    numFiles = numSeqs//seqsPerFile
    numCals = 4

    # FIXME: How do we tell the compiler this should return a sequence of pulses?
    @qgl2decl
    def getPulseSeq(qubit: qbit, pulseSeqStr) -> pulse:
        init(qubit)
        for pulseStr in pulseSeqStr:
            doACPulse(qubit, int(pulseStr))
        MEAS(qubit)

    for ct in range(numFiles):
        for s in range(seqsPerFile):
            init(qubit)
            seqStr = pulseSeqStrs[ct*seqsPerFile+s]
            getPulseSeq(qubit, seqStr)
        # Add numCals calibration scalings
        for _ in range(numCals):
            init(qubit)
            Id(qubit)
            MEAS(qubit)

            init(qubit)
            X(qubit)
            MEAS(qubit)
        # FIXME: Then magically get the sequences here....
        # This needs to get refactored....
        fileNames = compile_to_hardware([], 'RBT/RBT',
                                        suffix='_{0}'.format(ct+1), qgl2=True)

    if showPlot:
        plot_pulse_files(fileNames)

@qgl2decl
def SimultaneousRB_AC(qubits: qbit_list, seqs, showPlot=False):
    """
    Simultaneous randomized benchmarking on multiple qubits using atomic Clifford pulses. 

    Parameters
    ----------
    qubits : iterable of logical channels to implement seqs on (list or tuple) 
    seqs : a tuple of sequences created for each qubit in qubits
    showPlot : whether to plot (boolean)

    Example
    -------
    >>> q1 = QubitFactory('q1')
    >>> q2 = QubitFactory('q2')
    >>> seqs1 = create_RB_seqs(1, [2, 4, 8, 16])
    >>> seqs2 = create_RB_seqs(1, [2, 4, 8, 16])
    >>> SimultaneousRB_AC((q1, q2), (seqs1, seqs2), showPlot=False)
    """
    # Original:
    # seqsBis = []
    # for seq in zip(*seqs):
    #     seqsBis.append([reduce(operator.__mul__, [AC(q,c) for q,c in zip(qubits,
    #                                                                      pulseNums)]) for pulseNums in zip(*seq)])

    # # Add the measurement to all sequences
    # for seq in seqsBis:
    #     seq.append(reduce(operator.mul, [MEAS(q) for q in qubits]))

    # # Tack on the calibration sequences
    # seqsBis += create_cal_seqs((qubits), 2)

    # fileNames = compile_to_hardware(seqsBis, 'RB/RB')
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)

    for seq in zip(*seqs):
        # Start sequence
        with concur:
            for q in qubits:
                init(q)
        for pulseNums in zip(*seq):
            with concur:
                for q,c in zip(qubits, pulseNums):
                    AC(q,c)
        # Measure at end of each sequence
        with concur:
            for q in qubits:
                MEAS(q)

    # Tack on calibration
    create_cal_seqs((qubits), 2)

    # QGL2 compiler must supply missing list of sequences argument
    compileAndPlot('RB/RB', showPlot)

# Imports for testing only
from qgl2.qgl2 import qgl2main
from QGL.Channels import Qubit, LogicalMarkerChannel, Measurement, Edge
from QGL import ChannelLibrary
from qgl2.qgl1 import Qubit, QubitFactory
import numpy as np
from math import pi
import random

@qgl2main
def main():
    # Set up 2 qbits, following model in QGL/test/test_Sequences

    # FIXME: Cannot use these in current QGL2 compiler, because
    # a: QGL2 doesn't understand creating class instances, and 
    # b: QGL2 currently only understands the fake Qbits
#    qg1 = LogicalMarkerChannel(label="q1-gate")
#    q1 = Qubit(label='q1', gateChan=qg1)
#    q1.pulseParams['length'] = 30e-9
#    q1.pulseParams['phase'] = pi/2
#    qg2 = LogicalMarkerChannel(label="q2-gate")
#    q2 = Qubit(label='q2', gateChan=qg2)
#    q2.pulseParams['length'] = 30e-9
#    q2.pulseParams['phase'] = pi/2

#    sTrig = LogicalMarkerChannel(label='slaveTrig')
#    dTrig = LogicalMarkerChannel(label='digitizerTrig')
#    Mq1gate = LogicalMarkerChannel(label='M-q1-gate')
#    m1 = Measurement(label='M-q1', gateChan = Mq1gate, trigChan = dTrig)
#    Mq2gate = LogicalMarkerChannel(label='M-q2-gate')
#    m2 = Measurement(label='M-q2', gateChan = Mq2gate, trigChan = dTrig)

    # this block depends on the existence of q1 and q2
#    crgate = LogicalMarkerChannel(label='cr-gate')

#    cr = Edge(label="cr", source = q1, target = q2, gateChan = crgate )
#    cr.pulseParams['length'] = 30e-9
#    cr.pulseParams['phase'] = pi/4

#    mq1q2g = LogicalMarkerChannel(label='M-q1q2-gate')
#    m12 = Measurement(label='M-q1q2', gateChan = mq1q2g, trigChan=dTrig)

#    ChannelLibrary.channelLib = ChannelLibrary.ChannelLibrary()
#    ChannelLibrary.channelLib.channelDict = {
#        'q1-gate': qg1,
#        'q1': q1,
#        'q2-gate': qg2,
#        'q2': q2,
#        'cr-gate': crgate,
#        'cr': cr,
#        'slaveTrig': sTrig,
#        'digitizerTrig': dTrig,
#        'M-q1': m1,
#        'M-q1-gate': Mq1gate,
#        'M-q2': m2,
#        'M-q2-gate': Mq2gate,
#        'M-q1q2-gate': mq1q2g,
#        'M-q1q2': m12
#    }
#    ChannelLibrary.channelLib.build_connectivity_graph()

    # Use stub Qubits, but comment this out when running directly.
    q1 = QubitFactory("q1")
    q2 = QubitFactory("q2")

    np.random.seed(20152606) # set seed for create_RB_seqs()
    random.seed(20152606) # set seed for random.choice()
    SingleQubitRB(q1, create_RB_seqs(1, 2**np.arange(1,7)))

    # For some reason this only works if I reverse the 2 qubit args
    # q2 then q1. Why?
    # The original unit test had this commeent:
    """  Fails on APS1, APS2, and Tek7000 due to:
    File "QGL\PatternUtils.py", line 129, in add_gate_pulses
    if has_gate(chan) and not pulse.isZero and not (chan.gateChan
    AttributeError: 'CompositePulse' object has no attribute 'isZero'
    """
    np.random.seed(20152606) # set seed for create_RB_seqs()
    TwoQubitRB(q2, q1, create_RB_seqs(2, [2, 4, 8, 16, 32], repeats=16))

    np.random.seed(20151709) # set seed for create_RB_seqs
    seqs1 = create_RB_seqs(1, 2**np.arange(1,7))
    seqs2 = create_RB_seqs(1, 2**np.arange(1,7))
    SimultaneousRB_AC((q1, q2), (seqs1, seqs2))

    np.random.seed(20152606) # set seed for create_RB_seqs
    SingleQubitRB_AC(q1,create_RB_seqs(1, 2**np.arange(1,7)))

#    SingleQubitIRB_AC(q1,'')

#    SingleQubitRBT(q1,'')

if __name__ == "__main__":
    main()
