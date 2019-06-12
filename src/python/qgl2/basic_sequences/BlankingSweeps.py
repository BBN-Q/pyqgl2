# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
Sequences for optimizing gating timing.
"""

from qgl2.qgl2 import qgl2decl, qreg

from qgl2.qgl1 import Id, X90, MEAS

from QGL.Compiler import compile_to_hardware

@qgl2decl
def sweep_gateDelay(qubit: qreg, sweepPts):
    """
    Sweep the gate delay associated with a qubit channel using a simple Id, Id, X90, X90
    seqeuence.

    Parameters
    ---------
    qubit : logical qubit to create sequences for
    sweepPts : iterable to sweep the gate delay over.
    """
    raise NotImplementedError("Not implemented")

    # Not apparently used?

    # Problem in doing in QGL2: Need params of the real qubit, which we don't have

    # Original:
#    generator = qubit.phys_chan.generator
#    oldDelay = generator.gateDelay

#    for ct, delay in enumerate(sweepPts):
#        seqs = [[Id(qubit, length=120e-9), Id(qubit), MEAS(qubit)],
#                [Id(qubit, length=120e-9), MEAS(qubit)],
#                [Id(qubit, length=120e-9), X90(qubit), MEAS(qubit)],
#                [Id(qubit, length=120e-9), X90(qubit), MEAS(qubit)]]

#        generator.gateDelay = delay

#        compile_to_hardware(seqs, 'BlankingSweeps/GateDelay', suffix='_{}'.format(ct+1))

#    generator.gateDelay = oldDelay
