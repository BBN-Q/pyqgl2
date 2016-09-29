# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# Test functions to test end-to-end handling of Barriers & multi qbit sequences

from qgl2.qgl1 import QubitFactory, Id, X, MEAS, Y
from qgl2.qgl2 import qgl2decl, concur, qbit
from qgl2.util import init

@qgl2decl
def multiQbitTest2():
    q1 = QubitFactory('q1')
    q2 = QubitFactory('q2')

    with concur:
        for q in [q1, q2]:
            init(q)
            Id(q)
            X(q)
            MEAS(q)

@qgl2decl
def doSimple():
    q2 = QubitFactory('q2')
    simpleSingle2(q2)

@qgl2decl
def simpleSingle2(q: qbit):
    init(q)
    X(q)
    MEAS(q)

@qgl2decl
def simpleSingle():
    q2 = QubitFactory('q2')
    init(q2)
    X(q2)
    MEAS(q2)

@qgl2decl
def anotherMulti():
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
def anotherMulti2():
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
def anotherMulti3():
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

