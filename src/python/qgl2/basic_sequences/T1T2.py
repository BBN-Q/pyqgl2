# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit

@qgl2decl
def InversionRecovery(qubit: qbit, delays, showPlot=False, calRepeats=2, suffix=False):
    """
    Inversion recovery experiment to measure qubit T1

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    delays : delays after inversion before measurement (iterable; seconds)
    showPlot : whether to plot (boolean)
    calRepeats : how many repetitions of calibration pulses (int)

    Returns
    -------
    plotHandle : handle to plot window to prevent destruction
    """
    raise NotImplementedError("Not implemented")

@qgl2decl
def Ramsey(qubit: qbit, pulseSpacings, TPPIFreq=0, showPlot=False, calRepeats=2, suffix=False):
    """
    Variable pulse spacing Ramsey (pi/2 - tau - pi/2) with optional TPPI.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    pulseSpacings : pulse spacings (iterable; seconds)
    TPPIFreq : frequency for TPPI phase updates of second Ramsey pulse (Hz)
    showPlot : whether to plot (boolean)
    calRepeats : how many repetitions of calibration pulses (int)

    Returns
    -------
    plotHandle : handle to plot window to prevent destruction
    """
    raise NotImplementedError("Not implemented")

