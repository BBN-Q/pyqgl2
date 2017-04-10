
from qgl2.qgl2 import qgl2decl, qgl2main, qbit, qbit_list
from qgl2.qgl2 import QRegister
from qgl2.qgl1 import X, Y, Z, Id, Utheta
from itertools import product

import numpy as np

@qgl2decl
def t1():
    """
    Not intended to be a valid or useful sequence;
    only meant to test assignment and control flow
    """

    q1 = QRegister('q1')

    a = 1
    if True:
        a = 2

    # We should do an X, because the change to a should stick.
    if a == 2:
        X(q1)
    elif a == 1:
        # oops!
        Y(q1)
    else:
        # double oops!
        Z(q1)

@qgl2decl
def t2():

    q1 = QRegister('q1')

    a = 1
    if False:
        a = 2
    else:
        a = 3

    # We should do an X, because the change to a should stick.
    if a == 3:
        X(q1)
    elif a == 1:
        Y(q1)
    elif a == 2:
        Z(q1)
    else:
        Id(q1)

    print('T2 a = %d' % a)

@qgl2decl
def t3():
    """
    Correct result is X(q1)
    """

    q1 = QRegister('q1')

    a = 1

    for i in range(5):
        a += 1

    if a == 6:
        X(q1)
    else:
        Y(q1)

    print('T3 a = %d' % a)

@qgl2decl
def t4():
    """
    Correct result is [ X(q1), X(q1), X(q1), Y(q1), Y(q1) ]
    """

    q1 = QRegister('q1')

    # No p_list: use a_list
    t4_helper(q1, X, [1, 2, 3])

    # p_list supplied: use it
    t4_helper(q1, Y, [1], [1, 2])

@qgl2decl
def t4_helper(q: qbit, op, a_list, p_list=None):

    if p_list is None:
        p_list = a_list

    for p in p_list:
        op(q)
