# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.
'''
Test the qgl1/basic_sequences
'''
import datetime
import unittest
import numpy as np
from math import pi

from pyqgl2.main import compile_function
from QGL import *
from qgl2.qgl1control import Barrier

from test.helpers import testable_sequence, discard_zero_Ids, \
    flattenSeqs, channel_setup, assertPulseSequenceEqual, \
    get_cal_seqs_1qubit, get_cal_seqs_2qubits

class TestBasicMins(unittest.TestCase):
    def setUp(self):
        channel_setup()

    def tearDown(self):
        pass

    def test_AllXY(self):
        q1 = QubitFactory('q1')
        expectedseq = []
        # Expect a single sequence 5 * 2 * 21 pulses long
        # Expect it to start like this:
        expectedseq += [
            qsync(),
            qwait(),
            Id(q1),
            Id(q1),
            MEAS(q1),
            qsync(),
            qwait(),
            Id(q1),
            Id(q1),
            MEAS(q1)
            ]

        # To turn on verbose logging in compile_function
        # from pyqgl2.ast_util import NodeError
        # from pyqgl2.debugmsg import DebugMsg
        # NodeError.MUTE_ERR_LEVEL = NodeError.NODE_ERROR_NONE
        # DebugMsg.set_level(0)

        # Can optionally supply saveOutput=True to save the qgl1.py
        # file,
        # and intermediate_output="path-to-output-file" to save
        # intermediate products
        resFunction = compile_function("src/python/qgl2/basic_sequences/AllXYMin.py",
                                      "doAllXY",
                                      (q1,))
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        self.assertEqual(len(seqs), 5*21*2)
        assertPulseSequenceEqual(self, seqs[:len(expectedseq)], expectedseq)

    # Tests list of lists of function references, instead of sub-functions
    def test_AllXY_alt1(self):
        q1 = QubitFactory('q1')
        expectedseq = []
        # Expect a single sequence 5 * 2 * 21 pulses long
        # Expect it to start like this:
        expectedseq += [
            qsync(),
            qwait(),
            Id(q1),
            Id(q1),
            MEAS(q1),
            qsync(),
            qwait(),
            Id(q1),
            Id(q1),
            MEAS(q1)
            ]

        resFunction = compile_function(
                "test/code/AllXY_alt.py",
                "doAllXY",
                (q1,))
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        self.assertEqual(len(seqs), 5*21*2)
        assertPulseSequenceEqual(self, seqs[:len(expectedseq)], expectedseq)

    def test_AllXY_alt2(self):
        q1 = QubitFactory('q1')
        expectedseq = []
        # Expect a single sequence 5 * 2 * 21 pulses long
        # Expect it to start like this:
        expectedseq += [
            qsync(),
            qwait(),
            Id(q1),
            Id(q1),
            MEAS(q1),
            qsync(),
            qwait(),
            Id(q1),
            Id(q1),
            MEAS(q1)
            ]

        resFunction = compile_function(
                "test/code/AllXY_alt.py",
                "doAllXY2",
                (q1,))
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        self.assertEqual(len(seqs), 5*21*2)
        assertPulseSequenceEqual(self, seqs[:len(expectedseq)], expectedseq)


    # CRMin

    # PiRabi
    def test_PiRabi(self):
        controlQ = QubitFactory('q1')
        targetQ = QubitFactory('q2')
        edge = EdgeFactory(controlQ, targetQ)
        # FIXME: Better values!?
        lengths = np.linspace(0, 4e-6, 11)
        riseFall=40e-9
        amp=1
        phase=0
        calRepeats = 2

        expected_seq = []
        # Seq1
        for l in lengths:
            expected_seq += [
                qsync(),
                qwait(),
                qsync(),
                qwait(),
                Id(controlQ),
                flat_top_gaussian(edge, riseFall, length=l, amp=amp, phase=phase),
                Barrier("", (targetQ, controlQ)),
                MEAS(targetQ),
                MEAS(controlQ)
            ]
        # Seq2
        for l in lengths:
            expected_seq += [
                qsync(),
                qwait(),
                qsync(),
                qwait(),
                X(controlQ),
                flat_top_gaussian(edge, riseFall, length=l, amp=amp, phase=phase),
                X(controlQ),
                Barrier("", (targetQ, controlQ)),
                MEAS(targetQ),
                MEAS(controlQ)
            ]

        # Add calibration
        calseq = get_cal_seqs_2qubits(targetQ, controlQ, calRepeats)
        expected_seq += calseq
        expected_seq = testable_sequence(expected_seq)

        resFunction = compile_function("src/python/qgl2/basic_sequences/CRMin.py",
                                      "doPiRabi")
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        self.maxDiff = None
        assertPulseSequenceEqual(self, seqs, expected_seq)

    def test_EchoCRLen(self):
        controlQ = QubitFactory('q1')
        targetQ = QubitFactory('q2')
        # FIXME: Better values!?
        lengths = np.linspace(0, 2e-6, 11)
        riseFall=40e-9
        amp=1
        phase=0
        calRepeats=2

        expected_seq = []
        # Seq1
        for l in lengths:
            expected_seq += [
                qsync(),
                qwait(),
                qsync(),
                qwait(),
                Id(controlQ),
                echoCR(controlQ, targetQ, length=l, phase=phase,
                       riseFall=riseFall),
                Id(controlQ),
                Barrier("", (targetQ, controlQ)),
                MEAS(targetQ),
                MEAS(controlQ)
            ]
        # Seq2
        for l in lengths:
            expected_seq += [
                qsync(),
                qwait(),
                qsync(),
                qwait(),
                X(controlQ),
                echoCR(controlQ, targetQ, length=l, phase=phase,
                       riseFall=riseFall),
                X(controlQ),
                Barrier("", (targetQ, controlQ)),
                MEAS(targetQ),
                MEAS(controlQ)
            ]

        # Add calibration
        cal_seqs = get_cal_seqs_2qubits(targetQ, controlQ, calRepeats)
        expected_seq += cal_seqs
        expected_seq = testable_sequence(expected_seq)

        resFunction = compile_function("src/python/qgl2/basic_sequences/CRMin.py",
                                      "doEchoCRLen")
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        self.maxDiff = None
        assertPulseSequenceEqual(self, seqs, expected_seq)

    def test_EchoCRPhase(self):
        controlQ = QubitFactory('q1')
        targetQ = QubitFactory('q2')
        phases = np.linspace(0, pi/2, 11)
        riseFall=40e-9
        amp=1
        length=100e-9
        calRepeats=2
        expected_seq = []

        # Seq1
        for p in phases:
            expected_seq += [
                qsync(),
                qwait(),
                qsync(),
                qwait(),
                Id(controlQ),
                echoCR(controlQ, targetQ, length=length, phase=p,
                       riseFall=riseFall),
                X90(targetQ),
                Id(controlQ),
                Barrier("", (targetQ, controlQ)),
                MEAS(targetQ),
                MEAS(controlQ)
            ]

        # Seq2
        for p in phases:
            expected_seq += [
                qsync(),
                qwait(),
                qsync(),
                qwait(),
                X(controlQ),
                echoCR(controlQ, targetQ, length=length, phase=p,
                       riseFall=riseFall),
                X90(targetQ),
                X(controlQ),
                Barrier("", (targetQ, controlQ)),
                MEAS(targetQ),
                MEAS(controlQ)
            ]

        # Add calibration
        cal_seqs = get_cal_seqs_2qubits(targetQ, controlQ, calRepeats)
        expected_seq += cal_seqs
        expected_seq = testable_sequence(expected_seq)

        resFunction = compile_function("src/python/qgl2/basic_sequences/CRMin.py",
                                      "doEchoCRPhase")
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        self.maxDiff = None
        assertPulseSequenceEqual(self, seqs, expected_seq)

    ## DecouplingMin

    def test_HahnEcho(self):
        q = QubitFactory('q1')
        steps = 11
        pulseSpacings = np.linspace(0, 5e-6, steps)
        periods = 0
        calRepeats=2
        expectedseq = []
        for k in range(len(pulseSpacings)):
            expectedseq += [
                qsync(),
                qwait(),
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

        resFunction = compile_function("src/python/qgl2/basic_sequences/DecouplingMin.py",
                                      "doHahnEcho",
                                      (q, pulseSpacings, periods, calRepeats))
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        assertPulseSequenceEqual(self, seqs, expectedseq)

    def test_CPMG(self):
        q = QubitFactory('q1')

        # Create numPulses sequences
        numPulses = [0, 2, 4, 6]
        pulseSpacing = 500e-9
        calRepeats = 2

        def addt180t(q, pulseSpacing, rep):
            t180t = []
            for _ in range(rep):
                t180t += [
                    Id(q, (pulseSpacing - q.pulseParams['length'])/2),
                    Y(q),
                    Id(q, (pulseSpacing - q.pulseParams['length'])/2)
                ]
            return t180t

        expectedseq = []
        for rep in numPulses:
            expectedseq += [
                qsync(),
                qwait(),
                X90(q)
            ]
            expectedseq += addt180t(q, pulseSpacing, rep)
            expectedseq += [
                X90(q),
                MEAS(q)
            ]

        # Add calibration
        cal = get_cal_seqs_1qubit(q, calRepeats)
        expectedseq += cal

        expectedseq = testable_sequence(expectedseq)

        resFunction = compile_function("src/python/qgl2/basic_sequences/DecouplingMin.py",
                                      "doCPMG",
                                      (q, numPulses, pulseSpacing, calRepeats))
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        assertPulseSequenceEqual(self, seqs, expectedseq)

    ## FlipFlopMin
    def test_FlipFlop(self):
        qubit = QubitFactory('q1')
        dragParamSweep = np.linspace(0, 5e-6, 11) # FIXME
        maxNumFFs = 10

        def addFFSeqs(dragParam, maxNumFFs, qubit):
            ffs = []
            for rep in range(maxNumFFs):
                ffs += [
                    qsync(),
                    qwait(),
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
                qsync(),
                qwait(),
                Id(qubit),
                MEAS(qubit)
            ]
            expectedseq += addFFSeqs(dragParam, maxNumFFs, qubit)
        expectedseq += [
            qsync(),
            qwait(),
            X(qubit),
            MEAS(qubit)
        ]
        resFunction = compile_function("src/python/qgl2/basic_sequences/FlipFlopMin.py",
                                      "doFlipFlop",
                                      (qubit, dragParamSweep, maxNumFFs))
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        assertPulseSequenceEqual(self, seqs, expectedseq)

    ## RB isn't ready yet

    ## Rabi

    def test_RabiAmp(self):
        q1 = QubitFactory('q1')
        amps = np.linspace(0, 1, 11)
        phase = 0

        expectedseq = []
        for amp in amps:
            expectedseq += [
                qsync(),
                qwait(),
                Utheta(q1, amp=amp, phase=phase),
                MEAS(q1)
            ]

        resFunction = compile_function("src/python/qgl2/basic_sequences/RabiMin.py",
                                      "doRabiAmp",
                                      (q1, amps, phase))
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        assertPulseSequenceEqual(self, seqs, expectedseq)

    # Fails due to import of tanh, etc. See RabiMin.py
    def test_RabiWidth(self):
        from qgl2.basic_sequences.pulses import local_tanh
        q1 = QubitFactory('q1')
        widths = np.linspace(0, 5e-6, 11)

        resFunction = compile_function("src/python/qgl2/basic_sequences/RabiMin.py",
                                      "doRabiWidth",
                                      (q1, widths))
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expectedseq = []
        for l in widths:
            expectedseq += [
                qsync(),
                qwait(),
                Utheta(q1, length=l, amp=1, phase=0, shapeFun=local_tanh),
                MEAS(q1)
            ]

        assertPulseSequenceEqual(self, seqs, expectedseq)

    def test_RabiAmpPi(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        amps = np.linspace(0, 1, 11)

        resFunction = compile_function("src/python/qgl2/basic_sequences/RabiMin.py",
                                      "doRabiAmpPi",
                                      (q1, q2, amps))
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expectedseq = []
        for amp in amps:
            expectedseq += [
                qsync(),
                qwait(),
                qsync(),
                qwait(),
                X(q2),
                Utheta(q1, amp=amp, phase=0),
                X(q2),
                MEAS(q2)
            ]

        assertPulseSequenceEqual(self, seqs, expectedseq)

    def test_SingleShot(self):
        q1 = QubitFactory('q1')
        resFunction = compile_function("src/python/qgl2/basic_sequences/RabiMin.py",
                                      "doSingleShot",
                                      (q1,))
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expectedseq = [
            qsync(),
            qwait(),
            Id(q1),
            MEAS(q1),
            qsync(),
            qwait(),
            X(q1),
            MEAS(q1)
        ]

        assertPulseSequenceEqual(self, seqs, expectedseq)

    def test_PulsedSpec(self):
        q1 = QubitFactory('q1')
        resFunction = compile_function("src/python/qgl2/basic_sequences/RabiMin.py",
                                      "doPulsedSpec",
                                      (q1, True))
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expectedseq = [
            qsync(),
            qwait(),
            X(q1),
            MEAS(q1)
        ]

        assertPulseSequenceEqual(self, seqs, expectedseq)

    def test_RabiAmp_NQubits(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        qubits = [q1, q2]
        amps = np.linspace(0, 5e-6, 11)
        p = 0
        docals = False
        calRepeats = 2
        expectedseq = []

        for a in amps:
            expectedseq += [
                qsync(),
                qwait(),
                qsync(),
                qwait(),
                Utheta(q1, amp=a, phase=p),
                Utheta(q2, amp=a, phase=p),
                Barrier("", (q1, q2)),
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
                                      (qubits, amps, docals, calRepeats))
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        assertPulseSequenceEqual(self, seqs, expectedseq)

    def test_Swap(self):
        q = QubitFactory('q1')
        mq = QubitFactory('q2')
        delays = np.linspace(0, 5e-6, 11)
        expectedseq = []
        for d in delays:
            expectedseq += [
                qsync(),
                qwait(),
                qsync(),
                qwait(),
                X(q),
                X(mq),
                Id(mq, length=d),
                Barrier("", (q, mq)),
                MEAS(q),
                MEAS(mq)
            ]

        # Add calibration
        cal_seqs = get_cal_seqs_2qubits(mq, q, 2)
        expectedseq += cal_seqs

        expectedseq = testable_sequence(expectedseq)

        resFunction = compile_function("src/python/qgl2/basic_sequences/RabiMin.py",
                                      "doSwap",
                                      (q, mq, delays))
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        assertPulseSequenceEqual(self, seqs, expectedseq)

    ## SPAMMin

    def test_SPAM(self):
        q = QubitFactory('q1')
        angleSweep = np.linspace(0, pi/2, 11)
        maxSpamBlocks=10
        expectedseq = []

        def spam_seqs(angle, q, maxSpamBlocks):
            thisseq = []
            for rep in range(maxSpamBlocks):
                thisseq += [
                    qsync(),
                    qwait(),
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
                qsync(),
                qwait(),
                Id(q),
                MEAS(q)
            ]
            expectedseq += spam_seqs(angle, q, maxSpamBlocks)
        expectedseq += [
            qsync(),
            qwait(),
            X(q),
            MEAS(q)
        ]
        resFunction = compile_function("src/python/qgl2/basic_sequences/SPAMMin.py",
                                      "doSPAM",
                                      (q, angleSweep, maxSpamBlocks))
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        assertPulseSequenceEqual(self, seqs, expectedseq)

    ## T1T2Min

    def test_InversionRecovery(self):
        q = QubitFactory('q1')
        delays = np.linspace(0, 5e-6, 11)
        calRepeats = 2
        expectedseq = []
        for d in delays:
            expectedseq += [
                qsync(),
                qwait(),
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
                                      (q, delays, calRepeats))
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        assertPulseSequenceEqual(self, seqs, expectedseq)

    def test_Ramsey(self):
        q = QubitFactory('q1')
        delays = np.arange(100e-9, 10e-6, 100e-9)
        TPPIFreq = 1e6
        calRepeats = 2
        expectedseq = []

        # Create the phases for the TPPI
        phases = 2*pi*TPPIFreq*delays

        # Create the basic Ramsey sequence
        for d,phase in zip(delays, phases):
            expectedseq += [
                qsync(),
                qwait(),
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
                                      (q, delays, TPPIFreq, calRepeats))
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        assertPulseSequenceEqual(self, seqs, expectedseq)

if __name__ == '__main__':
    # To test everything in this file (say, using cProfile)
    unittest.main("test.test_basic_mins")
    # To run just 1 test from this file, try something like:
    # unittest.main("test.test_basic_mins", "TestBasicMins.test_AllXY")
