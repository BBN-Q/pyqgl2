# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

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

@qgl2decl
def init(*args):
    for arg in args:
        qreg_init(arg)

@qgl2stub("qgl2.qgl1_util", "init_real")
def qreg_init(q: qreg) -> control:
    """
    Wait()
    Annotated as returning a pulse for backwards compatibility.
    """

    return
