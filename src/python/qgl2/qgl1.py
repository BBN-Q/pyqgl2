# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# Stubs of QGL1 functions with annotations so the QGL2 compiler knows
# how to handle these functions

# The annotations are defined in here
from qgl2.qgl2 import qreg, pulse, qgl2stub, qgl2meas, control, classical, sequence

# Many uses of Id supply a delay. That's the length: an int or float
# Must use the label 'length'
# FIXME: Do we need to include that explicitly?
@qgl2stub('QGL.PulsePrimitives')
def Id(channel: qreg, *args, **kwargs) -> pulse:
    print('Id')

# Some uses supply qubit, length, amp, phase, shapeFun in that order
# Others qreg, amp, phase only in that order
# FIXME: Do we need to include the other 2?
@qgl2stub('QGL.PulsePrimitives')
def Utheta(qubit: qreg, amp=0, phase=0, label='Utheta', **kwargs) -> pulse:
    print('Utheta')

@qgl2stub('QGL.PulsePrimitives')
def Xtheta(qubit: qreg, amp=0, label='Xtheta', **kwargs) -> pulse:
    print('Xtheta')

@qgl2stub('QGL.PulsePrimitives')
def Ytheta(qubit: qreg, amp=0, label='Ytheta', **kwargs) -> pulse:
    print('Ytheta')

@qgl2stub('QGL.PulsePrimitives')
def Ztheta(qubit: qreg, angle=0, label='Ztheta', **kwargs) -> pulse:
    print('Ztheta')

@qgl2stub('QGL.PulsePrimitives')
def X(qubit: qreg, **kwargs) -> pulse:
    print('X')

@qgl2stub('QGL.PulsePrimitives')
def Xm(qubit: qreg, **kwargs) -> pulse:
    print('Xm')

@qgl2stub('QGL.PulsePrimitives')
def Ym(qubit: qreg, **kwargs) -> pulse:
    print('Ym')

@qgl2stub('QGL.PulsePrimitives')
def X90(qubit: qreg, **kwargs) -> pulse:
    print('X90')

@qgl2stub('QGL.PulsePrimitives')
def X90m(qubit: qreg, **kwargs) -> pulse:
    print('X90m')

@qgl2stub('QGL.PulsePrimitives')
def Y(qubit: qreg, **kwargs) -> pulse:
    print('Y')

@qgl2stub('QGL.PulsePrimitives')
def Y90(qubit: qreg, **kwargs) -> pulse:
    print('Y90')

@qgl2stub('QGL.PulsePrimitives')
def Y90m(qubit: qreg, **kwargs) -> pulse:
    print('Y90m')

@qgl2stub('QGL.PulsePrimitives')
def Z(qubit: qreg, **kwargs) -> pulse:
    print('Z')

@qgl2stub('QGL.PulsePrimitives')
def Z90(qubit: qreg, **kwargs) -> pulse:
    print('Z90')

@qgl2stub('QGL.PulsePrimitives')
def Z90m(qubit: qreg, **kwargs) -> pulse:
    print('Z90m')

@qgl2stub('QGL.PulsePrimitives')
def U90(qubi: qreg, phase=0, **kwargs) -> pulse:
    print('U90')

@qgl2stub('QGL.PulsePrimitives')
def AC(qubit: qreg, cliffNum) -> pulse:
    print('AC')

@qgl2stub('QGL.PulsePrimitives')
def ZX90_CR(controlQ: qreg, targetQ: qreg, **kwargs) -> pulse:
    """
    A calibrated CR ZX90 pulse.  Uses 'amp' for the pulse amplitude, 'phase' for its phase (in deg).
    """
    print('ZX90_CR')

# Used by RB basic sequences
@qgl2stub('QGL.Cliffords')
def clifford_seq(c, q1: qreg, q2: qreg = None) -> sequence:
    print('clifford_seq')

@qgl2stub('QGL.PulsePrimitives')
def flat_top_gaussian(chan: qreg, riseFall, length, amp, phase=0, label="flat_top_gaussian") -> pulse:
    print('flat_top_gaussian')

@qgl2stub('qgl2.qgl1_util', 'flat_top_gaussian_edge_impl')
def flat_top_gaussian_edge(source: qreg, target: qreg, riseFall,
                           length, amp, phase=0, label="flat_top_gussian") -> pulse:
    print('flat_top_gaussian_edge')

# Helper for CPMG, to get around not being able to access qubit params (issue #37)
@qgl2stub('qgl2.qgl1_util', 'pulseCentered')
def pulseCentered(qubit: qreg, pFunc, pulseSpacing) -> pulse:
    print("pFunc(qubit, length=(pulseSpacing - qubit.pulse_params['length']) / 2)")

@qgl2stub('QGL.PulsePrimitives')
def echoCR(controlQ: qreg, targetQ: qreg, amp=1, phase=0, length=200e-9, riseFall=20e-9, lastPi=True) -> pulse:
    print('echoCR')

@qgl2stub('QGL.PulsePrimitives')
def CNOT(controlQ: qreg, targetQ: qreg, **kwargs) -> pulse:
    print('CNOT')

# FIXME: QGL2 can't handle *args
# Calls include: qubit, 2 qubits, qreg list. But so far
# our qgl2 uses are just with a single qreg
@qgl2meas('QGL.PulsePrimitives')
def MEAS(q: qreg, *args, **kwargs) -> pulse:
    print('MEAS')

# Our uses of U never supply any extra kwargs
@qgl2stub('QGL.PulsePrimitives')
def U(qubit: qreg, phase=0, **kwargs) -> pulse:
    print('U')

# Note that this is really a class
#def Edge(**kwargs) -> qreg:
@qgl2stub('QGL.Channels')
def Edge(label, source: qreg, target: qreg, gate_chan, **kwargs) -> qreg:
    # FIXME: Can take source and target which are qregs
    # FIXME: Is qreg the right return type?
    print('Edge')

# Note that this is really a class
#def Qubit(**kwargs) -> qreg:
@qgl2stub('QGL.Channels')
def Qubit(label=None, gate_chan=None, **kwargs) -> qreg:
    print('Qubit')

@qgl2stub('QGL.ChannelLibraries')
def EdgeFactory(source: qreg, target: qreg) -> qreg:
    # Is that the right return?
    print('EdgeFactory')

@qgl2stub('QGL.ChannelLibraries')
def QubitFactory(label) -> qreg:
    print('QubitFactory')

@qgl2stub('QGL.ChannelLibraries')
def MeasFactory(label) -> qreg:
    print('MeasFactory')

@qgl2stub('QGL.ChannelLibraries')
def MarkerFactory(label) -> qreg:
    print('MarkerFactory')

# This is used just in testing mains
# Note that this is really a class
#def LogicalMarkerChannel(**kwargs) -> qreg:
@qgl2stub('QGL.Channels')
def LogicalMarkerChannel(label, **kwargs) -> qreg:
    print('LogicalMarkerChannel')

@qgl2stub('QGL.ControlFlow')
def qwait(kind="TRIG") -> control:
    print('qwait')

# Note that this is really a class
@qgl2stub('QGL.ControlFlow')
def Wait() -> control:
    print('Wait')

@qgl2stub('QGL.ControlFlow')
def Sync() -> control:
    print('Sync')

@qgl2stub('QGL.ControlFlow')
def Barrier(chanlist: qreg) -> control:
    # chanlist is list of channels that are waiting here
    print('Barrier(%s)' % (chanlist))

@qgl2stub('QGL.ControlFlow')
def Store(dest, source) -> control:
    print('STORE %s -> %s' % (source, dest))

@qgl2stub('QGL.ControlFlow')
def LoadCmp() -> control:
    print('LoadCmp')

# Note that these Cmp functions don't really need to be stubs,
# they can be run as is. But making them stubs ensures
# the imports work out.
# operand is expected to be an integer

@qgl2stub('QGL.ControlFlow')
def CmpEq(address, value) -> control:
    print('CMP %s == %s' % (address, value))
@qgl2stub('QGL.ControlFlow')
def CmpNeq(address, value) -> control:
    print('CMP %s != %s' % (address, value))
@qgl2stub('QGL.ControlFlow')
def CmpLt(address, value) -> control:
    print('CMP %s < %s' % (address, value))
@qgl2stub('QGL.ControlFlow')
def CmpGt(address, value) -> control:
    print('CMP %s > %s' % (address, value))

# Functions used by qgl2 compiler from ControlFlow

@qgl2stub('QGL.ControlFlow')
def Goto(target) -> control:
    # target is a BlockLabel
    pass

@qgl2stub('QGL.ControlFlow')
def LoadRepeat(value) -> control:
    # Value is an int # of times to repeat
    pass

@qgl2stub('QGL.ControlFlow')
def Call(target) -> control:
    # target is a BlockLabel
    pass

@qgl2stub('QGL.ControlFlow')
def Return() -> control:
    # Goes back to where you did Call()
    pass

@qgl2stub('QGL.ControlFlow')
def Repeat(target) -> control:
    # target is a BlockLabel
    pass

@qgl2stub('QGL.BlockLabel')
def BlockLabel(label):
    # label is a string, output is a BlockLabel
    pass

# FIXME: I'd like to allow a reference to QGL.ChannelLibraries.channelLib static; how?

# FIXME: I'd like to add these methods on the CL object, but how?
# @qgl2stub('QGL.ChannelLibraries')
# def new_qubit(label, **kwargs) -> qreg:
#     pass

# @qgl2stub('QGL.ChannelLibraries')
# def new_edge(source, target):
#    pass
