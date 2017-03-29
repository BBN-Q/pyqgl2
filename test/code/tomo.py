from itertools import product

from qgl2.qgl2 import concur, qgl2decl, qgl2main
from qgl2.qgl2 import classical, pulse, qbit, qbit_list
from qgl2.qgl1 import QubitFactory, Id, X90, Y90, X, Y, MEAS, Wait, CNOT

# Don't do this import here - it replaces our stubs above
#from QGL import *

# Note this different / non-standard definition of init
# Elsewhere init takes a single qubit
def init(*args):
    pass

@qgl2decl
def tomo(f, q1:qbit, q2:qbit):
    fncs = [Id, X90, Y90, X]
    for prep in product(fncs, fncs):
        for meas in product(fncs, fncs):
            init(q1, q2)
            for p, q in zip(prep, (q1,q2)):
                p(q)
            f(q1, q2)
            for m, q in zip(meas, (q1, q2)):
                m(q)
            for q in (q1, q2):
                MEAS(q)

@qgl2decl
def tomo_no_generators(f, q1:qbit, q2:qbit):
    fncs = [Id, X90, Y90, X]
    # QGL2 couldn't handle generators and needed to listify them
    # (no longer true)
    for prep in list(product(fncs, fncs)):
        for meas in list(product(fncs, fncs)):
            for p, q in list(zip(prep, (q1,q2))):
                p(q)
            f(q1, q2)
            for m, q in list(zip(meas, (q1, q2))):
                m(q)
            for q in (q1, q2):
                MEAS(q)

@qgl2decl
def statetomo(f, q1:qbit, q2:qbit):
    fncs = [Id, X90, Y90, X]
    for meas in product(fncs, fncs):
        init(q1, q2)
        f(q1, q2)
        for m, q in zip(meas, (q1, q2)):
            m(q)
        for q in (q1, q2):
            MEAS(q)

@qgl2decl
def process(control:qbit, target:qbit):
    X90(control)
    Y90(target)

@qgl2decl
def main():
    q1 = QubitFactory("q1")
    q2 = QubitFactory("q2")
    tomo(process, q1, q2)

@qgl2decl
def main_no_generators():
    q1 = QubitFactory("q1")
    q2 = QubitFactory("q2")
    tomo_no_generators(process, q1, q2)

@qgl2decl
def main_statetomo():
    q1 = QubitFactory("q1")
    q2 = QubitFactory("q2")
    statetomo(process, q1, q2)
