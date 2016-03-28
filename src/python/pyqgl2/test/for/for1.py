
from qgl2.qgl2 import concur, qbit, qgl2decl, qgl2main
from qgl2.qgl1 import Qubit, X90, Y90

@qgl2decl
def func_a(a: qbit, b: qbit, c: qbit):

    with concur:
        for q in [a, b, c]:
            func_b(q)

@qgl2decl
def func_b(a: qbit):
    for x in [1, 2, 3]:
        func_c(a, x)

@qgl2decl
def func_c(a: qbit, x: classical):
    X90(a, kwarg1=x) + Y90(a, kwarg1=x)

@qgl2main
def main():

    x = Qubit("1")
    y = Qubit("2")
    z = Qubit("3")

    func_a(x, y, z)

