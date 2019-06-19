# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.
'''
Test the qgl1/basic_sequences
'''
import datetime
import unittest
import numpy as np
from math import pi

from pyqgl2.main import compile_function
from pyqgl2.qreg import QRegister
from QGL import *

from test.helpers import testable_sequence, \
    channel_setup, assertPulseSequenceEqual, \
    get_cal_seqs_1qubit, get_cal_seqs_2qubits

class TestAllXY(unittest.TestCase):
    def setUp(self):
        channel_setup()

    def test_AllXY(self):
        # QGL1 uses QubitFactory, QGL2 uses QRegister
        q1 = QubitFactory('q1')
        qr = QRegister(1)

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


class TestCR(unittest.TestCase):
    def setUp(self):
        channel_setup()

    def test_PiRabi(self):
        controlQ = QubitFactory('q1')
        targetQ = QubitFactory('q2')
        controlQR = QRegister('q1')
        targetQR = QRegister('q2')
        qr = QRegister('q1', 'q2')
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
        cR = QRegister('q1')
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

## RB isn't ready yet
class TestRabiMin(unittest.TestCase):
    def setUp(self):
        channel_setup()
    ## Rabi

    def test_RabiAmp(self):
        q1 = QubitFactory('q1')
        qr = QRegister('q1')
        amps = np.linspace(0, 1, 11)
        phase = 0

        expectedseq = []
        for amp in amps:
            expectedseq += [
                qwait(channels=(q1,)),
                Utheta(q1, amp=amp, phase=phase),
                MEAS(q1)
            ]

        resFunction = compile_function("src/python/qgl2/basic_sequences/RabiMin.py",
                                      "doRabiAmp",
                                      (qr, amps, phase))
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        assertPulseSequenceEqual(self, seqs, expectedseq)

    # Fails due to import of tanh, etc. See RabiMin.py
    def test_RabiWidth(self):
        from qgl2.basic_sequences.pulses import local_tanh
        q1 = QubitFactory('q1')
        qr = QRegister('q1')
        widths = np.linspace(0, 5e-6, 11)

        resFunction = compile_function("src/python/qgl2/basic_sequences/RabiMin.py",
                                      "doRabiWidth",
                                      (qr, widths))
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expectedseq = []
        for l in widths:
            expectedseq += [
                qwait(channels=(q1,)),
                Utheta(q1, length=l, amp=1, phase=0, shapeFun=local_tanh),
                MEAS(q1)
            ]

        assertPulseSequenceEqual(self, seqs, expectedseq)

    def test_RabiAmpPi(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        qr = QRegister('q1', 'q2')
        amps = np.linspace(0, 1, 11)

        resFunction = compile_function("src/python/qgl2/basic_sequences/RabiMin.py",
                                      "doRabiAmpPi",
                                      (qr, amps))
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expectedseq = []
        for amp in amps:
            expectedseq += [
                qwait(channels=(q1,q2)),
                X(q2),
                Utheta(q1, amp=amp, phase=0),
                X(q2),
                MEAS(q2)
            ]

        assertPulseSequenceEqual(self, seqs, expectedseq)

    def test_SingleShot(self):
        q1 = QubitFactory('q1')
        qr = QRegister('q1')
        resFunction = compile_function("src/python/qgl2/basic_sequences/RabiMin.py",
                                      "doSingleShot",
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
        qr = QRegister('q1')
        resFunction = compile_function("src/python/qgl2/basic_sequences/RabiMin.py",
                                      "doPulsedSpec",
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
        qr = QRegister('q1', 'q2')
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
                MEAS(q1),
                MEAS(q2)
            ]

        if docals:
            # Add calibration
            cal_seqs = get_cal_seqs_2qubits(q1, q2, calRepeats)
            expectedseq += cal_seqs

        expectedseq = testable_sequence(expectedseq)

        resFunction = compile_function("src/python/qgl2/basic_sequences/RabiMin.py",
                                      "doRabiAmp_NQubits",
                                      (qr, amps, docals, calRepeats))
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        assertPulseSequenceEqual(self, seqs, expectedseq)

    def test_Swap(self):
        q = QubitFactory('q1')
        mq = QubitFactory('q2')
        qr = QRegister('q1', 'q2')
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

        resFunction = compile_function("src/python/qgl2/basic_sequences/RabiMin.py",
                                      "doSwap",
                                      (qr, delays))
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

        resFunction = compile_function("src/python/qgl2/basic_sequences/T1T2Min.py",
                                      "doInversionRecovery",
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

        resFunction = compile_function("src/python/qgl2/basic_sequences/T1T2Min.py",
                                      "doRamsey",
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
