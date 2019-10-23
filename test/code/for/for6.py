
from qgl2.qgl2 import concur, qreg, qgl2decl, qgl2main
from qgl2.qgl1 import QubitFactory, Id, Y90, Y, X90
from qgl2.util import init

@qgl2decl
def func_a(a: qreg, b: qreg, c: qreg):

    with concur:
        for q in [a, b, c]:
            init(q)
            for x in [1, 2]:
                for f in [func_c, func_d]:
                    f(a, x)

@qgl2decl
def func_c(a: qreg, x: classical):
    for n in range(2):
        mark(a, n)
        for op in [Id, X90]:
            op(a)
        Y(a, kwarg1=x)

@qgl2decl
def func_d(a: qreg, x: classical):
    for n in range(2):
        func_e(a, x, n)

@qgl2decl
def func_e(a: qreg, x: classical, n: classical):
    for m in range(100, 102):
        mark2(a, n, m)
        Id(a) + Y90(a, kwarg1=x)

@qgl2main
def main():

    x = QubitFactory("1")
    y = QubitFactory("2")
    z = QubitFactory("3")

    func_a(x, y, z)

