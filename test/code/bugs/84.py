
from qgl2.qgl2 import qgl2decl, qgl2main, qreg
from qgl2.qgl2 import QRegister
from qgl2.qgl1 import X, Y, Z, Id, Utheta
from itertools import product

@qgl2decl
def cond_helper(q: qreg, cond):
    if cond:
        X(q)

@qgl2decl
def t1():
    """
    Correct result is [ X(q1) ]
    """

    q1 = QRegister('q1')

    cond_helper(q1, False)

    X(q1)

@qgl2decl
def t2():
    """
    Correct result is [ X(q1) ]
    """

    q1 = QRegister('q1')
    q2 = QRegister('q2')

    # We're not going to reference q2 anywhere,
    # just to make sure that the compiler doesn't
    # freak out
    X(q1)

@qgl2decl
def t3():
    """
    Like t2, but with a function call
    """

    q1 = QRegister('q1')
    q2 = QRegister('q2')

    cond_helper(q1, True)

@qgl2decl
def t4():
    """
    Like t3, but the function call does nothing
    """

    q1 = QRegister('q1')
    q2 = QRegister('q2')

    cond_helper(q1, False)

    X(q1) # need to do something

@qgl2decl
def t5():
    """
    Like t3, but the function call does nothing
    """

    q1 = QRegister('q1')
    q2 = QRegister('q2')

    # don't do anything at all
