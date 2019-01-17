# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.
import unittest

# Test functions in edge.py

from .helpers import testable_sequence, \
    channel_setup, assertPulseSequenceEqual
from pyqgl2.main import compile_function

from QGL import *
from QGL.PatternUtils import flatten

class TestEdge(unittest.TestCase):
    def setUp(self):
        channel_setup()

    def tearDown(self):
        pass

    def test_edgeTest(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        expected = [
            qwait(channels=(q1, q2)),
            X(q1),
            X(q2),
            echoCR(q1, q2)
        ]
        expected = testable_sequence(expected)

        resFunction = compile_function("test/code/edge.py",
                                      "edgeTest")
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        assertPulseSequenceEqual(self, seqs, expected)

    def test_edgeTest3(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        expected = [
            qwait(channels=(q1,)),
            qwait(channels=(q2,)),
            echoCR(q1, q2),
            X(q2),
            Y(q2),
            Id(q2),
            X(q2)
        ]
        expected = testable_sequence(expected)

        resFunction = compile_function("test/code/edge.py",
                                      "edgeTest3")
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        self.maxDiff = None
        assertPulseSequenceEqual(self, seqs, expected)

    # requires 2nd edge in opposite direction
    def test_edgeTest4(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')

        expected = [
            qwait(channels=(q1,)),
            qwait(channels=(q2,)),
            echoCR(q1, q2),
            echoCR(q2, q1),
            echoCR(q1, q2),
            X(q1),
            Y(q1),
            Id(q1),
            X(q1)
        ]
        expected = testable_sequence(expected)

        resFunction = compile_function("test/code/edge.py",
                                      "edgeTest4")
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        self.maxDiff = None
        assertPulseSequenceEqual(self, seqs, expected)

    def test_cnotcrTest(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        expected = [
            qwait(channels=(q1,q2)),
            CNOT(q1, q2)
        ]
        expected = testable_sequence(expected)

        resFunction = compile_function("test/code/edge.py",
                                      "cnotcrTest")
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        self.maxDiff = None
        assertPulseSequenceEqual(self, seqs, expected)
