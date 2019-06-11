from qgl2.qgl2 import concur, qreg, qgl2decl, pulse, qgl2main
from qgl2.qgl1 import QubitFactory, X90, Y90

@qgl2decl
def func_a(a: qreg, b: qreg, c: qreg):

    with concur:
        for q in [a, b, c]:
            func_b(q)

@qgl2decl
def func_b(a: qreg) -> pulse:
    X90(a)
    Y90(a)

@qgl2main
def main():

    x = QubitFactory("1")
    y = QubitFactory("2")
    z = QubitFactory("3")

    func_a(x, y, z)

