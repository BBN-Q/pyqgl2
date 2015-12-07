from itertools import product

from qgl2.qgl2 import concur, qgl2decl, qgl2main
from qgl2.qgl2 import classical, pulse, qbit, qbit_list
from qgl2.qgl2 import Qbit

from QGL import *

def init(*args):
    pass

@qgl2decl
def tomo(f, q1:qbit, q2:qbit):
    fncs = [X90,Y90,X,Y]
    preps = product(fncs, fncs)
    measurements = preps

    for prep in preps:
        for meas in measurements:
            init(q1, q2)
            with concur():
                for p, q in zip(prep, (q1,q2)):
                    p(q)
            f(q1, q2)
            with concur():
                for m, q in zip(meas, (q1, q2)):
                    m(q)
                    MEAS(q)

@qgl2decl
def process(control:qbit, target:qbit):
    X90(control) * X90(target)
    CR(control, target)
    X(control)
    CR(control, target)
    X(control)

@qgl2main
def main():
    q1 = Qbit(1)
    q2 = Qbit(2)
    tomo(process, q1, q2)
