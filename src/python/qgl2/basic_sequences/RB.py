# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

def create_RB_seqs(numQubits, lengths, repeats=32, interleaveGate=None):
    """
    Create a list of lists of Clifford gates to implement RB.
    """
    raise Exception("Not implemented")

def SingleQubitRB(qubit, seqs, showPlot=False):
    """

    Single qubit randomized benchmarking using 90 and 180 generators. 

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    seqs : list of lists of Clifford group integers
    showPlot : whether to plot (boolean)

    Returns
    -------
    plotHandle : handle to plot window to prevent destruction
    """	
    raise Exception("Not implemented")

def TwoQubitRB(q1, q2, seqs, showPlot=False, suffix=""):
    """

    Two qubit randomized benchmarking using 90 and 180 single qubit generators and ZX90 

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    seqs : list of lists of Clifford group integers
    showPlot : whether to plot (boolean)

    Returns
    -------
    plotHandle : handle to plot window to prevent destruction
    """	
    raise Exception("Not implemented")

def SingleQubitRB_AC(qubit, seqs, showPlot=False):
    """

    Single qubit randomized benchmarking using atomic Clifford pulses. 

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    seqFile : file containing sequence strings
    showPlot : whether to plot (boolean)

    Returns
    -------
    plotHandle : handle to plot window to prevent destruction
    """	
    raise Exception("Not implemented")

def SingleQubitIRB_AC(qubit, seqFile, showPlot=False):
    """

    Single qubit interleaved randomized benchmarking using atomic Clifford pulses. 

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    seqFile : file containing sequence strings
    showPlot : whether to plot (boolean)

    Returns
    -------
    plotHandle : handle to plot window to prevent destruction
    """	
    raise Exception("Not implemented")

def SingleQubitRBT(qubit, seqFileDir, analyzedPulse, showPlot=False):
    """

    Single qubit randomized benchmarking using atomic Clifford pulses. 

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    seqFile : file containing sequence strings
    showPlot : whether to plot (boolean)

    Returns
    -------
    plotHandle : handle to plot window to prevent destruction
    """	
    raise Exception("Not implemented")

def SimultaneousRB_AC(qubits, seqs, showPlot=False):
    """

    Simultaneous randomized benchmarking on multiple qubits using atomic Clifford pulses. 

    Parameters
    ----------
    qubits : iterable of logical channels to implement seqs on (list or tuple) 
    seqs : a tuple of sequences created for each qubit in qubits
    showPlot : whether to plot (boolean)

    Example
    -------
    >>> q1 = QubitFactory('q1')
    >>> q2 = QubitFactory('q2')
    >>> seqs1 = create_RB_seqs(1, [2, 4, 8, 16])
    >>> seqs2 = create_RB_seqs(1, [2, 4, 8, 16])
    >>> SimultaneousRB_AC((q1, q2), (seqs1, seqs2), showPlot=False)
    """	
    raise Exception("Not implemented")

