from qgl2.qgl2 import qgl2decl, qgl2main, qbit, qbit_list
from qgl2.qgl2 import QRegister
from qgl2.qgl1 import X, Y, Z, Id, Utheta
from itertools import product

@qgl2decl
def t1():
    """
    Expected: [X(q1), X(q1)]
    """

    q1 = QRegister('q1')

    l1 = list()
    l1 += [ 0 ]
    l1 += [ 1 ]
    l1 += [ 2 ]

    if l1 == [0, 1, 2]:
        X(q1)
    else:
        Y(q1)

    if len(l1) == 3:
        X(q1)
    else:
        Y(q1)

@qgl2decl
def t2():
    """
    Expected: [X(q1), X(q1), X(q1), X(q1)]
    """

    q1 = QRegister('q1')

    l1 = [0, 1, 2, 3]

    l1 = l1[:2] + l1[2:]
    if l1 == [0, 1, 2, 3]:
        X(q1)
    else:
        Y(q1)

    l1 = l1[2:] + l1[:2]
    if l1 == [2, 3, 0, 1]:
        X(q1)
    else:
        Y(q1)

    l1 = l1[3:] + l1[:3]
    if l1 == [1, 2, 3, 0]:
        X(q1)
    else:
        Y(q1)

    l1 = l1[1:] + l1[:1]
    if l1 == [2, 3, 0, 1]:
        X(q1)
    else:
        Y(q1)

@qgl2decl
def t3():
    """
    Expected: [X(q1), X(q1), X(q1)]
    """

    q1 = QRegister('q1')

    total = 0
    if total == 0:
        X(q1)
    else:
        Y(q1)

    total += 2
    if total == 2:
        total += 2
        X(q1)
    else:
        total += 1
        Y(q1)

    if total == 4:
        X(q1)
    else:
        Y(q1)

@qgl2decl
def t4():
    """
    Expected: [X(q1), Y(q1), Y(q1), Z(q1), Z(q1), Z(q1), Z(q1)]

    TODO: currently fails; instance methods confuse the evaluator.
    """

    q1 = QRegister('q1')

    l1 = list()

    l1.append('a')
    for _ in l1:
        X(q1)

    l1.append('b')
    for _ in l1:
        Y(q1)

    l1.append('c')
    l1.append('d')
    for _ in l1:
        Z(q1)

@qgl2decl
def t5():
    """
    Expected: [X(q1), Y(q1), Y(q1), Z(q1), Z(q1), Z(q1), Z(q1)]

    Like t4, but uses operators that work properly right now.
    """

    q1 = QRegister('q1')

    l1 = list()

    l1 += ['a']
    for _ in l1:
        X(q1)

    l1 += ['b']
    for _ in l1:
        Y(q1)

    l1 += ['c', 'd']
    for _ in l1:
        Z(q1)
