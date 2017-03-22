# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import unittest

# Test functions in multi.py

from pyqgl2.main import compile_function
from test.helpers import channel_setup, testable_sequence

from test.helpers import testable_sequence, discard_zero_Ids, \
    flattenSeqs, channel_setup, assertPulseSequenceEqual, \
    get_cal_seqs_1qubit, get_cal_seqs_2qubits

from QGL import *

class Test90(unittest.TestCase):
    def setUp(self):
        channel_setup()

    def tearDown(self):
        pass

    def test_90_1(self):
        q1 = QubitFactory('q1')
        resFunction = compile_function('test/code/bugs/90.py', 't1')
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expected_seq = [ X(q1) ]
        assertPulseSequenceEqual(self, seqs[0], expected_seq)
        # print('\n'.join([str(x) for x in seqs[0]]))

    def test_90_2(self):
        q1 = QubitFactory('q1')
        resFunction = compile_function('test/code/bugs/90.py', 't2')
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expected_seq = [ X(q1) ]
        assertPulseSequenceEqual(self, seqs[0], expected_seq)
        # print('\n'.join([str(x) for x in seqs[0]]))

    def test_90_3(self):
        q1 = QubitFactory('q1')
        resFunction = compile_function('test/code/bugs/90.py', 't3')
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expected_seq = [ X(q1) ]
        assertPulseSequenceEqual(self, seqs[0], expected_seq)
        # print('\n'.join([str(x) for x in seqs[0]]))

    def test_90_4(self):
        q1 = QubitFactory('q1')
        resFunction = compile_function('test/code/bugs/90.py', 't4')
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expected_seq = [ X(q1) ] * 3
        expected_seq += [ Y(q1) ] * 2
        assertPulseSequenceEqual(self, seqs[0], expected_seq)
        # print('\n'.join([str(x) for x in seqs[0]]))

