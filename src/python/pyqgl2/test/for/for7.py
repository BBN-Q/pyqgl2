
from qgl2.qgl2 import concur, qbit, qgl2decl, Qbit
from qgl2.qgl2 import Qbit

@qgl2decl
def MEAS(q: qbit) -> pulse:
    # measure q, and as a side effect put the result in
    # a magic context-local variable named vmeas.
    #
    # This is rubbish; just for development purposes, because
    # assignment statements like "vmeas = MEAS(q)" trigger
    # a bug in the substition code
    measurement(q)

@qgl2decl
def settle(q: qbit) -> pulse:

    init(q)
    while True:
        MEAS(q)
        if vmeas:
            break
        Id(q)

@qgl2decl
def setup(a: qbit, b: qbit, c: qbit):

    with concur:
        for qbit in [a, b, c]:
            settle(qbit)

@qgl2main
def main():

    x = Qbit(1)
    y = Qbit(2)
    z = Qbit(3)

    setup(x, y, z)

