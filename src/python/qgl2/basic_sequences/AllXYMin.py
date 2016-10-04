# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# QGL2 simplified versions of AllXY

from qgl2.qgl2 import qgl2decl, qbit, concur
from qgl2.util import init
from qgl2.qgl1 import MEAS, QubitFactory
from qgl2.basic_sequences.new_helpers import IdId, XX, YY, XY, YX, X90Id, Y90Id, X90Y90, Y90X90, X90Y, Y90X, \
    XY90, YX90, X90X, XX90, Y90Y, YY90, XId, YId, X90X90, Y90Y90

from qgl2.qgl1 import Id, X, Y, X90, Y90

@qgl2decl
def doAllXY():
    # Temporary qbit to be over-ridden on compilation
    q = QubitFactory(label="q1")

    # For each of the 21 pulse pairs
    for func in [IdId, XX, YY, XY, YX, X90Id, Y90Id,
                 X90Y90, Y90X90, X90Y, Y90X, XY90, YX90, X90X,
                 XX90, Y90Y, YY90, XId, YId, X90X90, Y90Y90]:
        # Repeat it twice and do a MEAS at the end of each
        for i in range(2):
            init(q)
            func(q)
            MEAS(q)

@qgl2decl
def AllXYq2():
    # Temporary qbit to be over-ridden on compilation
    q = QubitFactory(label="q1")

    twentyOnepulseFuncs = [IdId, XX, YY, XY, YX, X90Id, Y90Id,
                           X90Y90, Y90X90, X90Y, Y90X, XY90, YX90, X90X,
                           XX90, Y90Y, YY90, XId, YId, X90X90, Y90Y90]

    # For each of the 21 pulse pairs
    for func in twentyOnepulseFuncs:
        # Repeat it twice and do a MEAS at the end of each
        for i in range(2):
            init(q)
            func(q)
            MEAS(q)

@qgl2decl
def AllXYq3():
    """
    A more qgl2-ish way of doing All-XY
    """

    # Temporary qbit to be over-ridden on compilation
    q = QubitFactory(label="q1")

    twentyOnePulsePairs = [
            (Id, Id), (X, X), (Y, Y),
            (X, Y), (Y, X), (X90, Id), (Y90, Id),
            (Y90, Y90), (Y90, X90),
            (X90, Y), (Y90, X), (X, Y90), (Y, X90),
            (X90, X), (X, X90), (Y90, Y), (Y, Y90),
            (X, Id), (Y, Id),
            (X90, X90), (Y90, Y90) ]

    # For each of the 21 pulse pairs
    for (f1, f2) in twentyOnePulsePairs:
        # Repeat it twice and do a MEAS at the end of each
        for i in range(2):
            init(q)
            f1(q)
            f2(q)
            MEAS(q)
