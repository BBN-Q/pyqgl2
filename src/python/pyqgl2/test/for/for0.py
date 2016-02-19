
from qgl2.qgl2 import concur, qbit, qgl2decl, Qbit
from qgl2.qgl2 import Qbit

@qgl2decl
def func_a(a: qbit, b: qbit, c: qbit):

    with concur:
        for q in [a, b, c]:
            func_b(q)

@qgl2decl
def func_b(a: qbit):
    X90(a) + Y90(a)

@qgl2main
def main():

    x = Qbit(1)
    y = Qbit(2)
    z = Qbit(3)

    func_a(x, y, z)

