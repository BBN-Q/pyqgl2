import unittest
import numpy as np
from itertools import product

from pyqgl2.main import compile_function
from QGL import *

from test.helpers import testable_sequence, discard_zero_Ids, \
    channel_setup, assertPulseSequenceEqual

class TestCompiler(unittest.TestCase):
    def setUp(self):
        channel_setup()

    def tearDown(self):
        pass

    def test_tomo(self):
        resFunction = compile_function("test/code/tomo.py", "main")
        seqs = resFunction()

        expectedseq = self.tomo_result()

        assertPulseSequenceEqual(self, seqs, expectedseq)

    def test_tomo_no_generators(self):
        resFunction = compile_function("test/code/tomo.py", "main_no_generators")
        seqs = resFunction()

        expectedseq = self.tomo_result()

        assertPulseSequenceEqual(self, seqs, expectedseq)

    def tomo_result(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        fncs = [Id, X90, Y90, X]

        expectedseq = []
        for (p1, p2) in product(fncs, fncs):
            for (m1, m2) in product(fncs, fncs):
                expectedseq += [
                    p1(q1),
                    p2(q2),
                    X90(q1),
                    Y90(q2),
                    m1(q1),
                    m2(q2),
                    MEAS(q1),
                    MEAS(q2)
                ]
        return expectedseq
