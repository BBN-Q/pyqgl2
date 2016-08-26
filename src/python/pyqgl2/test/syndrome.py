from qgl2.qgl2 import qgl2decl, qgl2main
from qgl2.qgl2 import qbit, classical
from qgl2.qgl2 import concur
from qgl2.qgl1 import QubitFactory
from qgl2.qgl1 import X, Y, Id
from qgl2.qgl2_check import QGL2check

class _SyndromeRole(object):

    def __init__(self, qbit_type, neighbors):
        self.x = False
        self.z = False

        if qbit_type == 'x':
            self.x = True
        elif qbit_type == 'z':
            self.z = True

        self.neighbors = list(neighbors)


def make_role(qbit_type, neighbors):
    return _SyndromeRole(qbit_type, neighbors)

@qgl2decl
def CNOT(q1: qbit, q2: qbit):
    with concur:
        X(q1)
        Y(q2)


@qgl2decl
def syndrome_cycle(qbits, role_def):

    for direction in range(4):
        with concur:
            for q in qbits:
                role = role_def[q]
                neighbor = role.neighbors[direction]

                if neighbor:
                    if role.x:
                        CNOT(q, neighbor)
                    elif role.z:
                        CNOT(neighbor, q)

@qgl2main
def main():
    """
    The initial role is:

    q0:d  q1:x  q2:d
    q3:z  q4:d  q5:z
    q6:d  q7:x  q8:d

    And the order of CNOTs is up-left-right-down

    This might be bogus, but it's just for an illustration
    """

    q0 = QubitFactory('0')
    q1 = QubitFactory('1')
    q2 = QubitFactory('2')
    q3 = QubitFactory('3')
    q4 = QubitFactory('4')
    q5 = QubitFactory('5')
    q6 = QubitFactory('6')
    q7 = QubitFactory('7')
    q8 = QubitFactory('8')

    all_qbits = [q0, q1, q2, q3, q4, q5, q6, q7, q8]

    role_def = dict()
    role_def[q0] = make_role('d', [None, None, q1, q3])
    role_def[q1] = make_role('x', [None, q0, q2, q4])
    role_def[q2] = make_role('d', [None, q1, None, q5])
    role_def[q3] = make_role('z', [q0, None, q4, q6])
    role_def[q4] = make_role('d', [q1, q3, q5, q7])
    role_def[q5] = make_role('z', [q2, q4, None, q8])
    role_def[q6] = make_role('d', [q3, None, q7, None])
    role_def[q7] = make_role('x', [q4, q6, q8, None])
    role_def[q8] = make_role('d', [q5, q7, None, None])

    syndrome_cycle(all_qbits, role_def)
