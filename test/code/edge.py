# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# Tests for end to end Edge handling, and handling stubs on >1 qubits

from qgl2.qgl1 import Id, X, MEAS, Y, echoCR, CNOT
from qgl2.qgl2 import qgl2decl, qreg, QRegister
from qgl2.util import init

@qgl2decl
def edgeTest():
    qs = QRegister('q1', 'q2')
    init(qs)
    X(qs)
    echoCR(qs[0], qs[1])

@qgl2decl
def edgeTest3():
    q1 = QRegister('q1')
    q2 = QRegister('q2')
    init(q1, q2)
    echoCR(q1, q2)
    X(q2)
    Y(q2)
    Id(q2)
    X(q2)

# Note you need a 2nd edge from q2 to q1 for edgeTest4,
# which may not be realistic
@qgl2decl
def edgeTest4():
    q1 = QRegister('q1')
    q2 = QRegister('q2')

    for q in [q1, q2]:
        init(q)
    echoCR(q1, q2)
    echoCR(q2, q1)
    echoCR(q1, q2)
    X(q1)
    Y(q1)
    Id(q1)
    X(q1)

@qgl2decl
def cnotcrTest():
    qr = QRegister('q1', 'q2')
    init(qr)
    CNOT(qr[0], qr[1])
