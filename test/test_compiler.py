import unittest
import numpy as np
from itertools import product

from pyqgl2.main import compileFunction
from QGL import *

from .helpers import channel_setup, testable_sequence

class TestCompiler(unittest.TestCase):
    def setUp(self):
        channel_setup()

    def tearDown(self):
        pass

    @unittest.expectedFailure
    def test_tomo(self):
        resFunction = compileFunction("src/python/pyqgl2/test/tomo.py", "main")
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expectedseq1, expectedseq2 = self.tomo_result()

        self.assertEqual(seqs[0], expectedseq1)
        self.assertEqual(seqs[1], expectedseq2)

    def test_tomo_no_generators(self):
        resFunction = compileFunction("src/python/pyqgl2/test/tomo.py", "main_no_generators")
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expectedseq1, expectedseq2 = self.tomo_result()

        self.assertEqual(seqs[0], expectedseq1)
        self.assertEqual(seqs[1], expectedseq2)

    def tomo_result(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        fncs = [Id, X90, Y90, X]

        expectedseq1 = []
        expectedseq2 = []
        for (p1, p2) in product(fncs, fncs):
            for (m1, m2) in product(fncs, fncs):
                expectedseq1 += [
                    p1(q1),
                    X90(q1),
                    m1(q1),
                    MEAS(q1)
                ]
                expectedseq2 += [
                    p2(q2),
                    Y90(q2),
                    m2(q2),
                    MEAS(q2)
                ]
        return expectedseq1, expectedseq2
