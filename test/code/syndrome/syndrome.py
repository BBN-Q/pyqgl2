from qgl2.qgl2 import qgl2decl, qgl2main, qbit, QRegister
from qgl2.qgl1 import X, Y, Z, Y90, X90, CNOT

@qgl2decl
def syndrome_cycle(qbits, role_def):

    for q in qbits:
        if role_def[q].is_x():
            Hadamard(q)

    for direction in range(4):
        for q in qbits:
            role = role_def[q]
            neighbor = role.neighbors[direction]

            if neighbor:
                if role.is_x():
                    CNOT(q, neighbor)
                elif role.is_z():
                    CNOT(neighbor, q)

    for q in qbits:
        if role_def[q].is_x():
            Hadamard(q)

@qgl2decl
def Hadamard(q: qbit):
    Y90(q)
    X90(q)

class SyndromeRole(object):
    """
    Simple mockup of the role of a qbit in a syndrome calculation:
    represents whether it's a data, x, or z bit, and the list
    of neighbors in each direction (up, left, right, and down; if
    there is no neighbor in a given direction, use None).
    """

    def __init__(self, qbit_type, neighbors):

        # half-hearted error checking
        #
        # We don't check whether the neighbors are bogus
        #
        assert qbit_type in ['x', 'z', 'd'], \
                ('invalid qbit_type [%s]' % str(qbit_type))
        assert isinstance(neighbors, list)
        assert len(neighbors) == 4

        self.qbit_type = qbit_type
        self.neighbors = list(neighbors)

    def is_x(self):
        return self.qbit_type == 'x'

    def is_z(self):
        return self.qbit_type == 'z'


@qgl2main
def main():
    """
    The initial role of each qbit is:

    q0:d  q1:x  q2:d
    q3:z  q4:d  q5:z
    q6:d  q7:x  q8:d

    And the order of CNOTs is up-left-right-down
    """

    q0 = QRegister('q0')
    q1 = QRegister('q1')
    q2 = QRegister('q2')
    q3 = QRegister('q3')
    q4 = QRegister('q4')
    q5 = QRegister('q5')
    q6 = QRegister('q6')
    q7 = QRegister('q7')
    q8 = QRegister('q8')

    all_qbits = [q0, q1, q2, q3, q4, q5, q6, q7, q8]

    role_def = dict()
    role_def[q0] = SyndromeRole('d', [None, None, q1, q3])
    role_def[q1] = SyndromeRole('x', [None, q0, q2, q4])
    role_def[q2] = SyndromeRole('d', [None, q1, None, q5])
    role_def[q3] = SyndromeRole('z', [q0, None, q4, q6])
    role_def[q4] = SyndromeRole('d', [q1, q3, q5, q7])
    role_def[q5] = SyndromeRole('z', [q2, q4, None, q8])
    role_def[q6] = SyndromeRole('d', [q3, None, q7, None])
    role_def[q7] = SyndromeRole('x', [q4, q6, q8, None])
    role_def[q8] = SyndromeRole('d', [q5, q7, None, None])

    syndrome_cycle(all_qbits, role_def)
