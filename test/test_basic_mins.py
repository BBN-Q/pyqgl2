# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.
'''
Test the qgl1/basic_sequences
'''
import datetime
import unittest
import numpy as np
from math import pi

from pyqgl2.main import compileFunction
from QGL import *

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

        # To turn on verbose logging in compileFunction
        # from pyqgl2.ast_util import NodeError
        # from pyqgl2.debugmsg import DebugMsg
        # NodeError.MUTE_ERR_LEVEL = NodeError.NODE_ERROR_NONE
        # DebugMsg.set_level(0)

        # Can optionally supply saveOutput=True to save the qgl1.py
        # file,
        # and intermediate_output="path-to-output-file" to save
        # intermediate products
        resFunction = compileFunction("src/python/qgl2/basic_sequences/AllXYMin.py",
                                      "doAllXY")
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        self.assertEqual(len(seqs), 1)
        self.assertEqual(len(seqs[0]), 5*21*2)
        assertPulseSequenceEqual(self, seqs[0][:len(expectedseq)], expectedseq)

    # Tests list of lists of function references, instead of sub-functions
    def test_AllXYq3(self):
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

        # To turn on verbose logging in compileFunction
        # from pyqgl2.ast_util import NodeError
        # from pyqgl2.debugmsg import DebugMsg
        # NodeError.MUTE_ERR_LEVEL = NodeError.NODE_ERROR_NONE
        # DebugMsg.set_level(0)

        # Can optionally supply saveOutput=True to save the qgl1.py
        # file,
        # and intermediate_output="path-to-output-file" to save
        # intermediate products
        resFunction = compileFunction(
                "src/python/qgl2/basic_sequences/AllXYMin.py",
                "AllXYq3")
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        self.assertEqual(len(seqs), 1)
        self.assertEqual(len(seqs[0]), 5*21*2)
        assertPulseSequenceEqual(self, seqs[0][:len(expectedseq)], expectedseq)


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

        expected_seq_q1 = [] # control
        # Seq1
        for l in lengths:
            expected_seq_q1 += [
                qsync(),
                qwait(),
                Id(controlQ),
                flat_top_gaussian(edge, riseFall, length=l, amp=amp, phase=phase),
                MEAS(controlQ)
            ]
        # Seq2
        for l in lengths:
            expected_seq_q1 += [
                qsync(),
                qwait(),
                X(controlQ),
                flat_top_gaussian(edge, riseFall, length=l, amp=amp, phase=phase),
                X(controlQ),
                MEAS(controlQ)
            ]

        expected_seq_q2 = [] # target
        # Seq1
        for l in lengths:
            expected_seq_q2 += [
                qsync(),
                qwait(),
                Id(targetQ, length=Id(controlQ).length),
                flat_top_gaussian(edge, riseFall, length=l, amp=amp, phase=phase),
                MEAS(targetQ)
            ]
        # Seq2
        for l in lengths:
            expected_seq_q2 += [
                qsync(),
                qwait(),
                Id(targetQ, length=X(controlQ).length),
                flat_top_gaussian(edge, riseFall, length=l, amp=amp, phase=phase),
                Id(targetQ, length=X(controlQ).length),
                MEAS(targetQ)
            ]

        # Add calibration
        cal_target, cal_control = get_cal_seqs_2qubits(targetQ, controlQ, calRepeats)
        expected_seq_q1 += cal_control
        expected_seq_q2 += cal_target
        discard_zero_Ids([expected_seq_q1, expected_seq_q2])

        # To turn on verbose logging in compileFunction
#        from pyqgl2.ast_util import NodeError
#        from pyqgl2.debugmsg import DebugMsg
#        NodeError.MUTE_ERR_LEVEL = NodeError.NODE_ERROR_NONE
#        DebugMsg.set_level(0)

        # Can optionally supply saveOutput=True to save the qgl1.py
        # file,
        # and intermediate_output="path-to-output-file" to save
        # intermediate products
        resFunction = compileFunction("src/python/qgl2/basic_sequences/CRMin.py",
                                      "doPiRabi")
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        # Need to map right seq to right expected seq
        self.assertEqual(len(seqs), 2)
        self.maxDiff = None
        if seqs[0][2] == Id(controlQ):
            assertPulseSequenceEqual(self, seqs[0], expected_seq_q1)
            assertPulseSequenceEqual(self, seqs[1], expected_seq_q2)
        else:
            assertPulseSequenceEqual(self, seqs[1], expected_seq_q1)
            assertPulseSequenceEqual(self, seqs[0], expected_seq_q2)

    def test_EchoCRLen(self):
        controlQ = QubitFactory('q1')
        targetQ = QubitFactory('q2')
        # FIXME: Better values!?
        lengths = np.linspace(0, 2e-6, 11)
        riseFall=40e-9
        amp=1
        phase=0
        calRepeats=2

        expected_seq_q1 = []
        # Seq1
        for l in lengths:
            expected_seq_q1 += [
                qsync(),
                qwait(),
                Id(controlQ),
                echoCR(controlQ, targetQ, length=l, phase=phase,
                       riseFall=riseFall),
                Id(controlQ),
                MEAS(controlQ)
            ]
        # Seq2
        for l in lengths:
            expected_seq_q1 += [
                qsync(),
                qwait(),
                X(controlQ),
                echoCR(controlQ, targetQ, length=l, phase=phase,
                       riseFall=riseFall),
                X(controlQ),
                MEAS(controlQ)
            ]

        expected_seq_q2 = []
        # Seq1
        for l in lengths:
            expected_seq_q2 += [
                qsync(),
                qwait(),
                Id(targetQ, length=Id(controlQ).length),
                echoCR(controlQ, targetQ, length=l, phase=phase,
                       riseFall=riseFall),
                Id(targetQ, length=Id(controlQ).length),
                MEAS(targetQ)
            ]
        # Seq2
        for l in lengths:
            expected_seq_q2 += [
                qsync(),
                qwait(),
                Id(targetQ, length=X(controlQ).length),
                echoCR(controlQ, targetQ, length=l, phase=phase,
                       riseFall=riseFall),
                Id(targetQ, length=X(controlQ).length),
                MEAS(targetQ)
            ]

        # Flatten the echos
        expected_seq_q1, expected_seq_q2 = flattenSeqs([expected_seq_q1, expected_seq_q2])

        # Add calibration
        cal_target, cal_control = get_cal_seqs_2qubits(targetQ, controlQ, calRepeats)
        expected_seq_q1 += cal_control
        expected_seq_q2 += cal_target
        discard_zero_Ids([expected_seq_q1, expected_seq_q2])

        # To turn on verbose logging in compileFunction
#        from pyqgl2.ast_util import NodeError
#        from pyqgl2.debugmsg import DebugMsg
#        NodeError.MUTE_ERR_LEVEL = NodeError.NODE_ERROR_NONE
#        DebugMsg.set_level(0)

        # Can optionally supply saveOutput=True to save the qgl1.py
        # file,
        # and intermediate_output="path-to-output-file" to save
        # intermediate products
        resFunction = compileFunction("src/python/qgl2/basic_sequences/CRMin.py",
                                      "doEchoCRLen")
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        # Need to map right seq to right expected seq
        self.assertEqual(len(seqs), 2)
        self.maxDiff = None
        if seqs[0][2] == Id(controlQ):
            assertPulseSequenceEqual(self, seqs[0], expected_seq_q1)
            assertPulseSequenceEqual(self, seqs[1], expected_seq_q2)
        else:
            assertPulseSequenceEqual(self, seqs[1], expected_seq_q1)
            assertPulseSequenceEqual(self, seqs[0], expected_seq_q2)

    def test_EchoCRPhase(self):
        controlQ = QubitFactory('q1')
        targetQ = QubitFactory('q2')
        phases = np.linspace(0, pi/2, 11)
        riseFall=40e-9
        amp=1
        length=100e-9
        calRepeats=2
        expected_seq_q1 = []

        l1 = X90(targetQ).length - Id(controlQ).length
        if l1 > 0:
            s1q1 = Id(controlQ, length=l1)
            s1q2 = Id(targetQ, length=0)
        else:
            s1q1 = Id(controlQ, length=0)
            s1q2 = Id(targetQ, length=l1)
        # Seq1
        for p in phases:
            expected_seq_q1 += [
                qsync(),
                qwait(),
                Id(controlQ),
                echoCR(controlQ, targetQ, length=length, phase=p,
                       riseFall=riseFall),
                Id(controlQ),
                s1q1,
                MEAS(controlQ)
            ]

        l2 = X90(targetQ).length - X(controlQ).length
        if l2 > 0:
            s2q1 = Id(controlQ, length=l2)
            s2q2 = Id(targetQ, length=0)
        else:
            s2q1 = Id(controlQ, length=0)
            s2q2 = Id(targetQ, length=l2)
        # Seq2
        for p in phases:
            expected_seq_q1 += [
                qsync(),
                qwait(),
                X(controlQ),
                echoCR(controlQ, targetQ, length=length, phase=p,
                       riseFall=riseFall),
                X(controlQ),
                s2q1,
                MEAS(controlQ)
            ]

        expected_seq_q2 = []
        # Seq1
        for p in phases:
            expected_seq_q2 += [
                qsync(),
                qwait(),
                Id(targetQ, length=Id(controlQ).length),
                echoCR(controlQ, targetQ, length=length, phase=p,
                       riseFall=riseFall),
                X90(targetQ),
                s1q2,
                MEAS(targetQ)
            ]
        # Seq2
        for p in phases:
            expected_seq_q2 += [
                qsync(),
                qwait(),
                Id(targetQ, length=X(controlQ).length),
                echoCR(controlQ, targetQ, length=length, phase=p,
                       riseFall=riseFall),
                X90(targetQ),
                s2q2,
                MEAS(targetQ)
            ]

        # Add calibration
        cal_target, cal_control = get_cal_seqs_2qubits(targetQ, controlQ, calRepeats)
        expected_seq_q1 += cal_control
        expected_seq_q2 += cal_target

        # Get rid of any 0 length Id pulses just added
        discard_zero_Ids([expected_seq_q1, expected_seq_q2])

        # Flatten the echos
        expected_seq_q1, expected_seq_q2 = flattenSeqs([expected_seq_q1, expected_seq_q2])

        # To turn on verbose logging in compileFunction
#        from pyqgl2.ast_util import NodeError
#        from pyqgl2.debugmsg import DebugMsg
#        NodeError.MUTE_ERR_LEVEL = NodeError.NODE_ERROR_NONE
#        DebugMsg.set_level(0)

        # Can optionally supply saveOutput=True to save the qgl1.py
        # file,
        # and intermediate_output="path-to-output-file" to save
        # intermediate products
        resFunction = compileFunction("src/python/qgl2/basic_sequences/CRMin.py",
                                      "doEchoCRPhase")
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        # Need to map right seq to right expected seq
        self.assertEqual(len(seqs), 2)
        self.maxDiff = None
        if seqs[0][2] == Id(controlQ):
            assertPulseSequenceEqual(self, seqs[0], expected_seq_q1)
            assertPulseSequenceEqual(self, seqs[1], expected_seq_q2)
        else:
            assertPulseSequenceEqual(self, seqs[1], expected_seq_q1)
            assertPulseSequenceEqual(self, seqs[0], expected_seq_q2)

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

        # Get rid of any 0 length Id pulses just added
        discard_zero_Ids([expectedseq])

        resFunction = compileFunction("src/python/qgl2/basic_sequences/DecouplingMin.py",
                                      "doHahnEcho")
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        assertPulseSequenceEqual(self, seqs[0], expectedseq)

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
        # Get rid of any 0 length Id pulses just added
        discard_zero_Ids([expectedseq])

        resFunction = compileFunction("src/python/qgl2/basic_sequences/DecouplingMin.py",
                                      "doCPMG")
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        assertPulseSequenceEqual(self, seqs[0], expectedseq)

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
        resFunction = compileFunction("src/python/qgl2/basic_sequences/FlipFlopMin.py",
                                      "doFlipFlop")
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        assertPulseSequenceEqual(self, seqs[0], expectedseq)

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

        resFunction = compileFunction("src/python/qgl2/basic_sequences/RabiMin.py",
                                      "doRabiAmp",
                                      (q1, amps, phase))
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        assertPulseSequenceEqual(self, seqs[0], expectedseq)

    # Fails due to import of tanh, etc. See RabiMin.py
    def test_RabiWidth(self):
        from qgl2.basic_sequences.pulses import local_tanh
        q1 = QubitFactory('q1')
        widths = np.linspace(0, 5e-6, 11)

        resFunction = compileFunction("src/python/qgl2/basic_sequences/RabiMin.py",
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

        assertPulseSequenceEqual(self, seqs[0], expectedseq)

    def test_RabiAmpPi(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        amps = np.linspace(0, 1, 11)

        resFunction = compileFunction("src/python/qgl2/basic_sequences/RabiMin.py",
                                      "doRabiAmpPi",
                                      (q1, q2, amps))
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expectedseq1 = []
        expectedseq2 = []
        for amp in amps:
            expectedseq1 += [
                qsync(),
                qwait(),
                Id(q1, length=X(q2).length), # fills space of X(q2)
                Utheta(q1, amp=amp, phase=0),
                Id(q1, length=X(q2).length), # fills space of X(q2)
                Id(q1, length=MEAS(q2).length) # fills space of MEAS(q2)
            ]
            expectedseq2 += [
                qsync(),
                qwait(),
                X(q2),
                Id(q2, length=X(q1).length), # fills space of Utheta(q1)
                X(q2),
                MEAS(q2)
            ]

        assertPulseSequenceEqual(self, seqs[0], expectedseq1)
        assertPulseSequenceEqual(self, seqs[1], expectedseq2)

    def test_SingleShot(self):
        q1 = QubitFactory('q1')
        resFunction = compileFunction("src/python/qgl2/basic_sequences/RabiMin.py",
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

        assertPulseSequenceEqual(self, seqs[0], expectedseq)

    def test_PulsedSpec(self):
        q1 = QubitFactory('q1')
        resFunction = compileFunction("src/python/qgl2/basic_sequences/RabiMin.py",
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

        assertPulseSequenceEqual(self, seqs[0], expectedseq)

    def test_RabiAmp_NQubits(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        qubits = [q1, q2]
        measChans = qubits
        amps = np.linspace(0, 5e-6, 11)
        p = 0
        docals = False
        calRepeats = 2
        expectedseq1 = []
        expectedseq2 = []
        for a in amps:
            q1l = Utheta(q1, amp=a, phase=p).length + MEAS(measChans[0]).length
            q2l = Utheta(q2, amp=a, phase=p).length + MEAS(measChans[1]).length
            expectedseq1 += [
                qsync(),
                qwait(),
                Utheta(q1, amp=a, phase=p),
                MEAS(measChans[0]) # Hard code the list is 2 long
            ]
            if q2l > q1l:
                expectedseq1 += [Id(q1, q2l-q1l)]

            expectedseq2 += [
                qsync(),
                qwait(),
                Utheta(q2, amp=a, phase=p),
                MEAS(measChans[1]) # Hard code the list is 2 long
            ]
            if q1l > q2l:
                expectedseq2 += [Id(q2, q1l-q2l)]

        if docals:
            # Add calibration
            cal_q1, cal_q2 = get_cal_seqs_2qubits(q1, q2, calRepeats)
            expectedseq1 += cal_q1
            expectedseq2 += cal_q2

        # Get rid of any 0 length Id pulses just added
        discard_zero_Ids([expectedseq1, expectedseq2])

        # from pyqgl2.ast_util import NodeError
        # from pyqgl2.debugmsg import DebugMsg
        # NodeError.MUTE_ERR_LEVEL = NodeError.NODE_ERROR_NONE
        # DebugMsg.set_level(0)
        # import logging
        # from QGL.Compiler import set_log_level
        # # Note this acts on QGL.Compiler at DEBUG by default
        # # Could specify other levels, loggers
        # set_log_level()

        resFunction = compileFunction("src/python/qgl2/basic_sequences/RabiMin.py",
                                      "doRabiAmp_NQubits",
                                      (amps, docals, calRepeats))
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        # Need to map right seq to right expected seq
        self.assertEqual(len(seqs), 2)
        self.maxDiff = None
        if seqs[0][2] == Utheta(q1, amp=amps[0], phase=p):
            assertPulseSequenceEqual(self, seqs[0], expectedseq1)
            assertPulseSequenceEqual(self, seqs[1], expectedseq2)
        else:
            assertPulseSequenceEqual(self, seqs[1], expectedseq1)
            assertPulseSequenceEqual(self, seqs[0], expectedseq2)

    # Swap that does the Xs and Id as fast as possible
    # Note we don't understand the QGL1 function, so
    # this test isn't strictly necessary.
    def test_Swap(self):
        q = QubitFactory('q1')
        mq = QubitFactory('q2')
        delays = np.linspace(0, 5e-6, 11)
        expectedseq1 = []
        expectedseq2 = []
        for d in delays:
            x1l = X(q).length
            x2l = X(mq).length
            expectedseq1 += [
                qsync(),
                qwait(),
                X(q)]
            # Pause for mq if necessary
            if x2l+d > x1l:
                expectedseq1 += [Id(q, x2l+d-x1l)]
            expectedseq1 += [
                MEAS(q)
            ]

            expectedseq2 += [
                qsync(),
                qwait(),
                X(mq),
                Id(mq, d)
            ]
            # Pause for q if necessary
            if x1l > x2l+d:
                expectedseq2 += [Id(mq, x1l-x2l-d)]
            expectedseq2 += [
                MEAS(mq)
            ]

        # Add calibration
        cal_q2, cal_q1 = get_cal_seqs_2qubits(mq, q, 2)
        expectedseq1 += cal_q1
        expectedseq2 += cal_q2

        # Get rid of any 0 length Id pulses just added
        discard_zero_Ids([expectedseq1, expectedseq2])

        # from pyqgl2.ast_util import NodeError
        # from pyqgl2.debugmsg import DebugMsg
        # NodeError.MUTE_ERR_LEVEL = NodeError.NODE_ERROR_NONE
        # DebugMsg.set_level(0)
        # import logging
        # from QGL.Compiler import set_log_level
        # # Note this acts on QGL.Compiler at DEBUG by default
        # # Could specify other levels, loggers
        # set_log_level()

        # Add final True arg for debugging
        resFunction = compileFunction("src/python/qgl2/basic_sequences/RabiMin.py",
                                      "doSwap",
                                      (q, mq, delays))
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        # Need to map right seq to right expected seq
        self.assertEqual(len(seqs), 2)
        # self.maxDiff = None
        if seqs[0][2] == X(q):
            assertPulseSequenceEqual(self, seqs[0], expectedseq1)
            assertPulseSequenceEqual(self, seqs[1], expectedseq2)
        else:
            assertPulseSequenceEqual(self, seqs[1], expectedseq1)
            assertPulseSequenceEqual(self, seqs[0], expectedseq2)

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
        resFunction = compileFunction("src/python/qgl2/basic_sequences/SPAMMin.py",
                                      "doSPAM")
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        assertPulseSequenceEqual(self, seqs[0], expectedseq)

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

        # Get rid of any 0 length Id pulses just added
        discard_zero_Ids([expectedseq])
        resFunction = compileFunction("src/python/qgl2/basic_sequences/T1T2Min.py",
                                      "doInversionRecovery")
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        assertPulseSequenceEqual(self, seqs[0], expectedseq)

    def test_Ramsey(self):
        q = QubitFactory('q1')
        pulseSpacings=np.arange(100e-9, 10e-6, 100e-9)
        TPPIFreq=1e6 # 0
        calRepeats = 2
        expectedseq = []

        # Create the phases for the TPPI
        phases = 2*pi*TPPIFreq*pulseSpacings

        # Create the basic Ramsey sequence
        for d,phase in zip(pulseSpacings, phases):
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

        # Get rid of any 0 length Id pulses just added
        discard_zero_Ids([expectedseq])

        resFunction = compileFunction("src/python/qgl2/basic_sequences/T1T2Min.py",
                                      "doRamsey")
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        assertPulseSequenceEqual(self, seqs[0], expectedseq)

    def test_Ramsey_list(self):
        # Test Ramsey putting the zip() call in a list()
        q = QubitFactory('q1')
        pulseSpacings=np.arange(100e-9, 10e-6, 100e-9)
        TPPIFreq=1e6 # 0
        calRepeats = 2
        expectedseq = []

        # Create the phases for the TPPI
        phases = 2*pi*TPPIFreq*pulseSpacings

        # Create the basic Ramsey sequence
        for d,phase in zip(pulseSpacings, phases):
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

        # Get rid of any 0 length Id pulses just added
        discard_zero_Ids([expectedseq])

        resFunction = compileFunction(
                "src/python/qgl2/basic_sequences/T1T2Min.py",
                "doRamsey_list")
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        assertPulseSequenceEqual(self, seqs[0], expectedseq)

if __name__ == '__main__':
    # To test everything in this file (say, using cProfile)
    unittest.main("test.test_basic_mins")
    # To run just 1 test from this file
    # Note that SPAM and FlipFlop and EchoCRPhase are the 3 slowest tests (in that order)
#    unittest.main("test.test_basic_mins", "TestBasicMins.test_AllXY")
#    unittest.main("test.test_basic_mins", "TestBasicMins.test_SPAM")
#    unittest.main("test.test_basic_mins", "TestBasicMins.test_RabiWidth")
#    unittest.main("test.test_basic_mins", "TestBasicMins.test_HahnEcho")
#    unittest.main("test.test_basic_mins", "TestBasicMins.test_CPMG")
