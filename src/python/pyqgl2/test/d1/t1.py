
from qgl2.qgl2 import concur, seq
from qgl2.qgl2 import qgl2decl, qgl2main
from qgl2.qgl2 import classical, pulse, qbit, qbit_list
from qgl2.qgl2 import Qbit

def X(qbit_param: qbit) -> pulse: pass
def X90(qbit_param: qbit) -> pulse: pass
def Y(qbit_param: qbit) -> pulse: pass
def Y90(qbit_param: qbit) -> pulse: pass
def Z(qbit_param: qbit) -> pulse: pass
def Z90(qbit_param: qbit) -> pulse: pass

from t2 import second_level
from t0 import fred as fred

@qgl2decl
def t1(bit1: qbit, bit2: qbit):
    second_level(bit1, bit2)
    fred(a, b)

@qgl2decl
def third_level(a: qbit, b: qbit):
    with concur:
        X90(a)
        Y90(b)
