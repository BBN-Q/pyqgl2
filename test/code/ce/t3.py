
from qgl2.qgl2 import concur, qreg, qgl2decl
from qgl2.qgl2 import sequence, pulse, qgl2main, classical

from qgl2.qgl1 import QubitFactory, X90, Y90, X, MEAS, Utheta, Xtheta
from qgl2.qgl1 import Call, BlockLabel, Goto, LoadRepeat, Repeat, Return
from qgl2.qgl1 import CmpEq

from qgl2.util import init

@qgl2main
def main():

    x0 = QubitFactory('q1')
    x1 = QubitFactory('q2')

    with concur:
        while not MEAS(x0):
            X(x0)

    with concur:
        while not MEAS(x1):
            X(x1)



