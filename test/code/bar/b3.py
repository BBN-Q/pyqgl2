from qgl2.qgl2 import concur, qbit, qgl2decl
from qgl2.qgl2 import sequence, pulse, qgl2main, classical

from qgl2.qgl1 import QubitFactory, X90, Y90, X, MEAS, Utheta, Xtheta
from qgl2.qgl1 import Call, BlockLabel, Goto, LoadRepeat, Repeat, Return
from qgl2.qgl1 import CmpEq

from qgl2.util import init

@qgl2decl
def sequential(a: qbit, b: qbit):
    X90(a)
    Y90(b)

@qgl2main
def main():

    q1 = QubitFactory('q1')
    q2 = QubitFactory('q2')
    q3 = QubitFactory('q3')

    with concur:
        sequential(q1, q2)
        sequential(q2, q3)


