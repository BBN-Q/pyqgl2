
from qgl2.qgl2 import concur, seq
from qgl2.qgl2 import qgl2decl, qgl2main
from qgl2.qgl2 import classical, pulse, qbit, qbit_list
from qgl2.qgl2 import Qbit

def X(qbit_param: qbit) -> pulse: pass
def X90(qbit_param: qbit) -> pulse: pass
def Y(qbit_param: qbit) -> pulse: pass
def Y90(qbit_param: qbit) -> pulse: pass

@qgl2decl
def t3(x: qbit, y: qbit):
    t2(y, x)

@qgl2decl
def t2(x: qbit, y: qbit):
    t1(x, y)

@qgl2decl
def t1(q_a: qbit, q_b: qbit):
    with concur:
        X(q_a) + X90(q_a) + Y90(q_a)
        Y(q_b) + Y90(q_b) + X90(q_b)

@qgl2decl
def yy(a: qbit):
    return 4

@qgl2decl
def zz(a):
    for b in [1, 2, 3]:
        print(b)

@qgl2main
def main():

    with concur as xxx:
        for nn in [1, 2]:
            zz(12)
            qbit1 = Qbit(1)
            qbit2 = Qbit(2)
            x = yy(qbit1)

            t3(qbit1, qbit2)
            t3(qbit2, qbit1)
