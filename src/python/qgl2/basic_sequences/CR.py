# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit

@qgl2decl
def PiRabi(controlQ: qbit, targetQ: qbit, lengths, riseFall=40e-9, amp=1, phase=0, calRepeats=2, showPlot=False):
    """
    Variable length CX experiment.

    Parameters
    ----------
    controlQ : logical channel for the control qubit (LogicalChannel)
    targetQ: logical channel for the target qubit (LogicalChannel)
    lengths : pulse lengths of the CR pulse to sweep over (iterable)
    showPlot : whether to plot (boolean)

    Returns
    -------
    plotHandle : handle to plot window to prevent destruction
    """
    raise Exception("Not implemented")

@qgl2decl
def EchoCRLen(controlQ: qbit, targetQ: qbit, lengths, riseFall=40e-9, amp=1, phase=0, calRepeats=2, showPlot=False):
    """
    Variable length CX experiment, with echo pulse sandwiched between two CR opposite-phase pulses.

    Parameters
    ----------
    controlQ : logical channel for the control qubit (LogicalChannel)
    targetQ: logical channel for the target qubit (LogicalChannel)
    lengths : pulse lengths of the CR pulse to sweep over (iterable)
    showPlot : whether to plot (boolean)

    Returns
    -------
    plotHandle : handle to plot window to prevent destruction
    """
    raise Exception("Not implemented")

@qgl2decl
def EchoCRPhase(controlQ: qbit, targetQ: qbit, phases, riseFall=40e-9, amp=1, length=100e-9, calRepeats=2, showPlot=False):
    """
    Variable phase CX experiment, with echo pulse sandwiched between two CR opposite-phase pulses.

    Parameters
    ----------
    controlQ : logical channel for the control qubit (LogicalChannel)
    CRchan: logical channel for the cross-resonance pulse (LogicalChannel) 
    phases : pulse phases of the CR pulse to sweep over (iterable)
    showPlot : whether to plot (boolean)

    Returns
    -------
    plotHandle : handle to plot window to prevent destruction
    """
    raise Exception("Not implemented")
