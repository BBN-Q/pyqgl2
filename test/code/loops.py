from qgl2.qgl2 import qgl2decl, qgl2main, qreg
from qgl2.qgl2 import QRegister
from qgl2.qgl1 import Id, X90, Y90, X, Y, MEAS

@qgl2decl
def classical_continue():
    q1 = QRegister("q1")

    for ct in range(3):
        X(q1)
        if ct >= 1:
            X90(q1)
            continue
            X90(q1)
        Y90(q1)

@qgl2decl
def classical_break():
    q1 = QRegister("q1")

    for ct in range(3):
        X(q1)
        if ct >= 1:
            X90(q1)
            break
            X90(q1)
        Y90(q1)

@qgl2decl
def runtime_continue():
    q1 = QRegister("q1")

    for ct in range(3):
        m = MEAS(q1)
        if m:
            X90(q1)
            # this should produce an error
            continue
        Y90(q1)

@qgl2decl
def runtime_break():
    q1 = QRegister("q1")

    for ct in range(3):
        m = MEAS(q1)
        if m:
            X90(q1)
            # this should produce an error
            break
