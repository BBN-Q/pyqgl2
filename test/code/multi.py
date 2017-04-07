# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# Test functions to test end-to-end handling of Barriers & multi qbit sequences

from qgl2.qgl1 import Id, X, MEAS, Y, Barrier
from qgl2.qgl2 import qgl2decl, qbit, QRegister
from qgl2.util import init

@qgl2decl
def multiQbitTest2():
    q1 = QRegister('q1')
    q2 = QRegister('q2')

    for q in [q1, q2]:
        Id(q)
        X(q)
    Barrier("", (q1, q2))
    for q in [q1, q2]:
        MEAS(q)

@qgl2decl
def doSimple():
    q2 = QRegister('q2')
    simpleSingle2(q2)

@qgl2decl
def simpleSingle2(q: qbit):
    X(q)
    MEAS(q)

@qgl2decl
def simpleSingle():
    q2 = QRegister('q2')
    X(q2)
    MEAS(q2)

@qgl2decl
def anotherMulti():
    q1 = QRegister('q1')
    q2 = QRegister('q2')
    for q in [q1, q2]:
        Id(q)
        X(q)
    Barrier("", (q1, q2))
    for q in [q1, q2]:
        MEAS(q)
    for q in [q1, q2]:
        Y(q)

@qgl2decl
def anotherMulti2():
    q1 = QRegister('q1')
    q2 = QRegister('q2')
    q3 = QRegister('q3')
    for q in [q1, q2]:
        Id(q)
        X(q)
    Barrier("", (q1, q2, q3))
    for q in [q1, q2]:
        MEAS(q)
    Barrier("", (q1, q2, q3))
    for q in [q1, q3]:
        Y(q)
