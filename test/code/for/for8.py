
from qgl2.qgl2 import concur, qreg, qgl2decl
from qgl2.qgl2 import Qbit


@qgl2decl
def setup(a: qreg, b: qreg, c: qreg):

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

