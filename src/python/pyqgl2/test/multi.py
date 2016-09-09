# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# Test functions to test end-to-end handling of Barriers & multi qbit sequences

from qgl2.qgl1 import QubitFactory, Id, X, MEAS, Y
from qgl2.qgl2 import qgl2decl, sequence, concur, seq, qbit
from qgl2.util import init
from qgl2.qgl2_check import QGL2check

@qgl2decl
def multiQbitTest2() -> sequence:
    q1 = QubitFactory('q1')
    q2 = QubitFactory('q2')

    with concur:
        for q in [q1, q2]:
            init(q)
            Id(q)
            X(q)
            MEAS(q)

@qgl2decl
def doSimple() -> sequence:
    q2 = QubitFactory('q2')
    simpleSingle2(q2)

@qgl2decl
def simpleSingle2(q: qbit) -> sequence:
    init(q)
    X(q)
    MEAS(q)

@qgl2decl
def simpleSingle() -> sequence:
    q2 = QubitFactory('q2')
    init(q2)
    X(q2)
    MEAS(q2)

@qgl2decl
def anotherMulti() -> sequence:
    q1 = QubitFactory('q1')
    q2 = QubitFactory('q2')
    with concur:
        for q in [q1, q2]:
            init(q)
            Id(q)
            X(q)
            MEAS(q)
    with concur:
        for q in [q1, q2]:
            Y(q)

@qgl2decl
def anotherMulti2() -> sequence:
    q1 = QubitFactory('q1')
    q2 = QubitFactory('q2')
    q3 = QubitFactory('q3')
    with concur:
        for q in [q1, q2]:
            # Including an init here means a Wait on all but not in q3: fails
            # init(q)
            Id(q)
            X(q)
            MEAS(q)
    with concur:
        for q in [q1, q3]:
            Y(q)

@qgl2decl
def anotherMulti3() -> sequence:
    q1 = QubitFactory('q1')
    q2 = QubitFactory('q2')
    q3 = QubitFactory('q3')
    with concur:
        for q in [q1, q2]:
            # Including an init here means a Wait on all but not in q3: fails
            # init(q)
            Id(q, length=0.000002)
            X(q)
            MEAS(q)
    with concur:
        for q in [q1, q3]:
            Y(q, length=0.000003)

