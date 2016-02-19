# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit, qbit_list

from QGL.PulsePrimitives import Id, X, Y, X90, Y90, MEAS
from QGL.Compiler import compile_to_hardware
from QGL.PulseSequencePlotter import plot_pulse_files

from .new_helpers import addMeasPulses, repeatSequences, compileAndPlot
from .new_helpers import IdId, XX, YY, XY, YX, X90Id, Y90Id, X90Y90, Y90X90, X90Y, Y90X, \
    XY90, YX90, X90X, XX90, Y90Y, YY90, XId, YId, X90X90, Y90Y90

@qgl2decl
def AllXY(q: qbit, showPlot = False):
    # Dan says for now, the compiler doesn't understand function references. So I can's use IdId for example
    # And it also doesn't do the for loops yet
    # So this may be what I have to do for now - completely unrolled / explicit

    # These produce the state |0>
    # No pulses
    Id(q)
    Id(q)
    MEAS(q)

    Id(q)
    Id(q)
    MEAS(q)

    # Pulsing around the same axis
    X(q)
    X(q)
    MEAS(q)

    X(q)
    X(q)
    MEAS(q)

    Y(q)
    Y(q)
    MEAS(q)

    Y(q)
    Y(q)
    MEAS(q)

    # Pulsing around orthogonal axes
    X(q)
    Y(q)
    MEAS(q)

    X(q)
    Y(q)
    MEAS(q)

    Y(q)
    X(q)
    MEAS(q)

    Y(q)
    X(q)
    MEAS(q)

    # These next create a |+> or |i> state (equal superposition of |0> + |1>)
    # single pulses
    X90(q)
    Id(q)
    MEAS(q)

    X90(q)
    Id(q)
    MEAS(q)

    Y90(q)
    Id(q)
    MEAS(q)

    Y90(q)
    Id(q)
    MEAS(q)

    # Pulse pairs around orthogonal axes with 1e error sensitivity
    X90(q)
    Y90(q)
    MEAS(q)

    X90(q)
    Y90(q)
    MEAS(q)

    Y90(q)
    X90(q)
    MEAS(q)

    Y90(q)
    X90(q)
    MEAS(q)

    # Pulse pairs with 2e erro sensitivity
    X90(q)
    Y(q)
    MEAS(q)

    X90(q)
    Y(q)
    MEAS(q)

    Y90(q)
    X(q)
    MEAS(q)

    Y90(q)
    X(q)
    MEAS(q)

    X(q)
    Y90(q)
    MEAS(q)

    X(q)
    Y90(q)
    MEAS(q)

    Y(q)
    X90(q)
    MEAS(q)

    Y(q)
    X90(q)
    MEAS(q)

    # Pulse pairs around common axis with 3e error sensitivity
    X90(q)
    X(q)
    MEAS(q)

    X90(q)
    X(q)
    MEAS(q)

    X(q)
    X90(q)
    MEAS(q)

    X(q)
    X90(q)
    MEAS(q)

    Y90(q)
    Y(q)
    MEAS(q)

    Y90(q)
    Y(q)
    MEAS(q)

    Y(q)
    Y90(q)
    MEAS(q)

    Y(q)
    Y90(q)
    MEAS(q)

    # These next create the |1> state
    # single pulses
    X(q)
    Id(q)
    MEAS(q)

    X(q)
    Id(q)
    MEAS(q)

    Y(q)
    Id(q)
    MEAS(q)

    Y(q)
    Id(q)
    MEAS(q)

    # Pulse pairs
    X90(q)
    X90(q)
    MEAS(q)

    X90(q)
    X90(q)
    MEAS(q)

    Y90(q)
    Y90(q)
    MEAS(q)

    Y90(q)
    Y90(q)
    MEAS(q)

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    compileAndPlot('AllXY/AllXY', showPlot)

@qgl2decl
def AllXYq2_loop_unrolling(q: qbit, showPlot = False):
    # Dan says for now, the compiler doesn't understand function references. So I can's use IdId for example
    # So here is a slightly degraded version

    # These produce the state |0>
    # No pulses
    for _ in range(2):
        Id(q)
        Id(q)
        MEAS(q)

    # Pulsing around the same axis
    for _ in range(2):
        X(q)
        X(q)
        MEAS(q)
    for _ in range(2):
        Y(q)
        Y(q)
        MEAS(q)

    # Pulsing around orthogonal axes
    for _ in range(2):
        X(q)
        Y(q)
        MEAS(q)
    for _ in range(2):
        Y(q)
        X(q)
        MEAS(q)

    # These next create a |+> or |i> state (equal superposition of |0> + |1>)
    # single pulses
    for _ in range(2):
        X90(q)
        Id(q)
        MEAS(q)
    for _ in range(2):
        Y90(q)
        Id(q)
        MEAS(q)

    # Pulse pairs around orthogonal axes with 1e error sensitivity
    for _ in range(2):
        X90(q)
        Y90(q)
        MEAS(q)
    for _ in range(2):
        Y90(q)
        X90(q)
        MEAS(q)

    # Pulse pairs with 2e erro sensitivity
    for _ in range(2):
        X90(q)
        Y(q)
        MEAS(q)
    for _ in range(2):
        Y90(q)
        X(q)
        MEAS(q)
    for _ in range(2):
        X(q)
        Y90(q)
        MEAS(q)
    for _ in range(2):
        Y(q)
        X90(q)
        MEAS(q)

    # Pulse pairs around common axis with 3e error sensitivity
    for _ in range(2):
        X90(q)
        X(q)
        MEAS(q)
    for _ in range(2):
        X(q)
        X90(q)
        MEAS(q)
    for _ in range(2):
        Y90(q)
        Y(q)
        MEAS(q)
    for _ in range(2):
        Y(q)
        Y90(q)
        MEAS(q)

    # These next create the |1> state
    # single pulses
    for _ in range(2):
        X(q)
        Id(q)
        MEAS(q)
    for _ in range(2):
        Y(q)
        Id(q)
        MEAS(q)

    # Pulse pairs
    for _ in range(2):
        X90(q)
        X90(q)
        MEAS(q)
    for _ in range(2):
        Y90(q)
        Y90(q)
        MEAS(q)

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    compileAndPlot('AllXY/AllXY', showPlot)

@qgl2decl
def AllXYq2(q: qbit, showPlot = False):
    # This is the kind of thing that I would like to work in QGL2, but
    # doesn't yet
    twentyOnepulseFuncs = [IdId, XX, YY, XY, YX, X90Id, Y90Id,
                           X90Y90, Y90X90, X90Y, Y90X, XY90, YX90, X90X,
                           XX90, Y90Y, YY90, XId, YId, X90X90, Y90Y90]

    # For each of the 21 pulse pairs
    for func in twentyOnepulseFuncs:
        # Repeat it twice and do a MEAS at the end of each
        for i in range(2):
            func(q)
            MEAS(q)

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    compileAndPlot('AllXY/AllXY', showPlot)

def AllXYq1(q: qbit, showPlot = False):
    # Revised basic sequence test to try to be more readable, but
    # fundamentally a QGL1 version

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

    # Result is something like:
#        [ Id(q),  Id(q), MEAS(q)], # no pulses
#        [ Id(q),  Id(q), MEAS(q)], # no pulses
#        ....

    compileAndPlot(seqs, 'AllXY/AllXY', showPlot)
