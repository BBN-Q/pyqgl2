# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.
import unittest

# Test functions in multi.py

from .helpers import testable_sequence, discard_zero_Ids, \
    channel_setup, assertPulseSequenceEqual
from pyqgl2.main import compile_function

from QGL import *
from qgl2.qgl1control import Barrier

class TestMulti(unittest.TestCase):
    def setUp(self):
        channel_setup()

    def tearDown(self):
        pass

    def test_multiQbitTest2(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        expected = [
            Id(q1),
            X(q1),
            Id(q2),
            X(q2),
            Barrier("", (q1, q2)),
            MEAS(q1),
            MEAS(q2)
        ]

        resFunction = compile_function("test/code/multi.py",
                                      "multiQbitTest2")
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        assertPulseSequenceEqual(self, seqs, expected)

    def test_doSimple(self):
        q2 = QubitFactory('q2')
        expected = [
            X(q2),
            MEAS(q2)
        ]
        resFunction = compile_function("test/code/multi.py",
                                      "doSimple")
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        assertPulseSequenceEqual(self, seqs, expected)

    def test_anotherMulti(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        expected = [
            Id(q1),
            X(q1),
            Id(q2),
            X(q2),
            Barrier("", (q1, q2)),
            MEAS(q1),
            MEAS(q2),
            Y(q1),
            Y(q2)
        ]

        resFunction = compile_function("test/code/multi.py",
                                      "anotherMulti")
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        assertPulseSequenceEqual(self, seqs, expected)

    def test_anotherMulti2(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        q3 = QubitFactory('q3')
        #q1: Id, X, MEAS, <barrier>, Y, <barrier>
        # q2: Id, X, MEAS, <barrier> ?Id?
        # q3: <barrier>, Y, <barrier>
        expected = [
            Id(q1),
            X(q1),
            Id(q2),
            X(q2),
            Barrier("", (q1, q2, q3)),
            MEAS(q1),
            MEAS(q2),
            Barrier("", (q1, q2, q3)),
            Y(q1),
            Y(q3)
        ]

        resFunction = compile_function("test/code/multi.py",
                                      "anotherMulti2")
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        assertPulseSequenceEqual(self, seqs, expected)
