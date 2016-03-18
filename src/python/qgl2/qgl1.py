# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# Stubs of QGL1 functions with annotations so the QGL2 compiler knows how to handle these functions

# The annotations are defined in here
from .qgl2 import qbit, pulse, qgl2stub, sequence, qbit_list, control

# Start with functions that are used by the BasicSequences
#from QGL.PulsePrimitives import Id, X, Y, X90, Y90, MEAS, flat_top_gaussian, echoCR, U90, X90m, AC, Utheta, U
#from QGL.Compiler import compile_to_hardware
#from QGL.Channels import Qubit, LogicalMarkerChannel, Edge
#from QGL.ControlFlow import qwait, qif, Wait
#from QGL.ChannelLibrary import EdgeFactory
#from QGL.Cliffords import clifford_seq, clifford_mat, inverse_clifford

#from QGL.PulsePrimitives import Id, X, Y, X90, Y90, MEAS, flat_top_gaussian, echoCR, U90, X90m, AC, Utheta, U

# Many uses of Id supply a delay. That's the length: an int or float
# FIXME: Do we need to include that explicitly?
@qgl2stub
def Id(channel: qbit, *args, **kwargs) -> pulse:
    print('Id')

# Some uses supply qubit, length, amp, phase, shapeFun in that order
# Others qbit, amp, phase only in that order
# FIXME: Do we need to include the other 2?
@qgl2stub
def Utheta(qubit: qbit, amp=0, phase=0, label='Utheta', **kwargs) -> pulse:
    print('Utheta')

@qgl2stub
def X(qubit: qbit, **kwargs) -> pulse:
    print('X')
@qgl2stub
def X90(qubit: qbit, **kwargs) -> pulse:
    print('X90')
@qgl2stub
def X90m(qubit: qbit, **kwargs) -> pulse:
    print('X90m')
@qgl2stub
def Y(qubit: qbit, **kwargs) -> pulse:
    print('Y')
@qgl2stub
def Y90(qubit: qbit, **kwargs) -> pulse:
    print('Y90')
@qgl2stub
def U90(qubi: qbit, phase=0, **kwargs) -> pulse:
    print('U90')
@qgl2stub
def AC(qubit: qbit, cliffNum) -> pulse:
    print('AC')
@qgl2stub
def flat_top_gaussian(chan: qbit, riseFall, length, amp, phase=0) -> pulse:
    print('flat_top_gaussian')
@qgl2stub
def echoCR(controlQ: qbit, targetQ: qbit, amp=1, phase=0, length=200e-9, riseFall=20e-9, lastPi=True) -> sequence:
    print('echoCR')

# FIXME: QGL2 can't handle *args
# Calls include: qubit, 2 qubits, qbit list. But so far
# our qgl2 uses are just with a single qbit
#def MEAS(*args: qbit_list, **kwargs) -> pulse:
@qgl2stub
def MEAS(q: qbit, *args, **kwargs) -> pulse:
    print('MEAS')
# Our uses of U never supply any extra kwargs
@qgl2stub
def U(qubit: qbit, phase=0, **kwargs) -> pulse:
    print('U')

#from QGL.Compiler import compile_to_hardware
@qgl2stub
def compile_to_hardware(seqs: sequence, fileName, suffix=''):
    print('compile_to_hardware')

#from QGL.Channels import Qubit, Edge, LogicalMarkerChannel
# Edge used in test mains
# Note that this is really a class
#def Edge(**kwargs) -> qbit:
@qgl2stub
def Edge(label, source: qbit, target: qbit, gateChan, **kwargs) -> qbit:
    # FIXME: Can take source and target which are qbits
    # FIXME: Is qbit the right return type?
    print('Edge')
# Note that this is really a class
#def Qubit(**kwargs) -> qbit:
@qgl2stub
def Qubit(label, gateChan=None, **kwargs) -> qbit:
    print('Qubit')
# This is used just in testing mains
# Note that this is really a class
#def LogicalMarkerChannel(**kwargs) -> qbit:
@qgl2stub
def LogicalMarkerChannel(label, **kwargs) -> qbit:
    print('LogicalMarkerChannel')

#from QGL.ControlFlow import qwait, qif, Wait
@qgl2stub
def qif(mask, ifSeq: sequence, elseSeq: sequence = None) -> control:
    print('qif')
@qgl2stub
def qwait(kind="TRIG") -> control:
    pring('qwait')
# Note that this is really a class
@qgl2stub
def Wait() -> control:
    print('Wait')

#from QGL.ChannelLibrary import EdgeFactory
@qgl2stub
def EdgeFactory(source: qbit, target: qbit) -> qbit:
    # Is that the right return?
    print('EdgeFactory')

#from QGL.Cliffords import clifford_seq, clifford_mat, inverse_clifford
@qgl2stub
def inverse_clifford(cMat):
    # It's all classical I think?
    print('inverse_clifford')
@qgl2stub
def clifford_mat(c, numQubits) -> pulse:
    # Is that the right return type?
    print('clifford_mat')
@qgl2stub
def clifford_seq(c, q1: qbit, q2: qbit = None) -> sequence:
    # Is that the right return type?
    print('clifford_seq')


# Functions used by qgl2 compiler from ControlFlow

@qgl2stub
def Goto(target) -> control:
    # Note target is a BlockLabel
    pass
@qgl2stub
def LoadRepeat(value) -> control:
    # Value is an int
    pass
@qgl2stub
def Call(target) -> control:
    # target is a BlockLabel
    pass
@qgl2stub
def Return() -> control:
    pass
@qgl2stub
def Repeat(target) -> control:
    # target is a BlockLabel
    pass
@qgl2stub
def BlockLabel(label):
    # label is a string, output is a BlockLabel
    pass
