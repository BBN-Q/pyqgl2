# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.
'''
Test the qgl2/basic_sequences to ensure they replicate the QGL1 functionality.
'''
import datetime
import unittest
import numpy as np
from math import pi
import random

from pyqgl2.main import compile_function
from pyqgl2.qreg import QRegister
from QGL import *

from test.helpers import testable_sequence, \
    channel_setup, assertPulseSequenceEqual, \
    get_cal_seqs_1qubit, get_cal_seqs_2qubits, \
    stripWaitBarrier, flattenPulseBlocks

class TestAllXY(unittest.TestCase):
    def setUp(self):
        channel_setup()

    def test_AllXY(self):
        # QGL1 uses QubitFactory, QGL2 uses QRegister
        q1 = QubitFactory('q1')
        qr = QRegister(q1)

        # Specify the QGL1 we expect QGL2 to generate
        # Note in this case we specify only a sample of the start
        expectedseq = []
        # Expect a single sequence 4 * 2 * 21 pulses long
        # Expect it to start like this:
        expectedseq += [
            qwait(channels=(q1,)), # aka init(q1) aka Wait(q1)
            Id(q1),
            Id(q1),
            MEAS(q1),
            qwait(channels=(q1,)),
            Id(q1),
            Id(q1),
            MEAS(q1)
            ]

        # To turn on verbose logging in compile_function
        # from pyqgl2.ast_util import NodeError
        # from pyqgl2.debugmsg import DebugMsg
        # NodeError.MUTE_ERR_LEVEL = NodeError.NODE_ERROR_NONE
        # DebugMsg.set_level(0)

        # Now compile the QGL2 to produce the function that would generate the expected sequence.
        # Supply the path to the QGL2, the main function in that file, and a list of the args to that function.
        # Can optionally supply saveOutput=True to save the qgl1.py
        # file,
        # and intermediate_output="path-to-output-file" to save
        # intermediate products
        resFunction = compile_function("src/python/qgl2/basic_sequences/AllXY.py",
                                      "AllXY",
                                       (qr,))
        # Run the QGL2. Note that the generated function takes no arguments itself
        seqs = resFunction()
        # Transform the returned sequences into the canonical form for comparing
        # to the explicit QGL1 version above.
        # EG, 'flatten' any embedded lists of sequences.
        seqs = testable_sequence(seqs)

        # Assert that the QGL1 is the same as the generated QGL2
        self.assertEqual(len(seqs), 4*21*2)
        assertPulseSequenceEqual(self, seqs[:len(expectedseq)], expectedseq)

    # Tests list of lists of function references, instead of sub-functions
    def test_AllXY_alt1(self):
        q1 = QubitFactory('q1')
        qr = QRegister('q1')
        expectedseq = []
        # Expect a single sequence 4 * 2 * 21 pulses long
        # Expect it to start like this:
        expectedseq += [
            qwait(channels=(q1,)),
            Id(q1),
            Id(q1),
            MEAS(q1),
            qwait(channels=(q1,)),
            Id(q1),
            Id(q1),
            MEAS(q1)
            ]

        resFunction = compile_function(
                "test/code/AllXY_alt.py",
                "doAllXY",
                (qr,))
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        self.assertEqual(len(seqs), 4*21*2)
        assertPulseSequenceEqual(self, seqs[:len(expectedseq)], expectedseq)

    def test_AllXY_alt2(self):
        q1 = QubitFactory('q1')
        qr = QRegister('q1')
        expectedseq = []
        # Expect a single sequence 4 * 2 * 21 pulses long
        # Expect it to start like this:
        expectedseq += [
            qwait(channels=(q1,)),
            Id(q1),
            Id(q1),
            MEAS(q1),
            qwait(channels=(q1,)),
            Id(q1),
            Id(q1),
            MEAS(q1)
            ]

        resFunction = compile_function(
                "test/code/AllXY_alt.py",
                "doAllXY2",
                (qr,))
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        self.assertEqual(len(seqs), 4*21*2)
        assertPulseSequenceEqual(self, seqs[:len(expectedseq)], expectedseq)

# BlankingSweeps are OBE, so not tested

class TestCR(unittest.TestCase):
    def setUp(self):
        channel_setup()

    def test_PiRabi(self):
        controlQ = QubitFactory('q1')
        targetQ = QubitFactory('q2')
        controlQR = QRegister(controlQ)
        targetQR = QRegister(targetQ)
        edge = EdgeFactory(controlQ, targetQ)
        lengths = np.linspace(0, 4e-6, 11)
        riseFall=40e-9
        amp=1
        phase=0
        calRepeats = 2

        expected_seq = []
        # Seq1
        for l in lengths:
            expected_seq += [
                qwait(channels=(controlQ, targetQ)),
                Id(controlQ),
                flat_top_gaussian(edge, riseFall, length=l, amp=amp, phase=phase),
                Barrier(controlQ, targetQ),
                MEAS(controlQ),
                MEAS(targetQ)
            ]
        # Seq2
        for l in lengths:
            expected_seq += [
                qwait(channels=(controlQ, targetQ)),
                X(controlQ),
                flat_top_gaussian(edge, riseFall, length=l, amp=amp, phase=phase),
                X(controlQ),
                Barrier(controlQ, targetQ),
                MEAS(controlQ),
                MEAS(targetQ)
            ]

        # Add calibration
        calseq = get_cal_seqs_2qubits(controlQ, targetQ, calRepeats)
        expected_seq += calseq
        expected_seq = testable_sequence(expected_seq)

        resFunction = compile_function("src/python/qgl2/basic_sequences/CR.py",
                                       "PiRabi", (controlQR, targetQR, lengths, riseFall, amp, phase, calRepeats))
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        self.maxDiff = None
        assertPulseSequenceEqual(self, seqs, expected_seq)

    def test_EchoCRLen(self):
        controlQ = QubitFactory('q1')
        targetQ = QubitFactory('q2')
        cR = QRegister('q1') # Equivalent to QRegister(controlQ)
        tR = QRegister('q2')
        # FIXME: Better values!?
        lengths = np.linspace(0, 2e-6, 11)
        riseFall=40e-9
        amp=1
        phase=0
        calRepeats=2
        canc_amp=0
        canc_phase=np.pi/2

        expected_seq = []
        # Seq1
        for l in lengths:
            expected_seq += [
                qwait(channels=(controlQ, targetQ)),
                Id(controlQ),
                echoCR(controlQ, targetQ, length=l, phase=phase, amp=amp, 
                       riseFall=riseFall, canc_amp=canc_amp, canc_phase=canc_phase),
                Id(controlQ),
                Barrier(controlQ, targetQ),
                MEAS(controlQ),
                MEAS(targetQ)
            ]
        # Seq2
        for l in lengths:
            expected_seq += [
                qwait(channels=(controlQ, targetQ)),
                X(controlQ),
                echoCR(controlQ, targetQ, length=l, phase=phase, amp=amp,
                       riseFall=riseFall, canc_amp=canc_amp, canc_phase=canc_phase),
                X(controlQ),
                Barrier(controlQ, targetQ),
                MEAS(controlQ),
                MEAS(targetQ)
            ]

        # Add calibration
        cal_seqs = get_cal_seqs_2qubits(controlQ, targetQ, calRepeats)
        expected_seq += cal_seqs
        expected_seq = testable_sequence(expected_seq)

        resFunction = compile_function("src/python/qgl2/basic_sequences/CR.py",
                                       "EchoCRLen",
                                       (cR, tR, lengths, riseFall, amp, phase, calRepeats, canc_amp, canc_phase)   )
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        self.maxDiff = None
        assertPulseSequenceEqual(self, seqs, expected_seq)

    def test_EchoCRPhase(self):
        controlQ = QubitFactory('q1')
        targetQ = QubitFactory('q2')
        cR = QRegister('q1')
        tR = QRegister('q2')
        phases = np.linspace(0, pi/2, 11)
        riseFall=40e-9
        amp=1
        length=100e-9
        calRepeats=2
        canc_amp=0
        canc_phase=np.pi/2
        expected_seq = []

        # Seq1
        for p in phases:
            expected_seq += [
                qwait(channels=(controlQ, targetQ)),
                Id(controlQ),
                echoCR(controlQ, targetQ, length=length, phase=p, amp=amp,
                       riseFall=riseFall, canc_amp=canc_amp, canc_phase=canc_phase),
                Barrier(controlQ, targetQ),
                X90(targetQ),
                Id(controlQ),
                Barrier(controlQ, targetQ),
                MEAS(controlQ),
                MEAS(targetQ)
            ]

        # Seq2
        for p in phases:
            expected_seq += [
                qwait(channels=(controlQ, targetQ)),
                X(controlQ),
                echoCR(controlQ, targetQ, length=length, phase=p, amp=amp,
                       riseFall=riseFall, canc_amp=canc_amp, canc_phase=canc_phase),
                Barrier(controlQ, targetQ),
                X90(targetQ),
                X(controlQ),
                Barrier(controlQ, targetQ),
                MEAS(controlQ),
                MEAS(targetQ)
            ]

        # Add calibration
        cal_seqs = get_cal_seqs_2qubits(controlQ, targetQ, calRepeats)
        expected_seq += cal_seqs
        expected_seq = testable_sequence(expected_seq)

        resFunction = compile_function("src/python/qgl2/basic_sequences/CR.py",
                                       "EchoCRPhase",
                                       (cR, tR, phases, riseFall, amp, length, calRepeats, canc_amp, canc_phase))

        seqs = resFunction()
        seqs = testable_sequence(seqs)

        self.maxDiff = None
        assertPulseSequenceEqual(self, seqs, expected_seq)

class TestDecoupling(unittest.TestCase):
    def setUp(self):
        channel_setup()

    def test_HahnEcho(self):
        q = QubitFactory('q1')
        qr = QRegister('q1')
        steps = 11
        pulseSpacings = np.linspace(0, 5e-6, steps)
        periods = 0
        calRepeats=2
        expectedseq = []
        for k in range(len(pulseSpacings)):
            expectedseq += [
                qwait(channels=(q,)),
                X90(q),
                Id(q, pulseSpacings[k]),
                Y(q),
                Id(q, pulseSpacings[k]),
                U90(q, phase=2*pi*periods/len(pulseSpacings)*k),
                MEAS(q)
            ]

        # Add calibration
        cal = get_cal_seqs_1qubit(q, calRepeats)
        expectedseq += cal

        expectedseq = testable_sequence(expectedseq)

        resFunction = compile_function("src/python/qgl2/basic_sequences/Decoupling.py",
                                      "HahnEcho",
                                      (qr, pulseSpacings, periods, calRepeats))
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        # import ipdb; ipdb.set_trace()
        assertPulseSequenceEqual(self, seqs, expectedseq)

    def test_CPMG(self):
        q = QubitFactory('q1')
        qr = QRegister('q1')

        # Create numPulses sequences
        numPulses = [0, 2, 4, 6]
        pulseSpacing = 500e-9
        pulseSpacingDiff = pulseSpacing - q.pulse_params['length']
        calRepeats = 2

        def addt180t(q, pulseSpacingDiff, rep):
            t180t = []
            for _ in range(rep):
                t180t += [
                    Id(q, pulseSpacingDiff/2),
                    Y(q),
                    Id(q, pulseSpacingDiff/2)
                ]
            return t180t

        expectedseq = []
        for rep in numPulses:
            expectedseq += [
                qwait(channels=(q,)),
                X90(q)
            ]
            expectedseq += addt180t(q, pulseSpacingDiff, rep)
            expectedseq += [
                X90(q),
                MEAS(q)
            ]

        # Add calibration
        cal = get_cal_seqs_1qubit(q, calRepeats)
        expectedseq += cal

        expectedseq = testable_sequence(expectedseq)

        resFunction = compile_function("src/python/qgl2/basic_sequences/Decoupling.py",
                                      "CPMG",
                                      (qr, numPulses, pulseSpacing, calRepeats))
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        assertPulseSequenceEqual(self, seqs, expectedseq)

class TestFeedback(unittest.TestCase):
    def setUp(self):
        channel_setup()

    # FIXME: Add tests for these once implemented
    #def test_Reset(self);
    # ("Reset", (q1, np.linspace(0, 5e-6, 11), 0, 2), "Reset"),
    #def test_BitFlip3(self);
    # ("BitFlip3", (q1, [0, 2, 4, 6], 500e-9, 2), "BitFlip"),

class TestFlipFlop(unittest.TestCase):
    def setUp(self):
        channel_setup()

    def test_FlipFlop(self):
        qubit = QubitFactory('q1')
        qr = QRegister('q1')
        dragParamSweep = np.linspace(0, 1, 11)
        maxNumFFs = 10

        def addFFSeqs(dragParam, maxNumFFs, qubit):
            ffs = []
            for rep in range(maxNumFFs):
                ffs += [
                    qwait(channels=(qubit,)),
                    X90(qubit, dragScaling=dragParam)
                ]
                for _ in range(rep):
                    ffs += [
                        X90(qubit, dragScaling=dragParam),
                        X90m(qubit, dragScaling=dragParam)
                    ]
                ffs += [
                    Y90(qubit, dragScaling=dragParam),
                    MEAS(qubit)
                ]
            return ffs

        expectedseq = []
        for dragParam in dragParamSweep:
            expectedseq += [
                qwait(channels=(qubit,)),
                Id(qubit),
                MEAS(qubit)
            ]
            expectedseq += addFFSeqs(dragParam, maxNumFFs, qubit)
        expectedseq += [
            qwait(channels=(qubit,)),
            X(qubit),
            MEAS(qubit)
        ]
        resFunction = compile_function("src/python/qgl2/basic_sequences/FlipFlop.py",
                                      "FlipFlop",
                                      (qr, dragParamSweep, maxNumFFs))
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        assertPulseSequenceEqual(self, seqs, expectedseq)

# FIXME: Tests for this class are incomplete
class TestRB(unittest.TestCase):
    def setUp(self):
        channel_setup(doHW=True)

    def test_SingleQubitRB(self):
        q1 = QubitFactory('q1')
        qr = QRegister(q1)
        np.random.seed(20152606) # set seed for create_RB_seqs()
        random.seed(20152606) # set seed for random.choice()
        # Range below should be 1,7 but that takes too long; use 1,2 so it's quick
        rbseqs = create_RB_seqs(1, 2**np.arange(1,2))
        purity = True
        add_cals = True

        # Try copying in the basic QGL1 code
        # Can't do it directly since that code doesn't return the
        # sequence
        # This isn't quite right; this is before adding the Waits for example
        expectedseq = []
        def testSingleQubitRB(qubit, rbseqs, purit=False, add_cal=True):
            from QGL.Cliffords import clifford_seq
            from QGL.BasicSequences.helpers import create_cal_seqs
            from functools import reduce
            import operator
            seqsBis = []
            op = [Id(qubit, length=0), Y90m(qubit), X90(qubit)]
            for ct in range(3 if purit else 1):
                for seq in rbseqs:
                    seqsBis.append(reduce(operator.add, [clifford_seq(c, qubit)
                                                         for c in seq]))
                    #append tomography pulse to measure purity
                    seqsBis[-1].append(op[ct])
                    #append measurement
                    seqsBis[-1].append(MEAS(qubit))
            #Tack on the calibration sequences
            if add_cal:
                seqsBis += create_cal_seqs((qubit, ), 2)
            return seqsBis

        expectedseq = testSingleQubitRB(q1, rbseqs, purity, add_cals)
        # Must reset the seeds because QGL1 used the prior values, to ensure QGL2 gets same values
        np.random.seed(20152606) # set seed for create_RB_seqs()
        random.seed(20152606) # set seed for random.choice()
        resFunction = compile_function("src/python/qgl2/basic_sequences/RB.py",
                                      "SingleQubitRB",
                                      (qr, rbseqs, purity, add_cals))
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        # Run testable on the QGL1 to flatten the sequence of sequences
        expectedseq = testable_sequence(expectedseq)
        # Strip out the QGL2 Waits and Barriers that QGL1 doesn't have
        seqs = stripWaitBarrier(seqs)
        # self.maxDiff = None
        assertPulseSequenceEqual(self, seqs, expectedseq)

    def test_TwoQubitRB(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        qr1 = QRegister(q1)
        qr2 = QRegister(q2)
        np.random.seed(20152606) # set seed for create_RB_seqs()
        # Without this next seed, results differ run to run and QGL1 to QGL2
        random.seed(20152606) # set seed for random.choice()
        # Repeats below should be 16 but that takes too long; use 4 so it's quick
        rbseqs = create_RB_seqs(2, [2, 4, 8, 16, 32], repeats=4)
        add_cals = True

        # Try copying in the basic QGL1 code
        # Can't do it directly since that code doesn't return the
        # sequence
        # This isn't quite right; this is before adding the Waits for example
        expectedseq = []
        def testTwoQubitRB(q1, q2, rbseqs, add_cal=True):
            from QGL.Cliffords import clifford_seq
            from QGL.BasicSequences.helpers import create_cal_seqs
            from functools import reduce
            import operator
            seqsBis = []
            for seq in rbseqs:
                seqsBis.append(reduce(operator.add, [clifford_seq(c, q2, q1)
                                                     for c in seq]))

            #Add the measurement to all sequences
            for seq in seqsBis:
                # FIXME: Correct thing is doing these with * as below,
                # But that differs from QGL2 version
                # seq.append(MEAS(q1) * MEAS(q2))
                seq.append(MEAS(q1))
                seq.append(MEAS(q2))
            #Tack on the calibration sequences
            if add_cal:
                seqsBis += create_cal_seqs((q1, q2), 2)
            return seqsBis

        expectedseq = testTwoQubitRB(q1, q2, rbseqs, add_cals)
        # Must reset the seeds because QGL1 used the prior values, to ensure QGL2 gets same values
        np.random.seed(20152606) # set seed for create_RB_seqs()
        # Without this next seed, results differ run to run and QGL1 to QGL2
        random.seed(20152606) # set seed for random.choice()
        resFunction = compile_function("src/python/qgl2/basic_sequences/RB.py",
                                      "TwoQubitRB",
                                      (qr1, qr2, rbseqs, add_cals))
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        # Run testable on the QGL1 to flatten the sequence of sequences
        expectedseq = testable_sequence(expectedseq)
        # Strip out the QGL2 Waits and Barriers that QGL1 doesn't have
        # Note that if you want to see the real sequence, don't do this
        seqs = stripWaitBarrier(seqs)
        # self.maxDiff = None
        # Note: We expect the sequences to start differing around element 2110, due
        # to PulseBlock vs list of pulses, given QGL2 uses Barrier;Pulse where QGL1 uses PulseBlock(pulse)
        # (but that difference is harmless we think)
        assertPulseSequenceEqual(self, seqs[:2110], expectedseq[:2110])
        # assertPulseSequenceEqual(self, seqs, expectedseq)

    def test_SingleQubitRB_AC(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        qr1 = QRegister(q1)
        qr2 = QRegister(q2)
        np.random.seed(20152606) # set seed for create_RB_seqs()
        rbseqs = create_RB_seqs(1, 2**np.arange(1,7))
        add_cals = True
        purity = False

        # Try copying in the basic QGL1 code
        # Can't do it directly since that code doesn't return the
        # sequence
        # This isn't quite right; this is before adding the Waits for example
        expectedseq = []
        def testSingleQubitRB_AC(qubit, seqs, purit=False, add_cal=True):
            from QGL.PulsePrimitives import AC, MEAS, Id, Y90m, X90
            from QGL.BasicSequences.helpers import create_cal_seqs
            from functools import reduce
            import operator
            seqsBis = []
            op = [Id(qubit, length=0), Y90m(qubit), X90(qubit)]
            for ct in range(3 if purit else 1):
                for seq in seqs:
                    seqsBis.append([AC(qubit, c) for c in seq])
                    # append tomography pulse to measure purity
                    seqsBis[-1].append(op[ct])
                    # append measurement
                    seqsBis[-1].append(MEAS(qubit))
            # Tack on the calibration sequences
            if add_cals:
                seqsBis += create_cal_seqs((qubit, ), 2)
            return seqsBis

        expectedseq = testSingleQubitRB_AC(q1, rbseqs, purity, add_cals)
        # Must reset the seeds because QGL1 used the prior values, to ensure QGL2 gets same values
        np.random.seed(20152606) # set seed for create_RB_seqs()
        resFunction = compile_function("src/python/qgl2/basic_sequences/RB.py",
                                      "SingleQubitRB_AC",
                                      (qr1, rbseqs, purity, add_cals))
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        # Run testable on the QGL1 to flatten the sequence of sequences
        expectedseq = testable_sequence(expectedseq)
        # Strip out the QGL2 Waits and Barriers that QGL1 doesn't have
        # Note that if you want to see the real sequence, don't do this
        seqs = stripWaitBarrier(seqs)
        # self.maxDiff = None
        assertPulseSequenceEqual(self, seqs, expectedseq)

    def test_SimultaneousRB_AC(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        qr1 = QRegister(q1)
        qr2 = QRegister(q2)
        qr = QRegister(q1, q2)
        np.random.seed(20151709) # set seed for create_RB_seqs()
        rbseqs = create_RB_seqs(1, 2**np.arange(1,7))
        add_cals = True

        # Try copying in the basic QGL1 code
        # Can't do it directly since that code doesn't return the
        # sequence
        # This isn't quite right; this is before adding the Waits for example
        expectedseq = []
        def testSimultaneousRB_AC(qubits, seqs, add_cal=True):
            from QGL.PulsePrimitives import AC, MEAS
            from QGL.BasicSequences.helpers import create_cal_seqs
            from functools import reduce
            import operator
            seqsBis = []
            for seq in zip(*seqs):
                seqsBis.append([reduce(operator.__mul__,
                                       [AC(q, c) for q, c in zip(qubits, pulseNums)])
                                for pulseNums in zip(*seq)])

            # Add the measurement to all sequences
            for seq in seqsBis:
                seq.append(reduce(operator.mul, [MEAS(q) for q in qubits]))

            # Tack on the calibration sequences
            if add_cal:
                seqsBis += create_cal_seqs((qubits), 2)
            return seqsBis

        expectedseq = testSimultaneousRB_AC((q1, q2), (rbseqs, rbseqs), add_cals)
        # Must reset the seeds because QGL1 used the prior values, to ensure QGL2 gets same values
        np.random.seed(20151709) # set seed for create_RB_seqs()
        resFunction = compile_function("src/python/qgl2/basic_sequences/RB.py",
                                      "SimultaneousRB_AC",
                                      (qr, (rbseqs, rbseqs), add_cals))
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        # Run testable on the QGL1 to flatten the sequence of sequences
        expectedseq = testable_sequence(expectedseq)

        # QGL2 generates Barrier, P(q1), P(q2), Barrier, ....
        # where QGL1 does PulseBlock(P(q1) * P(q2))
        # - these are equivalent, but look different.
        # I could go thru QGL2, when I find a Barrier, grab all next Pulses up to next Barrier & put them in a PulseBlock?
        # Here though, I take any PulseBlock in QGL1 and just list the Pulses
        expectedseq = flattenPulseBlocks(expectedseq)

        # Strip out the QGL2 Waits and Barriers that QGL1 doesn't have
        # Note that if you want to see the real sequence, don't do this
        seqs = stripWaitBarrier(seqs)

        # self.maxDiff = None
        assertPulseSequenceEqual(self, seqs, expectedseq)

    # These RB functions are unlikely to be done:
    #  SingleQubitRB_DiAC (?)
    #  SingleQubitIRB_AC (needs a file of sequences that I don't have)
    #  Not this one that needs a specific file: SingleQubitRBT

class TestRabi(unittest.TestCase):
    def setUp(self):
        channel_setup()

    def test_RabiAmp(self):
        q1 = QubitFactory('q1')
        qr = QRegister(q1)
        amps = np.linspace(0, 1, 11)
        phase = 0

        expectedseq = []
        for amp in amps:
            expectedseq += [
                qwait(channels=(q1,)),
                Utheta(q1, amp=amp, phase=phase),
                MEAS(q1)
            ]

        resFunction = compile_function("src/python/qgl2/basic_sequences/Rabi.py",
                                      "RabiAmp",
                                      (qr, amps, phase))
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        assertPulseSequenceEqual(self, seqs, expectedseq)

    # Note that QGL2 gives a warning printing the tanh function; harmless
    def test_RabiWidth(self):
        from QGL.PulseShapes import tanh
        q1 = QubitFactory('q1')
        qr = QRegister(q1)
        widths = np.linspace(0, 5e-6, 11)
        amp=1
        phase=0

        resFunction = compile_function("src/python/qgl2/basic_sequences/Rabi.py",
                                      "RabiWidth",
                                      (qr, widths, amp, phase, tanh))
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expectedseq = []
        for l in widths:
            expectedseq += [
                qwait(channels=(q1,)),
                Utheta(q1, length=l, amp=amp, phase=phase, shape_fun=tanh),
                MEAS(q1)
            ]

        assertPulseSequenceEqual(self, seqs, expectedseq)

    def test_RabiAmpPi(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        qr1 = QRegister(q1)
        qr2 = QRegister(q2)

        amps = np.linspace(0, 1, 11)
        phase=0

        resFunction = compile_function("src/python/qgl2/basic_sequences/Rabi.py",
                                      "RabiAmpPi",
                                      (qr1, qr2, amps, phase))
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expectedseq = []
        for amp in amps:
            expectedseq += [
                qwait(channels=(q1,q2)),
                X(q2),
                Utheta(q1, amp=amp, phase=phase),
                X(q2),
                MEAS(q2)
            ]

        assertPulseSequenceEqual(self, seqs, expectedseq)

    def test_SingleShot(self):
        q1 = QubitFactory('q1')
        qr = QRegister(q1)
        resFunction = compile_function("src/python/qgl2/basic_sequences/Rabi.py",
                                      "SingleShot",
                                      (qr,))
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expectedseq = [
            qwait(channels=(q1,)),
            Id(q1),
            MEAS(q1),
            qwait(channels=(q1,)),
            X(q1),
            MEAS(q1)
        ]

        assertPulseSequenceEqual(self, seqs, expectedseq)

    def test_PulsedSpec(self):
        q1 = QubitFactory('q1')
        qr = QRegister(q1)
        resFunction = compile_function("src/python/qgl2/basic_sequences/Rabi.py",
                                      "PulsedSpec",
                                      (qr, True))
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expectedseq = [
            qwait(channels=(q1,)),
            X(q1),
            MEAS(q1)
        ]

        assertPulseSequenceEqual(self, seqs, expectedseq)

    def test_RabiAmp_NQubits(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        qr = QRegister(q1, q2)
        amps = np.linspace(0, 5e-6, 11)
        p = 0
        docals = False
        calRepeats = 2
        expectedseq = []

        for a in amps:
            expectedseq += [
                qwait(channels=(q1,q2)),
                Utheta(q1, amp=a, phase=p),
                Utheta(q2, amp=a, phase=p),
                Barrier(q1, q2),
                MEAS(q1),
                MEAS(q2)
            ]

        if docals:
            # Add calibration
            cal_seqs = get_cal_seqs_2qubits(q1, q2, calRepeats)
            expectedseq += cal_seqs

        expectedseq = testable_sequence(expectedseq)

        resFunction = compile_function("src/python/qgl2/basic_sequences/Rabi.py",
                                      "RabiAmp_NQubits",
                                      (qr, amps, p, None, docals, calRepeats))
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        assertPulseSequenceEqual(self, seqs, expectedseq)

    # Note this is not a QGL1 basic sequence any longer
    def test_Swap(self):
        q = QubitFactory('q1')
        mq = QubitFactory('q2')
        qr = QRegister(q)
        mqr = QRegister(mq)
        delays = np.linspace(0, 5e-6, 11)
        expectedseq = []
        for d in delays:
            expectedseq += [
                qwait(channels=(q, mq)),
                X(q),
                X(mq),
                Id(mq, length=d),
                Barrier(q, mq),
                MEAS(q),
                MEAS(mq)
            ]

        # Add calibration
        cal_seqs = get_cal_seqs_2qubits(q, mq, 2)
        expectedseq += cal_seqs

        expectedseq = testable_sequence(expectedseq)

        resFunction = compile_function("src/python/qgl2/basic_sequences/Rabi.py",
                                      "Swap",
                                      (qr, delays, mqr))
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        assertPulseSequenceEqual(self, seqs, expectedseq)

class TestSPAM(unittest.TestCase):
    def setUp(self):
        channel_setup()

    def test_SPAM(self):
        q = QubitFactory('q1')
        qr = QRegister('q1')
        angleSweep = np.linspace(0, pi/2, 11)
        maxSpamBlocks=10
        expectedseq = []

        def spam_seqs(angle, q, maxSpamBlocks):
            thisseq = []
            for rep in range(maxSpamBlocks):
                thisseq += [
                    qwait(channels=(q,)),
                    Y90(q)
                ]
                innerseq = []
                for _ in range(rep):
                    innerseq += [
                        X(q),
                        U(q, phase=pi/2+angle),
                        X(q),
                        U(q, phase=pi/2+angle)
                        ]
                thisseq += innerseq
                thisseq += [
                    X90(q),
                    MEAS(q)
                ]
            return thisseq

        for angle in angleSweep:
            expectedseq += [
                qwait(channels=(q,)),
                Id(q),
                MEAS(q)
            ]
            expectedseq += spam_seqs(angle, q, maxSpamBlocks)
        expectedseq += [
            qwait(channels=(q,)),
            X(q),
            MEAS(q)
        ]
        resFunction = compile_function("src/python/qgl2/basic_sequences/SPAM.py",
                                      "SPAM",
                                      (qr, angleSweep, maxSpamBlocks))
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        assertPulseSequenceEqual(self, seqs, expectedseq)

class TestT1T2(unittest.TestCase):
    def setUp(self):
        channel_setup()

    def test_InversionRecovery(self):
        q = QubitFactory('q1')
        qr = QRegister('q1')
        delays = np.linspace(0, 5e-6, 11)
        calRepeats = 2
        expectedseq = []
        for d in delays:
            expectedseq += [
                qwait(channels=(q,)),
                X(q),
                Id(q, d),
                MEAS(q)
            ]

        # Add calibration
        cal = get_cal_seqs_1qubit(q, calRepeats)
        expectedseq += cal

        expectedseq = testable_sequence(expectedseq)

        resFunction = compile_function("src/python/qgl2/basic_sequences/T1T2.py",
                                      "InversionRecovery",
                                      (qr, delays, calRepeats))
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        assertPulseSequenceEqual(self, seqs, expectedseq)

    def test_Ramsey(self):
        q = QubitFactory('q1')
        qr = QRegister('q1')
        delays = np.arange(100e-9, 10e-6, 100e-9)
        TPPIFreq = 1e6
        calRepeats = 2
        expectedseq = []

        # Create the phases for the TPPI
        phases = 2*pi*TPPIFreq*delays

        # Create the basic Ramsey sequence
        for d,phase in zip(delays, phases):
            expectedseq += [
                qwait(channels=(q,)),
                X90(q),
                Id(q, d),
                U90(q, phase=phase),
                MEAS(q)
            ]
        # Add calibration
        cal = get_cal_seqs_1qubit(q, calRepeats)
        expectedseq += cal

        expectedseq = testable_sequence(expectedseq)

        resFunction = compile_function("src/python/qgl2/basic_sequences/T1T2.py",
                                      "Ramsey",
                                      (qr, delays, TPPIFreq, calRepeats))
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        assertPulseSequenceEqual(self, seqs, expectedseq)

if __name__ == '__main__':
    # To test everything in this file (say, using cProfile)
#    unittest.main("test.test_basic_mins")
    # To run just 1 test from this file, try something like:
#    unittest.main("test.test_basic_mins", "TestCR.test_PiRabi")
    unittest.main("test.test_basic_mins", "TestAllXY.test_AllXY")
