# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.
import unittest

# Test functions in multi.py

from .helpers import testable_sequence, discard_zero_Ids
from pyqgl2.main import compileFunction
from pyqgl2.channelSetup import channel_setup
from QGL import *

class TestMulti(unittest.TestCase):
    def setUp(self):
        channel_setup()

    def tearDown(self):
        pass

    def test_multiQbitTest2(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        expectedseq1 = [
            qsync(),
            qwait(),
            Id(q1),
            X(q1),
            MEAS(q1)
        ]
        q1l = Id(q1).length + X(q1).length + MEAS(q1).length

        expectedseq2 = [
            qsync(),
            qwait(),
            Id(q2),
            X(q2),
            MEAS(q2)
        ]
        q2l = Id(q2).length + X(q2).length + MEAS(q2).length
        if q1l > q2l:
            expectedseq2 += [Id(q2, q1l-q2l)]
        elif q2l > q1l:
            expectedseq1 += [Id(q1, q2l-q1l)]

        resFunction = compileFunction("src/python/pyqgl2/test/multi.py",
                                      "multiQbitTest2")
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        self.assertEqual(len(seqs), 2)
        if seqs[0][2] == Id(q1):
            self.assertEqual(seqs[0], expectedseq1)
            self.assertEqual(seqs[1], expectedseq2)
        else:
            self.assertEqual(seqs[0], expectedseq2)
            self.assertEqual(seqs[1], expectedseq1)

    def test_doSimple(self):
        q2 = QubitFactory('q2')
        expected = [
            qsync(),
            qwait(),
            X(q2),
            MEAS(q2)
        ]
        resFunction = compileFunction("src/python/pyqgl2/test/multi.py",
                                      "doSimple")
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        self.assertEqual(len(seqs), 1)
        self.assertEqual(seqs[0], expected)

    def test_anotherMulti(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        expectedseq1 = [
            qsync(),
            qwait(),
            Id(q1),
            X(q1),
            MEAS(q1)
        ]
        q1l = Id(q1).length + X(q1).length + MEAS(q1).length
        expectedseq2 = [
            qsync(),
            qwait(),
            Id(q2),
            X(q2),
            MEAS(q2)
        ]
        q2l = Id(q2).length + X(q2).length + MEAS(q2).length
        if q1l > q2l:
            expectedseq2 += [Id(q2, q1l-q2l)]
        elif q2l > q1l:
            expectedseq1 += [Id(q1, q2l-q1l)]
        expectedseq1 += [ Y(q1) ]
        expectedseq2 += [ Y(q2) ]
        q1l = Y(q1).length
        q2l = Y(q2).length
        if q1l > q2l:
            expectedseq2 += [Id(q2, q1l - q2l)]
        elif q2l > q1l:
            expectedseq2 += [Id(q1, q2l - q1l)]

        resFunction = compileFunction("src/python/pyqgl2/test/multi.py",
                                      "anotherMulti")
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        self.assertEqual(len(seqs), 2)
        if seqs[0][2] == Id(q1):
            self.assertEqual(seqs[0], expectedseq1)
            self.assertEqual(seqs[1], expectedseq2)
        else:
            self.assertEqual(seqs[0], expectedseq2)
            self.assertEqual(seqs[1], expectedseq1)

    def test_anotherMulti2(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        q3 = QubitFactory('q3')
        #q1: Id, X, MEAS, <barrier>, Y, <barrier>
        # q2: Id, X, MEAS, <barrier> ?Id?
        # q3: <barrier>, Y, <barrier>
        expected1 = [
            Id(q1),
            X(q1),
            MEAS(q1)
        ]
        q1l = Id(q1).length + X(q1).length + MEAS(q1).length
        expected2 = [
            Id(q2),
            X(q2),
            MEAS(q2)
        ]
        q2l = Id(q2).length + X(q2).length + MEAS(q2).length
        if q1l > q2l:
            expected2 += [Id(q2, q1l-q2l)]
        elif q2l > q1l:
            expected1 += [Id(q1, q2l-q1l)]
        expected1 += [Y(q1)]
        expected3 = [
            Id(q3, q1l),
            Y(q3)
        ]
        q1l = Y(q1).length
        q3l = Y(q3).length
        if q1l > q3l:
            expected3 += [Id(q3, q1l - q3l)]
        elif q3l > q1l:
            expected1 += [Id(q1, q3l - q1l)]
        expected2 += [Id(q2, max(q1l, q3l))]
        resFunction = compileFunction("src/python/pyqgl2/test/multi.py",
                                      "anotherMulti2")
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        self.maxDiff = None
        self.assertEqual(len(seqs), 3)
        if seqs[0][0] == Id(q1):
            self.assertEqual(seqs[0], expected1)
            if seqs[1][0] == Id(q2):
                self.assertEqual(seqs[1], expected2)
                self.assertEqual(seqs[2], expected3)
            else:
                self.assertEqual(seqs[1], expected3)
                self.assertEqual(seqs[2], expected2)
        elif seqs[1][0] == Id(q1):
            self.assertEqual(seqs[1], expected1)
            if seqs[0][0] == Id(q2):
                self.assertEqual(seqs[0], expected2)
                self.assertEqual(seqs[2], expected3)
            else:
                self.assertEqual(seqs[0], expected3)
                self.assertEqual(seqs[2], expected2)
        else:
            self.assertEqual(seqs[2], expected1)
            if seqs[0][0] == Id(q2):
                self.assertEqual(seqs[0], expected2)
                self.assertEqual(seqs[1], expected3)
            else:
                self.assertEqual(seqs[0], expected3)
                self.assertEqual(seqs[1], expected2)

    def test_anotherMulti3(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        q3 = QubitFactory('q3')
        #q1: Id, X, MEAS, <barrier>, Y, <barrier>
        # q2: Id, X, MEAS, <barrier> ?Id?
        # q3: <barrier>, Y, <barrier>
        expected1 = [
            Id(q1, length=0.000002),
            X(q1),
            MEAS(q1)
        ]
        q1l = Id(q1, length=0.000002).length + X(q1).length + MEAS(q1).length
        expected2 = [
            Id(q2, length=0.000002),
            X(q2),
            MEAS(q2)
        ]
        q2l = Id(q2, length=0.000002).length + X(q2).length + MEAS(q2).length
        if q1l > q2l:
            expected2 += [Id(q2, q1l-q2l)]
        elif q2l > q1l:
            expected1 += [Id(q1, q2l-q1l)]
        expected1 += [Y(q1, length=0.000003)]
        expected3 = [
            Id(q3, q1l),
            Y(q3, length=0.000003)
        ]
        q1l = Y(q1, length=0.000003).length
        q3l = Y(q3, length=0.000003).length
        if q1l > q3l:
            expected3 += [Id(q3, q1l - q3l)]
        elif q3l > q1l:
            expected1 += [Id(q1, q3l - q1l)]
        expected2 += [Id(q2, max(q1l, q3l))]
        resFunction = compileFunction("src/python/pyqgl2/test/multi.py",
                                      "anotherMulti3")
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        self.maxDiff = None
        self.assertEqual(len(seqs), 3)
        if seqs[0][0] == Id(q1, length=0.000002):
            self.assertEqual(seqs[0], expected1)
            if seqs[1][0] == Id(q2, length=0.000002):
                self.assertEqual(seqs[1], expected2)
                self.assertEqual(seqs[2], expected3)
            else:
                self.assertEqual(seqs[1], expected3)
                self.assertEqual(seqs[2], expected2)
        elif seqs[1][0] == Id(q1, length=0.000002):
            self.assertEqual(seqs[1], expected1)
            if seqs[0][0] == Id(q2, length=0.000002):
                self.assertEqual(seqs[0], expected2)
                self.assertEqual(seqs[2], expected3)
            else:
                self.assertEqual(seqs[0], expected3)
                self.assertEqual(seqs[2], expected2)
        else:
            self.assertEqual(seqs[2], expected1)
            if seqs[0][0] == Id(q2, length=0.000002):
                self.assertEqual(seqs[0], expected2)
                self.assertEqual(seqs[1], expected3)
            else:
                self.assertEqual(seqs[0], expected3)
                self.assertEqual(seqs[1], expected2)

