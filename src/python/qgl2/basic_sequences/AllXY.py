# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit, qbit_list

from QGL.PulsePrimitives import Id, X, Y, X90, Y90, MEAS
from QGL.Compiler import compile_to_hardware
from QGL.PulseSequencePlotter import plot_pulse_files

from .new_helpers import addMeasPulses, repeatSequences, compileAndPlot

@qgl2decl
def AllXY(q: qbit, showPlot = False):
    # Revised basic sequence test to try to be more readable

    # Original calculated 2 separate lists of 21 pulses intended to be done together
    # Here we merge the lists together manually first, to be more clear / explicit
    firstAndSecondPulses = [
        # These produce the state |0>
        [ Id(q),  Id(q)], # no pulses
        [ X(q),   X(q)], # pulsing around the same axis
        [ Y(q),   Y(q)],
        [ X(q),   Y(q)], # pulsing around orthogonal axes
        [ Y(q),   X(q)],
        # These next create a |+> or |i> state (equal superposition of |0> + |1>)
        [ X90(q), Id(q)], # single pulses
        [ Y90(q), Id(q)],
        [ X90(q), Y90(q)], # pulse pairs around orthogonal axes with 1e error sensitivity
        [ Y90(q), X90(q)],
        [ X90(q), Y(q)], # pulse pairs with 2e error sensitivity
        [ Y90(q), X(q)],
        [ X(q),   Y90(q)],
        [ Y(q),   X90(q)],
        [ X90(q), X(q)], # pulse pairs around common axis with 3e error sensitivity
        [ X(q),   X90(q)],
        [ Y90(q), Y(q)],
        [ Y(q),   Y90(q)],
        # These next create the |1> state
        [ X(q),   Id(q)], # single pulses
        [ Y(q),   Id(q)],
        [ X90(q), X90(q)], # pulse pairs
        [ Y90(q), Y90(q)]
    ]

    # Add a MEAS to each sequence and repeat each sequence
    seqs = repeatSequences(addMeasPulses(firstAndSecondPulses, [q]))

    # You would think that the ControlFlow.repeatall would do the same thing, but it doesn't seem to
    # seqs = repeatall(2, addMeasPulses(firstAndSecondPulses, [q]))

    # Result is something like:
#        [ Id(q),  Id(q), MEAS(q)], # no pulses
#        [ Id(q),  Id(q), MEAS(q)], # no pulses
#        ....

    compileAndPlot(seqs, 'AllXY/AllXY', showPlot)
