# Run t0.py

from qgl2.qgl2 import concur, seq
from qgl2.qgl2 import qgl2decl, qgl2main
from qgl2.qgl2 import classical, pulse, qbit, qbit_list
from qgl2.qgl1 import Qubit, X, X90, Y, Y90

from t2 import second_level
from t0 import fred as fred

@qgl2decl
def t1(bit1: qbit, bit2: qbit):
    second_level(bit1, bit2)
    fred(bit1, bit2)

@qgl2decl
def third_level(a: qbit, b: qbit):
    with concur:
        X90(a)
        Y90(b)
