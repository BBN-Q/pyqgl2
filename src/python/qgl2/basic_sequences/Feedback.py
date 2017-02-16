# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit_list, qgl2main, concur, qbit, pulse
from qgl2.qgl1 import Id, MEAS, X
from qgl2.util import init

from qgl2.basic_sequences.helpers import create_cal_seqs
from qgl2.basic_sequences.new_helpers import compileAndPlot

from itertools import product

# The following qreset definitions represent a progression in complexity
# This first one is the simplest (the "goal")

# TODO we don't want this method to be inlined by the compiler
# how do we tell QGL2 not to inline it?
@qgl2decl
def qreset(q: qbit):
    m = MEAS(q)
    if m == 1:
        X(q)

# In this next one, we assume that the hardware might disagree on which
# measurement result indicates qubit state = |0>, so we allow an optional
# sign flip. One way to write this seems to imply TDM computation.

@qgl2decl
def qreset_with_sign_inversion(q: qbit, measSign):
    m = MEAS(q)
    if m == measSign:
        X(q)

# In actuallity, the current definition of "MEAS" does not include a
# necessary element to make this work on real hardware. Namely, we need to
# deal with separate clock domains in the measurement and control systems, so
# we add a delay before checking for the existence of a value to make message
# passing delay deterministic.

@qgl2decl
def qreset_with_delay(q: qbit, delay):
    m = MEAS(q)
    # Wait to make branching time deterministic, and to allow residual
    # measurement photons to decay
    Id(q, delay)
    if m == 1:
        X(q)

# Finally, for short consitional sequences like this, we want each branch
# to consume the same amount of time, therefore the "else" branch should be
# populated with an Id. Putting these things all together we have:

@qgl2decl
def qreset_full(q:qbit, delay, measSign):
    m = MEAS(q)
    Id(q, delay)
    if m == measSign:
        X(q)
    else:
        Id(q)

def Reset(qubits: qbit_list, measDelay = 1e-6, signVec = None,
          doubleRound = True, showPlot = False, docals = True,
          calRepeats=2):
    """
    Reset a qubit register to the ground state.

    Parameters
    ----------
    qubits : tuple of logical channels to implement sequence (LogicalChannel)
    measDelay : delay between end of measuerement and reset pulse
    signVec : Measurement results that indicate that we should flip (default == 1 for all qubits)
    doubleRound : if true, double round of feedback
    showPlot : whether to plot (boolean)
    docals : enable calibration sequences
    calRepeats: number of times to repleat calibration
    """

    if signVec is None:
        signVec = [1]*len(qubits)

    for prep in product([Id,X], repeat=len(qubits)):
        with concur:
            for p,q,measSign in zip(prep, qubits, signVec):
                init(q)
                # prepare the initial state
                p(q)
                qreset_full(q, measDelay, measSign)
                if doubleRound:
                    qreset_full(q, measDelay, measSign)
        # TODO add sugar so that this can be concisely expressed as:
        # MEAS(qubits)
        with concur:
            for q in qubits:
                MEAS(q)

    # If we're doing calibration too, add that at the very end
    # - another 2^numQubits * calRepeats sequences
    if docals:
        create_cal_seqs(qubits, calRepeats)

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    compileAndPlot('Reset/Reset', showPlot)
