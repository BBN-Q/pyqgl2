
from qgl2.qgl2 import qgl2decl, qgl2main, qbit, classical, pulse, qbit_list
from qgl2.qgl1 import X, Y, Z, Id, Utheta, QubitFactory
from itertools import product

@qgl2decl
def t1():
    """
    Correct result is [ X(q1), X(q1), X(q1) ]
    """

    q1 = QubitFactory(label='q1')

    (x, y, z) = (1, 2, 3)
    if (x, y, z) == (1, 2, 3):
        X(q1)
    else:
        print('oops 1')
        Y(q1)

    (x, y, z) = (y, z, x)
    if (x, y, z) == (2, 3, 1):
        X(q1)
    else:
        print('oops 2')
        Y(q1)

    (x, y, z) = (y, z, x)
    if (x, y, z) == (3, 1, 2):
        X(q1)
    else:
        print('oops 3')
        Y(q1)

@qgl2decl
def t2():
    """
    Correct result is [ X(q1), X(q1), X(q1) ]
    """

    q1 = QubitFactory(label='q1')

    (x, y, z) = (1, 2, 3)

    if x < y:
        (x, y, z) = (y, z, x)

    print((x, y, z))

    if (x, y, z) == (2, 3, 1):
        X(q1)
    else:
        print('oops 1')
        Y(q1)

    if x < y:
        (x, y, z) = (y, z, x)

    print((x, y, z))

    if (x, y, z) == (3, 1, 2):
        X(q1)
    else:
        print('oops 2')
        Y(q1)

    if y < z:
        (x, y, z) = (y, z, x)

    print((x, y, z))

    if (x, y, z) == (1, 2, 3):
        X(q1)
    else:
        print('oops 3')
        Y(q1)

@qgl2decl
def t3():
    """
    Correct result is [ X(q1), X(q1), X(q1), X(q1) ]
    """

    q1 = QubitFactory(label='q1')

    a = [ 0, 1, 2, 3 ]

    a[0], a[1] = a[1], a[0]
    if a == [ 1, 0, 2, 3 ]:
        X(q1)
    else:
        print('oops 1')
        Y(q1)

    a[2], a[3] = a[3], a[2]
    if a == [ 1, 0, 3, 2 ]:
        X(q1)
    else:
        print('oops 2')
        Y(q1)

    a[0], a[2] = a[2], a[0]
    if a == [ 3, 0, 1, 2 ]:
        X(q1)
    else:
        print('oops 3')
        Y(q1)

    a[1], a[3] = a[3], a[1]
    if a == [ 3, 2, 1, 0 ]:
        X(q1)
    else:
        print('oops 4')
        Y(q1)


