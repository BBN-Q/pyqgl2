# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import unittest

from pyqgl2.main import compileFunction
from test.helpers import channel_setup, testable_sequence

from test.helpers import testable_sequence, discard_zero_Ids, \
    flattenSeqs, channel_setup, assertPulseSequenceEqual, \
    get_cal_seqs_1qubit, get_cal_seqs_2qubits

from QGL import *

class Test55(unittest.TestCase):
    """
    Test that += and array operations work correctly
    (without making a spare copy of the local state)
    """

    def setUp(self):
        channel_setup()

    def tearDown(self):
        pass

    def test_55_1(self):
        q1 = QubitFactory('q1')

        resFunction = compileFunction('test/code/bugs/55.py', 't1')
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expected_seq = [ X(q1), X(q1) ]

        # print('\n'.join([str(x) for x in seqs[0]]))
        assertPulseSequenceEqual(self, seqs[0], expected_seq)

    def test_55_2(self):
        q1 = QubitFactory('q1')

        resFunction = compileFunction('test/code/bugs/55.py', 't2')
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expected_seq = [ X(q1), X(q1), X(q1), X(q1) ]

        # print('\n'.join([str(x) for x in seqs[0]]))
        assertPulseSequenceEqual(self, seqs[0], expected_seq)

    def test_55_3(self):
        q1 = QubitFactory('q1')

        resFunction = compileFunction('test/code/bugs/55.py', 't3')
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expected_seq = [ X(q1), X(q1), X(q1) ]

        # print('\n'.join([str(x) for x in seqs[0]]))
        assertPulseSequenceEqual(self, seqs[0], expected_seq)


    @unittest.expectedFailure
    def test_55_4(self):
        """
        Test of list.append()

        This doesn't work right now: this is a kind of function call
        we don't understand.  It would be desirable to do so.
        """

        q1 = QubitFactory('q1')

        resFunction = compileFunction('test/code/bugs/55.py', 't4')
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expected_seq = [ X(q1), Y(q1), Y(q1), Z(q1), Z(q1), Z(q1), Z(q1) ]

        # print('\n'.join([str(x) for x in seqs[0]]))
        assertPulseSequenceEqual(self, seqs[0], expected_seq)

