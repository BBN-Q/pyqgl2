from qgl2.qgl2 import qgl2decl, qgl2main, qreg, QRegister
from qgl2.qgl1 import Id, X90, Y90, X, Y, Ztheta, MEAS, CNOT

from math import pi

@qgl2decl
def hadamard(q:qreg):
    Y90(q)
    X(q)

@qgl2decl
def CZ_k(c:qreg, t:qreg, k):
    theta = 2 * pi / 2**k
    Ztheta(t, angle=theta/2)
    CNOT(c, t)
    Ztheta(t, angle=-theta/2)
    CNOT(c, t)

@qgl2decl
def qft(qs:qreg):
    for i in range(len(qs)):
        hadamard(qs[i])
        for j in range(i+1, len(qs)):
            CZ_k(qs[i], qs[j], j-i)
    MEAS(qs)
