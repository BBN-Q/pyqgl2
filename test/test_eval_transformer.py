import unittest
import numpy as np
from itertools import product

from pyqgl2.main import compile_function
from QGL import *

from test.helpers import testable_sequence, \
    channel_setup, assertPulseSequenceEqual

class TestEvalTransformer(unittest.TestCase):
    def setUp(self):
        channel_setup()

    def tearDown(self):
        pass

    def test_classical_continue(self):
        resFunction = compile_function("test/code/loops.py",
                                       "classical_continue")
        seqs = resFunction()

        q1 = QubitFactory('q1')

        expectedseq = [
            X(q1), # start of ct == 0
            Y90(q1),
            X(q1), # start of ct == 1
            X90(q1),
            X(q1), # start of ct == 2
            X90(q1)
        ]

        assertPulseSequenceEqual(self, seqs, expectedseq)

    def test_classical_break(self):
        resFunction = compile_function("test/code/loops.py",
                                       "classical_break")
        seqs = resFunction()

        q1 = QubitFactory('q1')

        expectedseq = [
            X(q1), # start of ct == 0
            Y90(q1),
            X(q1), # start of ct == 1
            X90(q1) # then break
        ]

        assertPulseSequenceEqual(self, seqs, expectedseq)
