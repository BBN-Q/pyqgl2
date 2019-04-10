# Copyright 2019 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import unittest

from pyqgl2.main import compile_function
from pyqgl2.qreg import QRegister
from pyqgl2.qval import QValue, QValueAllocator
from test.helpers import channel_setup, flattenSeqs, testable_sequence
from test.helpers import assertPulseSequenceEqual

from QGL import *

class TestG24(unittest.TestCase):
    """
    Test the new MEAS() and QValue() stubs
    """

    def setUp(self):
        QValueAllocator._reset()
        channel_setup()

    def tearDown(self):
        pass

    def test_g24_1(self):
        """
        Use QMeas without a QValue, and expect to get the default
        measurement address of 0
        """

        q1 = QubitFactory('q1')

        resFunction = compile_function('test/code/g24.py', 't1')
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expected_seq = [ MEASA(q1, 0) ]

        assertPulseSequenceEqual(self, seqs, expected_seq)

    def test_g24_2(self):
        """
        Use QMeas with a QValue, with the default initial address.
        """

        q1 = QubitFactory('q1')

        resFunction = compile_function('test/code/g24.py', 't2')
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expected_seq = [ MEASA(q1, 16) ]

        assertPulseSequenceEqual(self, seqs, expected_seq)

    def test_g24_3(self):
        """
        Instead of using QMeas, use MEASA directly
        """

        q1 = QubitFactory('q1')

        resFunction = compile_function('test/code/g24.py', 't3')
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expected_seq = [ MEASA(q1, 16) ]

        assertPulseSequenceEqual(self, seqs, expected_seq)

    def test_g24_4(self):
        """
        Try to create two QValues with the same name but different
        sizes; this should raise a NameError
        """

        err_txt = ''
        qv1 = QValue(size=10, name='fred')
        try:
            qv2 = QValue(size=12, name='fred')
        except NameError as exc:
            err_txt = str(exc)

        self.assertNotEqual('', err_txt)
        self.assertEqual(
                err_txt, 'cannot change size of QValue (fred) from 10 to 12')

    def test_g24_5(self):
        """
        Instead of using QMeas, use MEASA directly, but create
        several QValues first.  Use the last one, which should be
        at index 19.
        """

        q1 = QubitFactory('q1')

        resFunction = compile_function('test/code/g24.py', 't5')
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        expected_seq = [ MEASA(q1, 19) ]

        assertPulseSequenceEqual(self, seqs, expected_seq)

