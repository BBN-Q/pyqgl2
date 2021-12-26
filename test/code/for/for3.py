
from qgl2.qgl2 import concur, qreg, qgl2decl
from qgl2.qgl2 import Qbit

@qgl2decl
def func_a1(a: qreg, b: qreg, c: qreg):
    with concur:
        for q in [a, b, c]:
            X90(a)
            func_b(q)

@qgl2decl
def func_a2(a: qreg, b: qreg, c: qreg):
    for q in [a, b, c]:
        X90(a)
        func_b(q)

@qgl2decl
def func_b(a: qreg):
    for x in [1, 2, 3]:
        X180(a, x)
    for x in [4, 5, 6]:
        Y90(a, x)

@qgl2main
def main():

    x = Qbit(1)
    y = Qbit(2)
    z = Qbit(3)

    func_a1(x, y, z)
    func_a2(x, y, z)

