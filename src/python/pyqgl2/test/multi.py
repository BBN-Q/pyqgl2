from qgl2.qgl1 import QubitFactory, Id, X, MEAS, Y
from qgl2.qgl2 import qgl2decl, sequence, concur, seq
from qgl2.qgl2 import init

@qgl2decl
def multiQbitTest() -> sequence:
    q1 = QubitFactory('q1')
    q2 = QubitFactory('q2')

    with concur:
        with seq:
            init(q1)
            Id(q1)
            X(q1)
        with seq:
            init(q2)
            X(q2)
            Id(q2)

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
            init(q)
            Id(q)
            X(q)
            MEAS(q)
    with concur:
        for q in [q1, q3]:
            Y(q)
