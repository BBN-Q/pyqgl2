
from qgl2.qgl2 import concur, seq
from qgl2.qgl2 import qgl2decl, qgl2main
from qgl2.qgl2 import classical, pulse, qbit, qbit_list
from qgl2.qgl1 import QubitFactory, X, X90, Y, Y90

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

    with concur:
        qbit1 = QubitFactory("1")
        qbit2 = QubitFactory("2")
        for nn in [1, 2]:
            zz(12)
            # Putting Qubit creation here inside the for loop
            # is an error, cause it looks like Qubit re-assignment
#            qbit1 = QubitFactory("1")
#            qbit2 = QubitFactory("2")
            x = yy(qbit1)

            t3(qbit1, qbit2)
            t3(qbit2, qbit1)
