# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# QGL2 test versions of AllXY

from qgl2.qgl2 import qgl2decl, qbit, concur
from qgl2.util import init
from qgl2.qgl1 import MEAS, QubitFactory

from qgl2.qgl1 import Id, X, Y, X90, Y90

# Helpers here for AllXY that produce pairs of pulses on the same qubit
# Produce the state |0>
@qgl2decl
def IdId(q: qbit):
    # no pulses
    Id(q)
    Id(q)

@qgl2decl
def XX(q: qbit):
    # pulse around same axis
    X(q)
    X(q)

@qgl2decl
def YY(q: qbit):
    # pulse around same axis
    Y(q)
    Y(q)

@qgl2decl
def XY(q: qbit):
    # pulsing around orthogonal axes
    X(q)
    Y(q)

@qgl2decl
def YX(q: qbit):
    # pulsing around orthogonal axes
    Y(q)
    X(q)

# These next produce a |+> or |i> state (equal superposition of |0> + |1>)
@qgl2decl
def X90Id(q: qbit):
    # single pulses
    X90(q)
    Id(q)

@qgl2decl
def Y90Id(q: qbit):
    # single pulses
    Y90(q)
    Id(q)

@qgl2decl
def X90Y90(q: qbit):
    # pulse pairs around orthogonal axes with 1e error sensititivity
    X90(q)
    Y90(q)

@qgl2decl
def Y90X90(q: qbit):
    # pulse pairs around orthogonal axes with 1e error sensititivity
    Y90(q)
    X90(q)

@qgl2decl
def X90Y(q: qbit):
    # pulse pairs with 2e sensitivity
    X90(q)
    Y(q)

@qgl2decl
def Y90X(q: qbit):
    # pulse pairs with 2e sensitivity
    Y90(q)
    X(q)

@qgl2decl
def XY90(q: qbit):
    # pulse pairs with 2e sensitivity
    X(q)
    Y90(q)

@qgl2decl
def YX90(q: qbit):
    # pulse pairs with 2e sensitivity
    Y(q)
    X90(q)

@qgl2decl
def X90X(q: qbit):
    # pulse pairs around common axis with 3e error sensitivity
    X90(q)
    X(q)

@qgl2decl
def XX90(q: qbit):
    # pulse pairs around common axis with 3e error sensitivity
    X(q)
    X90(q)

@qgl2decl
def Y90Y(q: qbit):
    # pulse pairs around common axis with 3e error sensitivity
    Y90(q)
    Y(q)

@qgl2decl
def YY90(q: qbit):
    # pulse pairs around common axis with 3e error sensitivity
    Y(q)
    Y90(q)

# These next create the |1> state
@qgl2decl
def XId(q: qbit):
    # single pulses
    X(q)
    Id(q)

@qgl2decl
def YId(q: qbit):
    # single pulses
    Y(q)
    Id(q)

@qgl2decl
def X90X90(q: qbit):
    # pulse pairs
    X90(q)
    X90(q)

@qgl2decl
def Y90Y90(q: qbit):
    # pulse pairs
    Y90(q)
    Y90(q)

@qgl2decl
def doAllXY(q:qbit):
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
def doAllXY2(q:qbit):
    # one layer of indirection on "func" in the loop below
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
