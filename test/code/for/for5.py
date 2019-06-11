
from qgl2.qgl2 import concur, qreg, qgl2decl
from qgl2.qgl2 import Qbit

@qgl2decl
def func_a(a: qreg, b: qreg, c: qreg):

    with concur:
        for q in [a, b, c]:
            for x in [1, 2]:
                init(q)
                for f in [X90, Y]:
                    f(q, x)

@qgl2decl
def func_c(a: qreg, x: classical):
    Id(a) + X90(a, x)

@qgl2decl
def func_d(a: qreg, x: classical):
    Id(a) + Y90(a, x)

@qgl2main
def main():

    x = Qbit(1)
    y = Qbit(2)
    z = Qbit(3)

    func_a(x, y, z)

