# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit, qbit_list, qgl2main

from QGL.PulsePrimitives import Id, X, Y, X90, Y90, MEAS
#from QGL.Compiler import compile_to_hardware
#from QGL.PulseSequencePlotter import plot_pulse_files

from qgl2.qgl1 import Id, X, Y, X90, Y90, MEAS, compile_to_hardware

from .new_helpers import addMeasPulses, repeatSequences, compileAndPlot
from .new_helpers import IdId, XX, YY, XY, YX, X90Id, Y90Id, X90Y90, Y90X90, X90Y, Y90X, \
    XY90, YX90, X90X, XX90, Y90Y, YY90, XId, YId, X90X90, Y90Y90
from .qgl2_plumbing import init

@qgl2decl
def AllXYq2(q: qbit, showPlot = False):
    # This is the kind of thing that I would like to work in QGL2, but
    # doesn't work yet (can't do function references or for loops
    # over a list it can't tell are constant)
    twentyOnepulseFuncs = [IdId, XX, YY, XY, YX, X90Id, Y90Id,
                           X90Y90, Y90X90, X90Y, Y90X, XY90, YX90, X90X,
                           XX90, Y90Y, YY90, XId, YId, X90X90, Y90Y90]

    # For each of the 21 pulse pairs
    for func in twentyOnepulseFuncs:
        # Repeat it twice and do a MEAS at the end of each
        for i in range(2):
            init(q)
            func(q)
            MEAS(q)

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    compileAndPlot('AllXY/AllXY', showPlot)

@qgl2decl
def AllXY(q: qbit, showPlot = False):
    # For each of the 21 pulse pairs
    for func in [IdId, XX, YY, XY, YX, X90Id, Y90Id,
                 X90Y90, Y90X90, X90Y, Y90X, XY90, YX90, X90X,
                 XX90, Y90Y, YY90, XId, YId, X90X90, Y90Y90]:
        # Repeat it twice and do a MEAS at the end of each
        for i in range(2):
            init(q)
            func(q)
            MEAS(q)

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    compileAndPlot('AllXY/AllXY', showPlot)

@qgl2decl
def AllXYtry2(q: qbit, showPlot = False):
    # For each of the 21 pulse pairs
    for func1, func2 in [[Id,Id], [X,X], [Y,Y], [X,Y], [Y,X], [X90,Id], [Y90,Id],
                         [X90,Y90], [Y90,X90], [X90,Y], [Y90,X], [X,Y90], [Y,X90], [X90,X],
                         [X,X90], [Y90,Y], [Y,Y90], [X,Id], [Y,Id], [X90,X90], [Y90,Y90]]:
        # Repeat it twice and do a MEAS at the end of each
        for i in range(2):
            init(q)
            func1(q)
            func2(q)
            MEAS(q)

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    compileAndPlot('AllXY/AllXY', showPlot)


# Imports for testing only
from qgl2.qgl2 import Qbit
#from QGL.Channels import Qubit, LogicalMarkerChannel
#from qgl2.qgl1 import Qubit
from math import pi

@qgl2main
def main():
    # Set up 1 qbit, following model in QGL/test/test_Sequences

    # FIXME: Cannot use these in current QGL2 compiler, because
    # a: QGL2 doesn't understand creating class instances, and 
    # b: QGL2 currently only understands the fake Qbits
#    qg1 = LogicalMarkerChannel(label="q1-gate")
#    q1 = Qubit(label='q1', gateChan=qg1)
#    q1.pulseParams['length'] = 30e-9
#    q1.pulseParams['phase'] = pi/2

    # But the current qgl2 compiler doesn't understand Qubits, only
    # Qbits. So use that instead when running through the QGL2
    # compiler, but comment this out when running directly.
    # And I can't easily make it understand stub Qubits either. Bah.
    # (because it expects the single arg to be an int)
#    q1 = Qubit(label="q1")
    q1 = Qbit(1)
    AllXY(q1)

if __name__ == "__main__":
    main()
