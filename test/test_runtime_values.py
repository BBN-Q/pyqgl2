import unittest
import numpy as np

from pyqgl2.main import compile_function
from QGL import *
from QGL.ControlFlow import *
from QGL.BlockLabel import label, endlabel

from test.helpers import testable_sequence, channel_setup, \
    assertPulseSequenceEqual, match_labels

class TestRuntimeValues(unittest.TestCase):
    def setUp(self):
        channel_setup()

    def tearDown(self):
        pass

    def reset_result(self, cmp_instr, mask):
        q1 = QubitFactory('q1')

        if_seq = [X(q1)]
        else_seq = [Id(q1)]
        expectedseq = [
            MEAS(q1),
            qwait("CMP"),
            cmp_instr(mask),
            Goto(label(if_seq)),
            else_seq,
            Goto(endlabel(if_seq)),
            if_seq,
            X90(q1)
        ]
        expectedseq = testable_sequence(expectedseq)
        return expectedseq

    def test_reset1(self):
        resFunction = compile_function("test/code/reset.py", "reset1")
        seqs = resFunction()

        expectedseq = self.reset_result(CmpNeq, 0)
        expectedseq = match_labels(expectedseq, seqs)

        assertPulseSequenceEqual(self, seqs, expectedseq)

    def test_reset2(self):
        resFunction = compile_function("test/code/reset.py", "reset2")
        seqs = resFunction()

        expectedseq = self.reset_result(CmpEq, 0)
        expectedseq = match_labels(expectedseq, seqs)

        assertPulseSequenceEqual(self, seqs, expectedseq)

    def test_reset3(self):
        resFunction = compile_function("test/code/reset.py", "reset3")
        seqs = resFunction()

        expectedseq = self.reset_result(CmpEq, 2)
        expectedseq = match_labels(expectedseq, seqs)

        assertPulseSequenceEqual(self, seqs, expectedseq)

    def test_reset4(self):
        resFunction = compile_function("test/code/reset.py", "reset4")
        seqs = resFunction()

        expectedseq = self.reset_result(CmpGt, 1)
        expectedseq = match_labels(expectedseq, seqs)

        assertPulseSequenceEqual(self, seqs, expectedseq)
    def test_reset5(self):
        resFunction = compile_function("test/code/reset.py", "reset5")
        seqs = resFunction()

        expectedseq = self.reset_result(CmpEq, 1)
        # TODO revisit this when QGL2 automatically injects an
        # Id(q1) into the else block.
        # expectedseq = match_labels(expectedseq, seqs)

        # assertPulseSequenceEqual(self, seqs, expectedseq)
