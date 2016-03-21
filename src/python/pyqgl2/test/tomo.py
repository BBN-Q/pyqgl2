from itertools import product

from qgl2.qgl2 import concur, qgl2decl, qgl2main
from qgl2.qgl2 import classical, pulse, qbit, qbit_list
from qgl2.qgl1 import Qubit, X90, Y90, X, Y, MEAS

# Don't do this import here - it replaces our stubs above
#from QGL import *

# Note this different / non-standard definition of init
# Elsewhere init takes a single qubit
def init(*args):
    pass

@qgl2decl
def tomo(f, q1:qbit, q2:qbit):
    # QGL2 can't yet handle a variable that is a list of functions
    fncs = [X90,Y90,X,Y]
    # QGL2 can't yet handle this call to product() to produce the list of functions to call
    preps = product(fncs, fncs)
    measurements = preps

    for prep in preps:
        for meas in measurements:
            init(q1, q2)
            with concur:
                for p, q in zip(prep, (q1,q2)):
                    p(q)
            f(q1, q2)
            with concur:
                for m, q in zip(meas, (q1, q2)):
                    m(q)
                    MEAS(q)

@qgl2decl
def process(control:qbit, target:qbit):
    X90(control) * X90(target)
    # What is CR?
    # Perhaps something like this:
    # Edge(label="cr", source = q1, target = q2, gateChan = crgate )
    # Or see CR.py: EchoCRLen and EchoCRPhase ?
    CR(control, target)
    X(control)
    CR(control, target)
    X(control)

@qgl2main
def main():
    q1 = Qubit("1")
    q2 = Qubit("2")
    tomo(process, q1, q2)
