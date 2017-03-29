from qgl2.qgl2 import concur, qgl2decl, qgl2main
from qgl2.qgl2 import qbit, qbit_list
from qgl2.qgl1 import QubitFactory, Id, X90, Y90, X, Y, MEAS

# FIXME these are inserted by the flattener, the user shouldn't have to
# import them manually
from qgl2.qgl1 import LoadCmp, CmpEq, CmpNeq, CmpGt, CmpLt, Goto, BlockLabel

@qgl2decl
def classical_continue():
    q1 = QubitFactory("q1")

    for ct in range(3):
        X(q1)
        if ct >= 1:
            X90(q1)
            continue
            X90(q1)
        Y90(q1)

@qgl2decl
def classical_break():
    q1 = QubitFactory("q1")

    for ct in range(3):
        X(q1)
        if ct >= 1:
            X90(q1)
            break
            X90(q1)
        Y90(q1)

@qgl2decl
def runtime_continue():
    q1 = QubitFactory("q1")

    for ct in range(3):
        m = MEAS(q1)
        if m:
            X90(q1)
            # this should produce an error
            continue
        Y90(q1)

@qgl2decl
def runtime_break():
    q1 = QubitFactory("q1")

    for ct in range(3):
        m = MEAS(q1)
        if m:
            X90(q1)
            # this should produce an error
            break
