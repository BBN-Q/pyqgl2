# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.
@qgl2decl
def HahnEcho(qubit, pulseSpacings, periods = 0, calRepeats=2, showPlot=False):
    """
    A single pulse Hahn echo with variable phase of second pi/2 pulse. 
    
    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    pulseSpacings : pulse spacings to sweep over; the t in 90-t-180-t-180 (iterable)
    periods: number of artificial oscillations
    calRepeats : how many times to repeat calibration scalings (default 2)
    showPlot : whether to plot (boolean)

    Returns
    -------
    plotHandle : handle to plot window to prevent destruction
    """
    raise Exception("Not implemented")

@qgl2decl
def CPMG(qubit, numPulses, pulseSpacing, calRepeats=2, showPlot=False):
    """
    CPMG pulse train with fixed pulse spacing. Note this pulse spacing is centre to centre,
    i.e. it accounts for the pulse width
    
    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    numPulses : number of 180 pulses; should be even (iterable)
    pulseSpacing : spacing between the 180's (seconds)
    calRepeats : how many times to repeat calibration scalings (default 2)
    showPlot : whether to plot (boolean)

    Returns
    -------
    plotHandle : handle to plot window to prevent destruction
    """
    raise Exception("Not implemented")

