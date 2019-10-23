
from qgl2.qgl2 import concur, qreg, qgl2decl, qgl2main
from qgl2.qgl1 import QubitFactory, Id
from qgl2.util import init

@qgl2decl
def MEAS(q: qreg) -> pulse:
    # measure q, and as a side effect put the result in
    # a magic context-local variable named vmeas.
    #
    # This is rubbish; just for development purposes, because
    # assignment statements like "vmeas = MEAS(q)" trigger
    # a bug in the substition code
    measurement(q)

@qgl2decl
def settle(q: qreg) -> pulse:

    init(q)
    while True:
        MEAS(q)
        if vmeas:
            break
        Id(q)

@qgl2decl
def setup(a: qreg, b: qreg, c: qreg):

    with concur:
        for qbit in [a, b, c]:
            settle(qbit)

@qgl2main
def main():

    x = QubitFactory("1")
    y = QubitFactory("2")
    z = QubitFactory("3")

    setup(x, y, z)

