# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# Test functions to test end-to-end handling of Barriers & multi qbit sequences

from qgl2.qgl1 import Id, X, MEAS, Y, Barrier
from qgl2.qgl2 import qgl2decl, qbit, QRegister
from qgl2.util import init

@qgl2decl
def multiQbitTest2():
    qs = QRegister('q1', 'q2')

    Id(qs)
    X(qs)
    Barrier("", (qs,))
    MEAS(qs)

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
    qs = QRegister(2)
    Id(qs)
    X(qs)
    Barrier("", (qs,))
    MEAS(qs)
    Y(qs)

@qgl2decl
def anotherMulti2():
    qs = QRegister(3)
    qsub = QRegister(qs[0], qs[1])
    Id(qsub)
    X(qs[0:2]) # equivalent to calling with qsub argument
    Barrier("", (qs,))
    MEAS(qsub)
    Barrier("", (qs,))
    Y(qs[0])
    Y(qs[2])

@qgl2decl
def anotherMulti3():
    qs = QRegister(3)
    # create the QRegister with slicing
    qsub = QRegister(qs[0:2])
    Id(qsub)
    X(qsub)
    Barrier("", (qs,))
    MEAS(qsub)
    Barrier("", (qs,))
    Y(qs[0])
    Y(qs[2])
