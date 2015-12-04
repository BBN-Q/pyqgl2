# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
Definitions related to QGL2 "built-in" functions
"""

class QGL2Functions(object):
    """
    Wrapping this up in a class to avoid cluttering the namespace
    """

    # This is just a smattering of possible waveforms.
    # (I'm not sure whether these are even correct, or
    # meaningful, but they're good enough for test cases)
    #
    UNI_WAVEFORMS = set([
        'MEAS',
        'X', 'X90', 'X180',
        'Y', 'Y90', 'Y180',
        'Z', 'Z90', 'Z180',
        'UTheta'])

    # Like UNI_WAVEFORMS, BI_OPS is fictitious
    #
    BI_OPS = set(['SWAP'])

