# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit, QRegister
from qgl2.util import init
from qgl2.qgl1 import X90, X90m, Y90, MEAS, Id, X

import numpy as np

@qgl2decl
def flipflop_seqs(dragParam, maxNumFFs, qubit: qbit):
    """ Helper function to create a list of sequences with a specified drag parameter. """
    # QGL2 qubits are read only.
    # So instead, supply the dragScaling as an explicit kwarg to all pulses
    # qubit.pulseParams['dragScaling'] = dragParam
    for rep in range(maxNumFFs):
        init(qubit)
        X90(qubit, dragScaling=dragParam)
        # FIXME: Original used [X90] + [X90, X90m]... is this right?
        for _ in range(rep):
            X90(qubit, dragScaling=dragParam)
            X90m(qubit, dragScaling=dragParam)
        Y90(qubit, dragScaling=dragParam)
        MEAS(qubit)

@qgl2decl
def doFlipFlop(qubit:qbit, dragParamSweep, maxNumFFs):

    # QGL2 qubits are read only, so can't modify qubit.pulseParams[dragScaling],
    # So no need to save this off and reset afterwards
    for dragParam in dragParamSweep:
        # Id sequence for reference
        init(qubit)
        Id(qubit)
        MEAS(qubit)

        # then a flip flop sequence for a particular DRAG parameter
        flipflop_seqs(dragParam, maxNumFFs, qubit)

    # Final pi for reference
    init(qubit)
    X(qubit)
    MEAS(qubit)
