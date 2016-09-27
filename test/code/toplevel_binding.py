from qgl2.qgl2 import concur, qgl2decl, qgl2main
from qgl2.qgl2 import classical, pulse, qbit, qbit_list
from qgl2.qgl1 import QubitFactory, Id, X90, Y90, X, Y, MEAS, Xtheta, Utheta

@qgl2decl
def main1(amps):
    q = QubitFactory('q1')
    for a in amps:
        Xtheta(q, amp=a)

@qgl2decl
def main2(amps, phase):
    q = QubitFactory('q1')
    for a in amps:
        Utheta(q, amp=a, phase=phase)

@qgl2decl
def main3(q:qbit, amps):
    for a in amps:
        Xtheta(q, amp=a)

@qgl2decl
def main4(q:qbit, amps, shape):
    for a in amps:
        Xtheta(q, amp=a, shapeFun=shape)
