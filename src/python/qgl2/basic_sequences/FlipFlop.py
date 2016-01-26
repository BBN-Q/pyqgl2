# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit

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
    raise Exception("Not implemented")
