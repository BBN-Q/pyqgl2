# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit, sequence
from qgl2.util import init
from qgl2.qgl1 import X90, X90m, Y90, MEAS, QubitFactory, Id, X

import numpy as np

@qgl2decl
def flipflop_seqs(dragScaling, maxNumFFs, qubit: qbit) -> sequence:
    """ Helper function to create a list of sequences with a specified drag parameter. """
    # FIXME: cause qubit is a placeholder, can't access pulseParams
    # So instead, supply the dragScaling as an explicit kwarg to all pulses
    # qubit.pulseParams['dragScaling'] = dragScaling
    for rep in range(maxNumFFs):
        init(qubit)
        X90(qubit, dragScaling=dragScaling)
        # FIXME: Original used [X90] + [X90, X90m]... is this right?
        for _ in range(rep):
            X90(qubit, dragScaling=dragScaling)
            X90m(qubi, dragScaling=dragScaling)
        Y90(qubit, dragScaling=dragScaling)
        MEAS(qubit) # FIXME: Need original dragScaling?

@qgl2decl
def FlipFlopMin() -> sequence:
    # FIXME: No args
    qubit = QubitFactory('q1')
    dragParamSweep = np.linspace(0, 5e-6, 11) # FIXME
    maxNumFFs = 10

    # FIXME: cause qubit is a placeholder, can't access pulseParams
    # originalScaling = qubit.pulseParams['dragScaling']
    for dragParam in dragParamSweep:
        init(qubit)
        Id(qubit)
        MEAS(qubit) # FIXME: Need original dragScaling?

        # FIXME: In original this was [[Id]] + flipflop - is this
        # right?
        flipflop_seqs(dragParam, maxNumFFs, qubit)
    # FIXME: cause qubit is a placeholder, can't access pulseParams
    # qubit.pulseParams['dragScaling'] = originalScaling

    # Add a final pi for reference
    init(qubit)
    X(qubit)
    MEAS(qubit)
