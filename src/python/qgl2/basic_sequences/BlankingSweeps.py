# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
Sequences for optimizing gating timing.
"""

from qgl2.qgl2 import qgl2decl, qbit

@qgl2decl
def sweep_gateDelay(qubit: qbit, sweepPts):
    """
    Sweep the gate delay associated with a qubit channel using a simple Id, Id, X90, X90
    seqeuence.

    Parameters
    ---------
    qubit : logical qubit to create sequences for
    sweepPts : iterable to sweep the gate delay over.
    """
    raise Exception("Not implemented")
