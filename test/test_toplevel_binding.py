import unittest
import numpy as np

from pyqgl2.main import compile_function
from pyqgl2.qreg import QRegister
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
        resFunction = compile_function(
            "test/code/toplevel_binding.py",
            "main1",
            {"amps": amps}
            )
        seqs = resFunction()

        self.assertEqual(seqs, expectedseq)

    def test_main1_tuple(self):
        q1 = QubitFactory('q1')
        amps = [1,2,3,4,5]
        expectedseq = [Xtheta(q1, amp=a) for a in amps]

        # tuple input for toplevel_bindings
        resFunction = compile_function(
            "test/code/toplevel_binding.py",
            "main1",
            (amps,)
            )
        seqs = resFunction()

        self.assertEqual(seqs, expectedseq)

    def test_main1_tuple_range(self):
        q1 = QubitFactory('q1')
        amps = range(5)
        expectedseq = [Xtheta(q1, amp=a) for a in amps]

        # tuple input for toplevel_bindings
        resFunction = compile_function(
            "test/code/toplevel_binding.py",
            "main1",
            (amps,)
            )
        seqs = resFunction()

        self.assertEqual(seqs, expectedseq)

    def test_main1_tuple_linspace(self):
        q1 = QubitFactory('q1')
        amps = np.linspace(0, 1, 5)
        expectedseq = [Xtheta(q1, amp=a) for a in amps]

        # tuple input for toplevel_bindings
        resFunction = compile_function(
            "test/code/toplevel_binding.py",
            "main1",
            (amps,)
            )
        seqs = resFunction()

        self.assertEqual(seqs, expectedseq)

    def test_main1_tuple_arange(self):
        q1 = QubitFactory('q1')
        amps = np.arange(5)
        expectedseq = [Xtheta(q1, amp=a) for a in amps]

        # tuple input for toplevel_bindings
        resFunction = compile_function(
            "test/code/toplevel_binding.py",
            "main1",
            (amps,)
            )
        seqs = resFunction()

        self.assertEqual(seqs, expectedseq)

    def test_main2_dict(self):
        q1 = QubitFactory('q1')
        amps = [1,2,3,4,5]
        expectedseq = [Utheta(q1, amp=a, phase=0.5) for a in amps]

        # dictionary input for toplevel_bindings
        resFunction = compile_function(
            "test/code/toplevel_binding.py",
            "main2",
            {"amps": amps, "phase": 0.5}
            )
        seqs = resFunction()

        self.assertEqual(seqs, expectedseq)

    def test_main2_tuple(self):
        q1 = QubitFactory('q1')
        amps = [1,2,3,4,5]
        expectedseq = [Utheta(q1, amp=a, phase=0.5) for a in amps]

        # tuple input for toplevel_bindings
        resFunction = compile_function(
            "test/code/toplevel_binding.py",
            "main2",
            (amps, 0.5)
            )
        seqs = resFunction()

        self.assertEqual(seqs, expectedseq)

    def test_main3(self):
        # add a qubit input
        q1 = QubitFactory('q1')
        qr = QRegister('q1')
        amps = range(5)
        expectedseq = [Xtheta(q1, amp=a) for a in amps]

        # tuple input for toplevel_bindings
        resFunction = compile_function(
            "test/code/toplevel_binding.py",
            "main3",
            (qr, amps)
            )
        seqs = resFunction()

        self.assertEqual(seqs, expectedseq)

    def test_main4(self):
        # add a function handle as an input
        q1 = QubitFactory('q1')
        qr = QRegister('q1')
        amps = range(5)
        expectedseq = [Xtheta(q1, amp=a, shapeFun=PulseShapes.tanh) for a in amps]

        # tuple input for toplevel_bindings
        resFunction = compile_function(
            "test/code/toplevel_binding.py",
            "main4",
            (qr, amps, PulseShapes.tanh)
            )
        seqs = resFunction()

        self.assertEqual(seqs, expectedseq)

    def test_main5(self):
        # qbit_list
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        qs = [q1, q2]
        qr1 = QRegister('q1')
        qr2 = QRegister('q2')
        qrs = [qr1, qr2]
        expectedseq = [X(q1), X(q2)]

        # tuple input for toplevel_bindings
        resFunction = compile_function(
            "test/code/toplevel_binding.py",
            "main5",
            (qrs,)
            )
        seqs = resFunction()

        self.assertEqual(seqs, expectedseq)

    def test_main5b(self):
        # TODO this doesn't actually match the signature of "main5",
        # because a QRegister is not a qbit_list (at least not as
        # currently defined). Should this throw an error?
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        qs = [q1, q2]
        qr = QRegister('q1', 'q2')
        expectedseq = [X(q1), X(q2)]

        # tuple input for toplevel_bindings
        resFunction = compile_function(
            "test/code/toplevel_binding.py",
            "main5",
            (qr,)
            )
        seqs = resFunction()

        self.assertEqual(seqs, expectedseq)
