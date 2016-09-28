
from qgl2.qgl2 import concur, qbit, qgl2decl, Qbit
from qgl2.qgl2 import Qbit

@qgl2decl
def MEAS(q: qbit):
    CHANMEAS(q)

@qgl2decl
def setup(a: qbit, b: qbit, c: qbit):

    with concur:
        for q in [a, b, c]:
            for i in range(10):
                if MEAS(q):
                    break
                X90(q)

@qgl2main
def main():

    x = Qbit(1)
    y = Qbit(2)
    z = Qbit(3)

    setup(x, y, z)

