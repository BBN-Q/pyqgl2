# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import unittest

# Test functions in multi.py

from pyqgl2.main import compile_function
from test.helpers import channel_setup, testable_sequence

from test.helpers import testable_sequence, discard_zero_Ids, \
    flattenSeqs, channel_setup, assertPulseSequenceEqual, \
    get_cal_seqs_1qubit, get_cal_seqs_2qubits

from QGL import *

class Test84(unittest.TestCase):
    def setUp(self):
        channel_setup()

    def tearDown(self):
        pass

    def test_84_1(self):
        q1 = QubitFactory('q1')
        resFunction = compile_function('test/code/bugs/84.py', 't1')
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expected_seq = [ X(q1) ]

        # print('\n'.join([str(x) for x in seqs]))
        assertPulseSequenceEqual(self, seqs, expected_seq)

    def test_84_2(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        resFunction = compile_function('test/code/bugs/84.py', 't2')
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expected_seq = [ X(q1) ]

        # print('\n'.join([str(x) for x in seqs]))
        assertPulseSequenceEqual(self, seqs, expected_seq)

    def test_84_3(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        resFunction = compile_function('test/code/bugs/84.py', 't3')
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expected_seq = [ X(q1) ]

        # print('\n'.join([str(x) for x in seqs]))
        assertPulseSequenceEqual(self, seqs, expected_seq)

    def test_84_4(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        resFunction = compile_function('test/code/bugs/84.py', 't4')
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expected_seq = [ X(q1) ]

        # print('\n'.join([str(x) for x in seqs]))
        assertPulseSequenceEqual(self, seqs, expected_seq)

    def test_84_5(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        resFunction = compile_function('test/code/bugs/84.py', 't5')
        seqs = resFunction()
        self.assertTrue(len(seqs) == 0)
