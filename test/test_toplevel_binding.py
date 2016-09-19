import unittest
import numpy as np

from pyqgl2.main import compileFunction
from QGL import *

from .helpers import channel_setup, testable_sequence

class TestTopLevelBinding(unittest.TestCase):
    def setUp(self):
        channel_setup()

    def tearDown(self):
        pass

    def test_main1_dict(self):
        q1 = QubitFactory('q1')
        amps = [1,2,3,4,5]
        expectedseq = [Xtheta(q1, amp=a) for a in amps]

        # dictionary input for toplevel_bindings
        resFunction = compileFunction(
            "src/python/pyqgl2/test/toplevel_binding.py",
            "main1",
            {"amps": amps}
            )
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        self.assertEqual(seqs[0], expectedseq)

    def test_main1_tuple(self):
        q1 = QubitFactory('q1')
        amps = [1,2,3,4,5]
        expectedseq = [Xtheta(q1, amp=a) for a in amps]

        # tuple input for toplevel_bindings
        resFunction = compileFunction(
            "src/python/pyqgl2/test/toplevel_binding.py",
            "main1",
            (amps,)
            )
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        self.assertEqual(seqs[0], expectedseq)

    def test_main1_tuple_range(self):
        q1 = QubitFactory('q1')
        amps = range(5)
        expectedseq = [Xtheta(q1, amp=a) for a in amps]

        # tuple input for toplevel_bindings
        resFunction = compileFunction(
            "src/python/pyqgl2/test/toplevel_binding.py",
            "main1",
            (amps,)
            )
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        self.assertEqual(seqs[0], expectedseq)

    def test_main1_tuple_linspace(self):
        q1 = QubitFactory('q1')
        amps = np.linspace(0, 1, 5)
        expectedseq = [Xtheta(q1, amp=a) for a in amps]

        # tuple input for toplevel_bindings
        resFunction = compileFunction(
            "src/python/pyqgl2/test/toplevel_binding.py",
            "main1",
            (amps,)
            )
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        self.assertEqual(seqs[0], expectedseq)

    def test_main1_tuple_arange(self):
        q1 = QubitFactory('q1')
        amps = np.arange(5)
        expectedseq = [Xtheta(q1, amp=a) for a in amps]

        # tuple input for toplevel_bindings
        resFunction = compileFunction(
            "src/python/pyqgl2/test/toplevel_binding.py",
            "main1",
            (amps,)
            )
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        self.assertEqual(seqs[0], expectedseq)

    def test_main2_dict(self):
        q1 = QubitFactory('q1')
        amps = [1,2,3,4,5]
        expectedseq = [Utheta(q1, amp=a, phase=0.5) for a in amps]

        # dictionary input for toplevel_bindings
        resFunction = compileFunction(
            "src/python/pyqgl2/test/toplevel_binding.py",
            "main2",
            {"amps": amps, "phase": 0.5}
            )
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        self.assertEqual(seqs[0], expectedseq)

    def test_main2_tuple(self):
        q1 = QubitFactory('q1')
        amps = [1,2,3,4,5]
        expectedseq = [Utheta(q1, amp=a, phase=0.5) for a in amps]

        # tuple input for toplevel_bindings
        resFunction = compileFunction(
            "src/python/pyqgl2/test/toplevel_binding.py",
            "main2",
            (amps, 0.5)
            )
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        self.assertEqual(seqs[0], expectedseq)

    def test_main3(self):
        q1 = QubitFactory('q1')
        amps = range(5)
        expectedseq = [Xtheta(q1, amp=a) for a in amps]

        # tuple input for toplevel_bindings
        resFunction = compileFunction(
            "src/python/pyqgl2/test/toplevel_binding.py",
            "main3",
            (q1, amps)
            )
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        self.assertEqual(seqs[0], expectedseq)
