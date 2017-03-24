# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
Test syndrome calculations
"""

import unittest

from .helpers import testable_sequence, channel_setup
from .helpers import assertPulseSequenceEqual

from pyqgl2.main import compile_function

from QGL import *

class TestMulti(unittest.TestCase):
    def setUp(self):
        channel_setup()

    def tearDown(self):
        pass

    def test_syn_0(self):
        """
        This is just a basic test to see whether the preprocessor
        accepts the simple syndrome code
        """

        resFunction = compile_function('test/code/syndrome/syndrome.py', 'main')
        self.assertTrue(resFunction)


    def test_syn_1(self):
        """
        This is just a basic test to see whether the preprocessor
        accepts the simple syndrome code

        TODO: currently fails with an error in compile_to_hardware,
        because we don't have all the qbits in our channel library,
        so all we do is compile_function and look at the sequences
        """

        resFunction = compile_function('test/code/syndrome/syndrome.py', 'main')
        self.assertTrue(resFunction)

        seqs = resFunction()
        seqs = testable_sequence(seqs)

        # TODO: do something with the resulting sequences

        """
        for seq in seqs:
            print('\n'.join([str(x) for x in seq]))
            print('------')
        """
