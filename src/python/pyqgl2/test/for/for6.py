
from qgl2.qgl2 import concur, qbit, qgl2decl, qgl2main
from qgl2.qgl1 import Qubit, Id, Y90, Y, X90
from qgl2.basic_sequences.qgl2_plumbing import init

@qgl2decl
def func_a(a: qbit, b: qbit, c: qbit):

    with concur:
        for q in [a, b, c]:
            init(q)
            for x in [1, 2]:
                for f in [func_c, func_d]:
                    f(a, x)

@qgl2decl
def func_c(a: qbit, x: classical):
    for n in range(2):
        mark(a, n)
        for op in [Id, X90]:
            op(a)
        Y(a, kwarg1=x)

@qgl2decl
def func_d(a: qbit, x: classical):
    for n in range(2):
        func_e(a, x, n)

@qgl2decl
def func_e(a: qbit, x: classical, n: classical):
    for m in range(100, 102):
        mark2(a, n, m)
        Id(a) + Y90(a, kwarg1=x)

@qgl2main
def main():

    x = Qubit("1")
    y = Qubit("2")
    z = Qubit("3")

    func_a(x, y, z)

