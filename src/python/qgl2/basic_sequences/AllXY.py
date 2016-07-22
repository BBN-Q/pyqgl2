# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit, qbit_list, qgl2main, sequence
from qgl2.qgl1 import QubitFactory

#from QGL.PulsePrimitives import Id, X, Y, X90, Y90, MEAS
#from QGL.Compiler import compile_to_hardware
#from QGL.PulseSequencePlotter import plot_pulse_files

from qgl2.qgl1 import Id, X, Y, X90, Y90, MEAS
from qgl2.control import *

from qgl2.basic_sequences.new_helpers import addMeasPulses, repeatSequences, compileAndPlot
from qgl2.basic_sequences.new_helpers import IdId, XX, YY, XY, YX, X90Id, Y90Id, X90Y90, Y90X90, X90Y, Y90X, \
    XY90, YX90, X90X, XX90, Y90Y, YY90, XId, YId, X90X90, Y90Y90
from qgl2.util import init

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
def doAllXY() -> sequence:
    q = QubitFactory(label="q1")
    # For each of the 21 pulse pairs
    for func in [IdId, XX, YY, XY, YX, X90Id, Y90Id,
                 X90Y90, Y90X90, X90Y, Y90X, XY90, YX90, X90X,
                 XX90, Y90Y, YY90, XId, YId, X90X90, Y90Y90]:
        # Repeat it twice and do a MEAS at the end of each
        for i in range(2):
            init(q)
            func(q)
            MEAS(q)

@qgl2decl
def AllXY(q: qbit, showPlot = False):
    # I'm not sure this would ever be run like this.
    # But logically we want something like this
    sequences = pyqgl2.main.main(doAllXY(q))()
    compileAndPlot(sequences, 'AllXY/AllXY', showPlot)

@qgl2decl
def AllXYprev(q: qbit, showPlot = False):
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

# Imports for testing only
#from QGL.Channels import Qubit, LogicalMarkerChannel
from qgl2.qgl1 import QubitFactory
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

    q1 = QubitFactory(label="q1")
    AllXY(q1)

if __name__ == "__main__":
    main()
