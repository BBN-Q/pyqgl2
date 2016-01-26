# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit_list

@qgl2decl
def Reset(qubits: qbit_list, measDelay = 1e-6, signVec = None,
          doubleRound = True, buf = 30e-9, showPlot=False, measChans: qbit_list = None, docals=True, calRepeats=2):
    """

    Variable amplitude Rabi nutation experiment for an arbitrary number of qubits simultaneously

    Parameters
    ----------
    qubits : tuple of logical channels to implement sequence (LogicalChannel)
    measDelay : delay between end of measuerement and LOADCMP
    signVec : conditions for feedback. List of 0 (flip if signal is above threshold) and 1 (flip if below) for each qubit. Default = 0 for all qubits
    doubleRound : if true, double round of feedback
    showPlot : whether to plot (boolean)
    measChans : tuble of qubits to be measured (LogicalChannel)
    docals, calRepeats: enable calibration sequences, repeated calRepeats times

    Returns
    -------
    plotHandle : handle to plot window to prevent destruction
    """
    raise Exception("Not implemented")
