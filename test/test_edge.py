# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.
import unittest

# Test functions in edge.py

from .helpers import testable_sequence, discard_zero_Ids, channel_setup
from pyqgl2.main import compileFunction

from QGL import *
from QGL.PatternUtils import flatten

class TestEdge(unittest.TestCase):
    def setUp(self):
        channel_setup()

    def tearDown(self):
        pass

    def test_edgeTest(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        expected1 = [
            qsync(),
            qwait(),
            X(q1)
        ]
        q1l = X(q1).length
        expected2 = [
            qsync(),
            qwait(),
            X(q2)
        ]
        q2l = X(q2).length
        if q1l > q2l:
            expected2 += [Id(q2, length=q1l-q2l)]
        elif q2l > q1l:
            expected1 += [Id(q1, length=q2l-q1l)]
        for el in echoCR(q1, q2):
            expected1 += [el]
            expected2 += [el]
        resFunction = compileFunction("src/python/pyqgl2/test/edge.py",
                                      "edgeTest")
        seqs = resFunction()
        seqs = testable_sequence(seqs)
#        self.maxDiff = None
        self.assertEqual(len(seqs), 2)
        if seqs[0][2] == X(q1):
            self.assertEqual(seqs[0], expected1)
            self.assertEqual(seqs[1], expected2)
        else:
            self.assertEqual(seqs[0], expected2)
            self.assertEqual(seqs[1], expected1)

    def test_edgeTest3(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        expected1 = [
            qsync(),
            qwait()
        ]
        expected2 = [
            qsync(),
            qwait()
        ]
        for el in echoCR(q1, q2):
            expected1 += [el]
            expected2 += [el]
        expected2 += [
            X(q2),
            Y(q2),
            Id(q2),
            X(q2)
        ]
        # Need q1 to pause so they end together.
        # I would think 1 pause for all 4 works. But
        # we're getting 4 pauses, as QGL2 has made each pulse
        # sequential requiring q1 to be in sync at every step.
        expected1 += [Id(q1, X(q2).length), Id(q1, Y(q2).length),
                      Id(q1, Id(q2).length), Id(q1, X(q2).length)]

        resFunction = compileFunction("src/python/pyqgl2/test/edge.py",
                                      "edgeTest3")
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        self.maxDiff = None
        self.assertEqual(len(seqs), 2)
        if seqs[0][-1] == X(q2):
            self.assertEqual(seqs[0], expected2)
            self.assertEqual(seqs[1], expected1)
        else:
            self.assertEqual(seqs[0], expected1)
            self.assertEqual(seqs[1], expected2)

    # requires 2nd edge in opposite direction
    def test_edgeTest4(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')

        expected1 = [
            qsync(),
            qwait()
        ]
        expected2 = [
            qsync(),
            qwait()
        ]
        for el in echoCR(q1, q2):
            expected1 += [el]
            expected2 += [el]
        for el in echoCR(q2, q1):
            expected1 += [el]
            expected2 += [el]
        for el in echoCR(q1, q2):
            expected1 += [el]
            expected2 += [el]
        expected1 += [
            X(q1),
            Y(q1),
            Id(q1),
            X(q1)
        ]
        # Need q2 to pause so they end together.
        # I would think 1 pause for all 4 works. But
        # we're getting 4 pauses, as QGL2 has made each pulse
        # sequential requiring q2 to be in sync at every step.
        expected2 += [Id(q2, X(q1).length), Id(q2, Y(q1).length),
                      Id(q2, Id(q1).length), Id(q2, X(q1).length)]

        resFunction = compileFunction("src/python/pyqgl2/test/edge.py",
                                      "edgeTest4")
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        self.maxDiff = None
        self.assertEqual(len(seqs), 2)
        if seqs[0][-1] == X(q1):
            self.assertEqual(seqs[0], expected1)
            self.assertEqual(seqs[1], expected2)
        else:
            self.assertEqual(seqs[0], expected2)
            self.assertEqual(seqs[1], expected1)

    def test_cnotcrTest(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        exp1 = [
            qsync(),
            qwait()
        ]
        exp2 = [
            qsync(),
            qwait()
        ]
        for el in CNOT_CR(q1, q2):
            exp1 += [el]
            exp2 += [el]
        resFunction = compileFunction("src/python/pyqgl2/test/edge.py",
                                      "cnotcrTest")
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        self.maxDiff = None
        self.assertEqual(len(seqs), 2)
        self.assertEqual(seqs[0], exp1)
        self.assertEqual(seqs[1], exp2)


