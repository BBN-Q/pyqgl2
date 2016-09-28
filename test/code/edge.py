# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# Tests for end to end Edge handling, and handling stubs on >1 qubits

from qgl2.qgl1 import QubitFactory, Id, X, MEAS, Y, echoCR, CNOT_CR
from qgl2.qgl2 import qgl2decl, sequence, concur, seq, qbit, qgl2stub
from qgl2.util import init

@qgl2decl
def edgeTest() -> sequence:
    q1 = QubitFactory('q1')
    q2 = QubitFactory('q2')
    with concur:
        for q in [q1, q2]:
            init(q)
    with concur:
        for q in [q1, q2]:
            X(q)
    echoCR(q1, q2)

# Simplest possible test
@qgl2decl
def edgeTest2() -> sequence:
    q1 = QubitFactory('q1')
    q2 = QubitFactory('q2')
    echoCR(q1, q2)

@qgl2decl
def edgeTest3() -> sequence:
    q1 = QubitFactory('q1')
    q2 = QubitFactory('q2')
    with concur:
        for q in [q1, q2]:
            init(q)
    echoCR(q1, q2)
    X(q2)
    Y(q2)
    Id(q2)
    X(q2)

# Note you need a 2nd edge from q2 to q1 for edgeTest4,
# which may not be realistic
@qgl2decl
def edgeTest4() -> sequence:
    q1 = QubitFactory('q1')
    q2 = QubitFactory('q2')

    with concur:
        for q in [q1, q2]:
            init(q)
    echoCR(q1, q2)
    echoCR(q2, q1)
    echoCR(q1, q2)
    X(q1)
    Y(q1)
    Id(q1)
    X(q1)

# edgeTest5 involves a stub that
# is bad: creating and using another / different qubit
# Here we have a stub whose implementation is in this same file
@qgl2stub('test.code.edge', 'MyPulseReal')
def MyPulse(source: qbit) -> qbit:
    pass

# QGL1 function
def MyPulseReal(source):
    from QGL.PulsePrimitives import X
    from QGL.ChannelLibrary import QubitFactory
    q3 = QubitFactory('q3')
    return X(q3)

@qgl2decl
def edgeTest5() -> sequence:
    q1 = QubitFactory('q1')
    q2 = QubitFactory('q2')
    with concur:
        for q in [q1, q2]:
            init(q)
            MyPulse(q)

@qgl2decl
def cnotcrTest() -> sequence:
    q1 = QubitFactory('q1')
    q2 = QubitFactory('q2')
    with concur:
        for q in [q1, q2]:
            init(q)
    CNOT_CR(q1, q2)
