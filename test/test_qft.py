# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import unittest

# Test functions in multi.py

from pyqgl2.main import compile_function
from test.helpers import channel_setup, testable_sequence

from test.helpers import testable_sequence, discard_zero_Ids, \
    flattenSeqs, channel_setup, assertPulseSequenceEqual, \
    get_cal_seqs_1qubit, get_cal_seqs_2qubits

from QGL import *

class TestQFT(unittest.TestCase):
    def setUp(self):
        channel_setup()

    def tearDown(self):
        pass

    def test_qft(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        qs = [q1, q2]

        resFunction = compile_function('test/code/qft.py', 'qft', (qs,))
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        # expected_seq = H(q1) + CZ_k(q1, q2, pi) + H(q2) + [MEAS(q1)*MEAS(q2)]
        expected_seq0 = H(q1) + \
                        CNOT_CR(q1, q2) + CNOT_CR(q1, q2) + \
                        [Id(q1, length=60e-9)] + \
                        [MEAS(q1)]
        expected_seq1 = [Id(q2, length=60e-9)] + \
                        [Ztheta(q2, pi/2)] + CNOT_CR(q1, q2) + [Ztheta(q2, -pi/2)] + CNOT_CR(q1, q2) + \
                        H(q2) + \
                        [MEAS(q2)]

        assertPulseSequenceEqual(self, seqs[0], expected_seq0)
        assertPulseSequenceEqual(self, seqs[1], expected_seq1)

def H(q):
    return [Y90(q), X(q)]
