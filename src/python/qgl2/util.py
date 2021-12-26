# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl1 import MEASA, Invalidate
from qgl2.qgl2 import qreg, pulse, control, qgl2decl, qgl2stub

# init will demarcate the beginning of a list of
# experiments. QGL1 compiler injects WAITs in beginning of
# every sequence for now
# In QGL1 there's an implicit `init_qubits` at the beginning of each sequence.
# `compile_sequence` adds it [here](https://github.com/BBN-Q/QGL/blob/master/QGL/Compiler.py#L303)
# by forcing each sequence to wait for a trigger which will come
# at a long enough interval that the qubit will relax to the ground state.
# In QGL2 this will not be hidden magic and the programmer should have to call `init`
# (everywhere you see `seq = []` would probably translate to `init` for now).
# There is still some discussion needed because the injected wait also serves
# to synchronize multiple channels and it seems that should still happen automagically for the programmer.
# There will be multiple ways to call init() and the programmer must choose.
# init is the marker of a new sequence

# Here we make init be a stub that takes a qubit, so the QGL2 code
# doesn't get confused that it contains things that don't take a
# qubit. Later if it does real stuff for which we want QGL2 to do
# error checking, etc, then make this a qgl2decl instead.

@qgl2stub("qgl2.qgl1_util", "init_real")
def init(q: qreg) -> control:
    """
    Wait()
    Annotated as returning a pulse for backwards compatibility.
    """

    return

@qgl2decl
def QMeas(q: qreg, qval=None):

    maddr = 0
    if qval is not None:
        maddr = qval.addr

    bitpos = 0
    mask = 0
    for qbit in q:
        mask += (1 << bitpos)
        bitpos += 1

    # no mask?  must be nothing to do
    #
    if mask:
        # TODO: we should only invalidate the mask, because that's the
        # only part that will become valid after the measurements, but
        # should we zero-out the entire word?
        #
        Invalidate(maddr, mask)

        bitpos = 0
        for qbit in q:
            MEASA(qbit, maddr=(maddr, bitpos))
            bitpos += 1
