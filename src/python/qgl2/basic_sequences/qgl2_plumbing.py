# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit, pulse
from QGL.ControlFlow import Wait
from qgl2.qgl1 import Wait

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
# Init is the marker of a new sequence
@qgl2decl
def init(q: qbit) -> pulse:
    # FIXME: Mark as returning a pulse?
    # For now, just do a wait
    Wait()
