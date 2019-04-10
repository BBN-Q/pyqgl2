# Copyright 2019 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qgl2main, qreg
from qgl2.qgl2 import QRegister
from qgl2.qgl2 import QValue
from qgl2.qgl1 import X, Y, Z, Id, Utheta, MEAS, MEASA
from qgl2.util import QMeas
from itertools import product

@qgl2main
def t1():
    """
    Correct result is something like

    [ MEASA(q1, maddr=0) ]
    """

    q1 = QRegister('q1')

    QMeas(q1)

@qgl2main
def t2():
    """
    Correct result is something like

    [ MEASA(q1, maddr=16) ]
    """

    q1 = QRegister('q1')

    v = QValue(size=2 * 4, name='test')

    QMeas(q1, qval=v)

@qgl2main
def t3():
    """
    Correct result is something like

    [ MEASA(q1, maddr=16) ]
    """

    q1 = QRegister('q1')

    v = QValue(size=2 * 4, name='test')

    MEASA(q1, maddr=v.addr)

@qgl2main
def t4():
    """
    Correct result is something like

    [ MEASA(q1, maddr=16) ]
    """

    q1 = QRegister('q1')

    v = QValue(size=2 * 4, name='test-alt')

    MEASA(q1, maddr=v.addr)

@qgl2main
def t5():
    """
    Correct result is something like

    [ MEASA(q1, maddr=19) ]
    """

    q1 = QRegister('q1')

    v = QValue(size=4, name='a')
    v = QValue(size=4, name='b')
    v = QValue(size=4, name='c')
    v = QValue(size=4, name='d')

    QMeas(q1, qval=v)

