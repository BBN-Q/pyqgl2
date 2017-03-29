import unittest

from pyqgl2.main import compile_function
from QGL import *

from test.helpers import channel_setup, assertPulseSequenceEqual

class TestInliner(unittest.TestCase):
    def setUp(self):
        channel_setup()

    def tearDown(self):
        pass

    def test_scope1(self):
        with self.assertRaises(SystemExit):
            resFunction = compile_function("test/code/scope.py",
                                           "B")

    def test_scope2(self):
        resFunction = compile_function("test/code/scope.py",
                                       "C")
        seqs = resFunction()

        q1 = QubitFactory('q1')

        expectedseq = [
            Xtheta(q1, amp=1),
            Ytheta(q1, amp=0)
        ]

        assertPulseSequenceEqual(self, seqs, expectedseq)
