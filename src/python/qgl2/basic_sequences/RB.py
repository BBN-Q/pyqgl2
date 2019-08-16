# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qreg, pulse, sequence

from qgl2.qgl1 import MEAS, Id, X, AC, clifford_seq, Y90m, X90
from pyqgl2.qreg import QRegister

# FIXME: RB uses Cliffords. Importing all of QGL.Cliffords forces QGL2
# to read more of QGL than we want. Redo Cliffords in QGL2 with QGL1 stubs where needed

# from QGL.Cliffords import clifford_seq, clifford_mat, inverse_clifford
from QGL.CliffordsBare import clifford_mat, inverse_clifford

from qgl2.basic_sequences.helpers import create_cal_seqs, measConcurrently

from qgl2.util import init

from csv import reader
from functools import reduce
import operator
import os

import numpy as np

# This is not pulses, just math; so this is just the original
def create_RB_seqs(numQubits, lengths, repeats=32, interleaveGate=None, recovery=True):
    """
    Create a list of lists of Clifford gates to implement RB.
    """
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
        seqs += np.random.randint(0, cliffGroupSize,
                                  size=(repeats, length-1)).tolist()

    # Possibly inject the interleaved gate
    if interleaveGate:
        newSeqs = []
        for seq in seqs:
            newSeqs.append(np.vstack((np.array(
                seq, dtype=np.int), interleaveGate*np.ones(
                    len(seq), dtype=np.int))).flatten(order='F').tolist())
        seqs = newSeqs

    if recovery:
        # Calculate the recovery gate
        for seq in seqs:
            if len(seq) == 1:
                mat = clifford_mat(seq[0], numQubits)
            else:
                mat = reduce(lambda x,y: np.dot(y,x), [clifford_mat(c, numQubits) for c in seq])
            seq.append(inverse_clifford(mat))

    return seqs

@qgl2decl
def SingleQubitRB(qubit: qreg, seqs, purity=False, add_cals=True):
    """
    Single qubit randomized benchmarking using 90 and 180 generators. 

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel)
    seqs : list of lists of Clifford group integers
    """
    # Original:
    # seqsBis = []
    # op = [Id(qubit, length=0), Y90m(qubit), X90(qubit)]
    # for ct in range(3 if purity else 1):
    #   for seq in seqs:
    #     seqsBis.append(reduce(operator.add, [clifford_seq(c, qubit) for c in seq]))

    #     #append tomography pulse to measure purity
    #     seqsBis[-1].append(op[ct])
    #     # Add the measurement to all sequences
    #     seqsBis[-1].append(MEAS(qubit))

    # # Tack on the calibration sequences
    # if add_cals:
    #   seqsBis += create_cal_seqs((qubit,), 2)

#    axis_descriptor = [{
#        'name': 'length',
#        'unit': None,
#        'points': list(map(len, seqs)),
#        'partition': 1
#    }]
#    metafile = compile_to_hardware(seqsBis, 'RB/RB', axis_descriptor = axis_descriptor, extra_meta = {'sequences':seqs})


    # seqs are result of create_RB_seqs: list of lists of integers
    # clifford_seq() returns a sequence of pulses itself
    # [clifford_seq() for c in seq]
    #   gives a list of len(seq) sequences
    # reduce(operator.add, listOfSequences)
    #   gives a single sequence of all the elements in listOfSequences
    # So the first for loop creates a single list of sequences

    ops = [Id]
    if purity:
        ops = [Id, Y90m, X90]
    for op in ops:
        for seq in seqs:
            init(qubit)
            for c in seq:
                clifford_seq(c, qubit)
            # append tomography pulse to measure purity
            if op == Id:
                op(qubit, length=0)
            else:
                op(qubit)
            # append measurement
            MEAS(qubit)

    if add_cals:
        # Tack on calibration sequences
        create_cal_seqs(qubit, 2)

@qgl2decl
def TwoQubitRB(q1: qreg, q2: qreg, seqs, add_cals=True):
    """
    Two qubit randomized benchmarking using 90 and 180 single qubit generators and ZX90 

    Parameters
    ----------
    q1,q2 : logical channels to implement sequence (LogicalChannel)
    seqs : list of lists of Clifford group integers
    """

    # Original:
    # seqsBis = []
    # for seq in seqs:
    #     seqsBis.append(reduce(operator.add, [clifford_seq(c, q1, q2) for c in seq]))

    # # Add the measurement to all sequences
    # for seq in seqsBis:
    #     seq.append(MEAS(q1, q2))

    # # Tack on the calibration sequences
    # if add_cals:
    #   seqsBis += create_cal_seqs((q1,q2), 2)

#    axis_descriptor = [{
#        'name': 'length',
#        'unit': None,
#        'points': list(map(len, seqs)),
#        'partition': 1
#    }]
#    metafile = compile_to_hardware(seqsBis, 'RB/RB', axis_descriptor = axis_descriptor, suffix = suffix, extra_meta = {'sequences':seqs})

    bothQs = QRegister(q1, q2)
    for seq in seqs:
        init(bothQs)
        for c in seq:
            clifford_seq(c, q2, q1)
        measConcurrently(bothQs)

    # Tack on the calibration sequences
    if add_cals:
        create_cal_seqs((q1, q2), 2)

@qgl2decl
def SingleQubitRB_AC(qubit: qreg, seqs, purity=False, add_cals=True):
    """
    Single qubit randomized benchmarking using atomic Clifford pulses. 

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel)
    seqFile : file containing sequence strings
    """

    # Original:
    # seqsBis = []
    # op = [Id(qubit, length=0), Y90m(qubit), X90(qubit)]
    # for ct in range(3 if purity else 1):
    #   for seq in seqs:
    #     seqsBis.append([AC(qubit, c) for c in seq])
    #     #append tomography pulse to measure purity
    #     seqsBis[-1].append(op[ct])
    #     #append measurement
    #     seqsBis[-1].append(MEAS(qubit))

    # # Tack on the calibration sequences
    # if add_cals:
    #   seqsBis += create_cal_seqs((qubit,), 2)

#    axis_descriptor = [{
#        'name': 'length',
#        'unit': None,
#        'points': list(map(len, seqs)),
#        'partition': 1
#    }]
#    metafile = compile_to_hardware(seqsBis, 'RB/RB', axis_descriptor = axis_descriptor, extra_meta = {'sequences':seqs})

    # AC() gives a single pulse on qubit

    op = [Id, Y90m, X90]
    for ct in range(3 if purity else 1):
        for seq in seqs:
            init(qubit)
            for c in seq:
                AC(qubit, c)
            # append tomography pulse to measure purity
            if ct == 1:
                op[ct](qubit, length=0)
            else:
                op[ct](qubit)
            # append measurement
            MEAS(qubit)

    if add_cals:
        # Tack on calibration sequences
        create_cal_seqs(qubit, 2)

@qgl2decl
def SingleQubitRB_DiAC(qubit, seqs, compiled=True, purity=False, add_cals=True):
    """Single qubit randomized benchmarking using diatomic Clifford pulses.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel)
    seqFile : file containing sequence strings
    compiled : if True, compile Z90(m)-X90-Z90(m) to Y90(m) pulses
    purity : measure <Z>,<X>,<Y> of final state, to measure purity. See J.J.
        Wallman et al., New J. Phys. 17, 113020 (2015)
    """
    op = [Id, Y90m, X90]
    for ct in range(3 if purity else 1):
        for seq in seqs:
            init(qubit)
            for c in seq:
                DiAC(qubit, c, compiled)
            # append tomography pulse to measure purity
            if ct == 1:
                op[ct](qubit, length=0)
            else:
                op[ct](qubit)
            # append measurement
            MEAS(qubit)

#    axis_descriptor = [{
#        'name': 'length',
#        'unit': None,
#        'points': list(map(len, seqs)),
#        'partition': 1
#    }]

    # Tack on the calibration sequences
    if add_cals:
        for _ in range(2):
            init(qubit)
            Id(qubit)
            MEAS(qubit)
        for _ in range(2):
            init(qubit)
            X90(qubit)
            X90(qubit)
            MEAS(qubit)
#        axis_descriptor.append(cal_descriptor((qubit,), 2))

#    metafile = compile_to_hardware(seqsBis, 'RB_DiAC/RB_DiAC', axis_descriptor = axis_descriptor, extra_meta = {'sequences':seqs})


@qgl2decl
def doACPulse(qubit: qreg, cliffNum) -> sequence:
    if cliffNum == 24:
        cliffNum = 0
    if cliffNum > 24:
        raise Exception("Max cliffNum 24, got %d" % cliffNum)
    AC(qubit, cliffNum)

@qgl2decl
def getPulseSeq(qubit: qreg, pulseSeqStr) -> sequence:
    init(qubit)
    for pulseStr in pulseSeqStr:
        doACPulse(qubit, int(pulseStr))
    MEAS(qubit)

@qgl2decl
def SingleQubitIRB_AC(qubit: qreg, seqFile):
    """
    Single qubit interleaved randomized benchmarking using atomic Clifford pulses. 

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel)
    seqFile : file containing sequence strings
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

    pulseSeqStrs = []
    with open(seqFile, 'r') as FID:
        fileReader = reader(FID)
        # each line in the file is a sequence, but I don't know how many that is
        for pulseSeqStr in fileReader:
            pulseSeqStrs.append(pulseSeqStr)
    numSeqs = len(pulseSeqStrs)

    # Hack for limited APS waveform memory and break it up into multiple files
    # We've shuffled the sequences so that we loop through each gate length on the inner loop
    numRandomizations = 36
    fileNames = []
    for ct in range(numRandomizations):
        doCt = ct
        isOne = True
        while doCt < numSeqs:
            getPulseSeq(qubit, pulseSeqStrs[doCt])

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
            # We need to split creating seqs from c_to_h
#            fileNames = compile_to_hardware([], 'RB/RB',
#                                            suffix='_{0}'.format(2*ct+1+1*(not
#                                                                           isOne)),
#                                            qgl2=True)

            doCt += numRandomizations
            isOne = not isOne

@qgl2decl
def SingleQubitRBT(qubit: qreg, seqFileDir, analyzedPulse: pulse, add_cals=True):
    """	Single qubit randomized benchmarking tomography using atomic Clifford pulses.

    This relies on specific sequence files and is here for historical purposes only.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel)
    seqFile : file containing sequence strings
    analyzedPulse : specific pulse to analyze
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
    #     if add_cals:
    #       numCals = 4
    #       chunk += [[Id(qubit), measBlock]]*numCals + [[X(qubit), measBlock]]*numCals
    #     fileNames = compile_to_hardware(chunk, 'RBT/RBT', suffix='_{0}'.format(ct+1))

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

    for ct in range(numFiles):
        for s in range(seqsPerFile):
            init(qubit)
            seqStr = pulseSeqStrs[ct*seqsPerFile+s]
            getPulseSeq(qubit, seqStr)
        if add_cals:
            # Add numCals calibration scalings
            for _ in range(numCals):
                init(qubit)
                Id(qubit)
                MEAS(qubit)

                init(qubit)
                X(qubit)
                MEAS(qubit)
#        # FIXME: Then magically get the sequences here....
#        # This needs to get refactored....
#        # We need to split creating seqs from c_to_h
#        fileNames = compile_to_hardware([], 'RBT/RBT',
#                                        suffix='_{0}'.format(ct+1), qgl2=True)

@qgl2decl
def SimultaneousRB_AC(qubits: qreg, seqs, add_cals=True):
    """
    Simultaneous randomized benchmarking on multiple qubits using atomic Clifford pulses. 

    Parameters
    ----------
    qubits : QRegister of logical channels to implement seqs on
    seqs : a tuple of sequences created for each qubit in qubits

    Example
    -------
    >>> q1 = QubitFactory('q1')
    >>> q2 = QubitFactory('q2')
    >>> seqs1 = create_RB_seqs(1, [2, 4, 8, 16])
    >>> seqs2 = create_RB_seqs(1, [2, 4, 8, 16])
    >>> qr = QRegister(q1, q2)
    >>> SimultaneousRB_AC(qr, (seqs1, seqs2))
    """
    # Original:
    # seqsBis = []
    # for seq in zip(*seqs):
    #     seqsBis.append([reduce(operator.__mul__, [AC(q,c) for q,c in zip(qubits,
    #                                                                      pulseNums)]) for pulseNums in zip(*seq)])

    # # Add the measurement to all sequences
    # for seq in seqsBis:
    #     seq.append(reduce(operator.mul, [MEAS(q) for q in qubits]))

#    axis_descriptor = [{
#        'name': 'length',
#        'unit': None,
#        'points': list(map(len, seqs)),
#        'partition': 1
#    }]

    # # Tack on the calibration sequences
    # if add_cals:
    #   seqsBis += create_cal_seqs((qubits), 2)
    #   axis_descriptor.append(cal_descriptor((qubits), 2))

    # metafile = compile_to_hardware(seqsBis, 'RB/RB', axis_descriptor = axis_descriptor, extra_meta = {'sequences':seqs})

    for seq in zip(*seqs):
        # Start sequence
        init(qubits)
        for pulseNums in zip(*seq):
            Barrier(qubits)
            for q,c in zip(qubits, pulseNums):
                AC(q,c)
        # Measure at end of each sequence
        measConcurrently(qubits)

    if add_cals:
        # Tack on calibration
        create_cal_seqs(qubits, 2)

# A main for running the sequences here with some typical argument values
# Here it runs all of them; could do a parse_args like main.py
def main():
    from pyqgl2.qreg import QRegister
    import pyqgl2.test_cl
    from pyqgl2.main import compile_function, qgl2_compile_to_hardware
    import numpy as np
    import random

    toHW = True
    plotPulses = False
    pyqgl2.test_cl.create_default_channelLibrary(toHW, True)

#    # To turn on verbose logging in compile_function
#    from pyqgl2.ast_util import NodeError
#    from pyqgl2.debugmsg import DebugMsg
#    NodeError.MUTE_ERR_LEVEL = NodeError.NODE_ERROR_NONE
#    DebugMsg.set_level(0)

    # Now compile the QGL2 to produce the function that would generate the expected sequence.
    # Supply the path to the QGL2, the main function in that file, and a list of the args to that function.
    # Can optionally supply saveOutput=True to save the qgl1.py
    # file,
    # and intermediate_output="path-to-output-file" to save
    # intermediate products

    # Pass in QRegister(s) NOT real Qubits
    q1 = QRegister("q1")
    q2 = QRegister("q2")
    qr = QRegister(q1, q2)

    # FIXME: See issue #44: Must supply all args to qgl2main for now

    # Functions here have some extra code to run before running the compiled QGL2,
    # so define functions for those; random number seeding

    def beforeSingleRB():
        np.random.seed(20152606) # set seed for create_RB_seqs()
        random.seed(20152606) # set seed for random.choice()
    # SingleQubitRB(q1, create_RB_seqs(1, 2**np.arange(1,7)))

    # The original unit test had this comment:
    """  Fails on APS1, APS2, and Tek7000 due to:
    File "QGL/PatternUtils.py", line 129, in add_gate_pulses
    if has_gate(chan) and not pulse.isZero and not (chan.gate_chan
    AttributeError: 'CompositePulse' object has no attribute 'isZero'
    """
    def beforeTwoRB():
        np.random.seed(20152606) # set seed for create_RB_seqs()
    # TwoQubitRB(q2, q1, create_RB_seqs(2, [2, 4, 8, 16, 32], repeats=16))

    def beforeSimRBAC():
        np.random.seed(20151709) # set seed for create_RB_seqs
        #seqs1 = create_RB_seqs(1, 2**np.arange(1,7))
        #seqs2 = create_RB_seqs(1, 2**np.arange(1,7))
    # SimultaneousRB_AC((q1, q2), (seqs1, seqs2))

    def beforeSingleRBAC():
        np.random.seed(20152606) # set seed for create_RB_seqs
    # SingleQubitRB_AC(q1,create_RB_seqs(1, 2**np.arange(1,7)))

# FIXME: Add test of SingleQubitRB_DiAC

#    for func, args, label, beforeFunc in [("SingleQubitRB", (q1, create_RB_seqs(1, 2**np.arange(1,7))), "RB", beforeSingleRB),
#                              ("TwoQubitRB", (q1, q2, create_RB_seqs(2, [2, 4, 8, 16, 32], repeats=16)), "RB", beforeTwoRB),
#                              ("SimultaneousRB_AC", (q1, q2, (create_RB_seqs(1, 2**np.arange(1,7)), create_RB_seqs(1, 2**np.arange(1,7)))), "RB", beforeSimRBAC),
#                              ("SingleQubitRB_AC", (q1,create_RB_seqs(1, 2**np.arange(1,7))), "RB", beforeSingleRBAC),
#                              ("SingleQubitIRB_AC", (q1,''), "RB"),
# Comment says this relies on a specific file, so don't bother running
#                              ("SingleQubitRBT", (q1,'', fixmePulse), "RBT"),
#                          ]:

    for func, args, label, beforeFunc in [("SingleQubitRB", (q1, create_RB_seqs(1, 2**np.arange(1,7)), False, True), "RB", beforeSingleRB),
                              ("TwoQubitRB", (q1, q2, create_RB_seqs(2, [2, 4, 8, 16, 32], repeats=16), True), "RB", beforeTwoRB),
#                              ("SingleQubitRB_AC", (q1,create_RB_seqs(1, 2**np.arange(1,7)), False, True), "RB", beforeSingleRBAC),
#                              ("SimultaneousRB_AC", (q1, q2, (create_RB_seqs(1, 2**np.arange(1,7)), create_RB_seqs(1, 2**np.arange(1,7))), True), "RB", beforeSimRBAC),
#                              ("SingleQubitIRB_AC", (q1,''), "RB", None),
# Comment says this relies on a specific file, so don't bother running
                              # ("SingleQubitRBT", (q1,'', fixmePulse, True), "RBT", None),
                           ]:

        print(f"\nRun {func}...")

        # This is typically setting random seed
        beforeFunc()

        # Here we know the function is in the current file
        # You could use os.path.dirname(os.path.realpath(__file)) to find files relative to this script,
        # Or os.getcwd() to get files relative to where you ran from. Or always use absolute paths.
        resFunc = compile_function(__file__, func, args)
        # Run the QGL2. Note that the generated function takes no arguments itself
        seq = resFunc()
        if toHW:
            import QGL
            print(f"Compiling {func} sequences to hardware\n")
            # QGL.Compiler.set_log_level()
            fileNames = qgl2_compile_to_hardware(seq, f'{label}/{label}')
            print(f"Compiled sequences; metafile = {fileNames}")
            if plotPulses:
                from QGL.PulseSequencePlotter import plot_pulse_files
                # FIXME: As called, this returns a graphical object to display
                plot_pulse_files(fileNames)
        else:
            print(f"\nGenerated {func} sequences:\n")
            from QGL.Scheduler import schedule

            scheduled_seq = schedule(seq)
            from IPython.lib.pretty import pretty
            print(pretty(scheduled_seq))

if __name__ == "__main__":
    main()
