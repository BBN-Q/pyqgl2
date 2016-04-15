from qgl2.qgl2 import concur, qbit, qgl2decl, sequence, pulse, qgl2main
from qgl2.qgl1 import Qubit, X90, Y90

@qgl2decl
def func_a(a: qbit, b: qbit, c: qbit) -> sequence:

    with concur:
        for q in [a, b, c]:
            func_b(q)

@qgl2decl
def func_b(a: qbit) -> pulse:
    X90(a)
    Y90(a)

@qgl2main
def main():

    x = Qubit("1")
    y = Qubit("2")
    z = Qubit("3")

    func_a(x, y, z)

