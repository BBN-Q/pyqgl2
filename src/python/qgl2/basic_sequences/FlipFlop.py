# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit

from QGL.PulsePrimitives import X90, X90m, Y90, Id, X, MEAS
from QGL.Compiler import compile_to_hardware
from QGL.PulseSequencePlotter import plot_pulse_files

from itertools import chain

@qgl2decl
def FlipFlop(qubit: qbit, dragParamSweep, maxNumFFs=10, showPlot=False):
    """

    Flip-flop sequence (X90-X90m)**n to determine off-resonance or DRAG parameter optimization.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    dragParamSweep : drag parameter values to sweep over (iterable)
    maxNumFFs : maximum number of flip-flop pairs to do
    showPlot : whether to plot (boolean)

    Returns
    -------
    plotHandle : handle to plot window to prevent destruction
    """
    raise NotImplementedError("Not implemented")

    # Original:
    # def flipflop_seqs(dragScaling):
    #     """ Helper function to create a list of sequences with a specified drag parameter. """
    #     qubit.pulseParams['dragScaling'] = dragScaling
    #     return [[X90(qubit)] + [X90(qubit), X90m(qubit)]*rep + [Y90(qubit)] for rep in range(maxNumFFs)]

    # # Insert an identity at the start of every set to mark them off
    # originalScaling = qubit.pulseParams['dragScaling']
    # seqs = list(chain.from_iterable([[[Id(qubit)]] + flipflop_seqs(dragParam) for dragParam in dragParamSweep]))
    # qubit.pulseParams['dragScaling'] = originalScaling

    # # Add a final pi for reference
    # seqs.append([X(qubit)])

    # # Add the measurment block to every sequence
    # measBlock = MEAS(qubit)
    # for seq in seqs:
    #     seq.append(measBlock)

    # fileNames = compile_to_hardware(seqs, 'FlipFlop/FlipFlop')
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)

