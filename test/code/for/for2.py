
from qgl2.qgl2 import concur, qreg, qgl2decl, qgl2main
from qgl2.qgl1 import QubitFactory, Id, X90, Y90

@qgl2decl
def func_a(a: qreg, b: qreg, c: qreg):

    with concur:
        for q in [a, b, c]:
            func_b(q)

@qgl2decl
def func_b(a: qreg):
    for x in [1, 2, 3]:
        func_c(a, x)
    for func in [func_c, func_d]:
        func(a, 1)

@qgl2decl
def func_c(a: qreg, x: classical):
    Id(a) + X90(a, kwarg1=x)

@qgl2decl
def func_d(a: qreg, x: classical):
    Id(a) + Y90(a, kwarg1=x)

@qgl2main
def main():

    x = QubitFactory("1")
    y = QubitFactory("2")
    z = QubitFactory("3")

    func_a(x, y, z)

