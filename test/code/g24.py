# Copyright 2019 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qgl2main, qreg
from qgl2.qgl2 import QRegister
from qgl2.qgl2 import QValue
from qgl2.qgl1 import X, Y, Z, Id, Utheta, MEAS, MEASA, Invalidate
from qgl2.util import QMeas
from itertools import product

@qgl2decl
def xQMeas(q: qreg, qval=None):

    maddr = 0
    if qval is not None:
        maddr = qval.addr

    bitpos = 0
    mask = 0
    for qbit in q:
        mask += (1 << bitpos)
        bitpos += 1

    if mask:
        Invalidate(maddr, mask)

        bitpos = 0
        for qbit in q:
            MEASA(qbit, maddr=(maddr, bitpos))
            bitpos += 1

@qgl2main
def t0():
    """
    Correct result is something like

    [ MEASA(q1, maddr=0), MEASA(q2, maddr=0) ]
    """

    q1 = QRegister('q1', 'q2')
    qv = QValue(size=2)
    QMeas(q1, qv)

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

@qgl2main
def t6():
    """
    Minimal example of a runtime conditional
    """

    q1 = QRegister('q1')
    v = QValue(size=1)

    QMeas(q1, qval=v)
    if QConditional(v):
        X(q1)
    else:
        X90(q1)


