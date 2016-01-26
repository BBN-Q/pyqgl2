# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit

@qgl2decl
def SPAM(qubit: qbit, angleSweep, maxSpamBlocks=10, showPlot=False):
    """

    X-Y sequence (X-Y-X-Y)**n to determine quadrature angles or mixer correction.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    angleSweep : angle shift to sweep over
    maxSpamBlocks : maximum number of XYXY block to do
    showPlot : whether to plot (boolean)

    Returns
    -------
    plotHandle : handle to plot window to prevent destruction
    """
    raise NotImplementedError("Not implemented")

