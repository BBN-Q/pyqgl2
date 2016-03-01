# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit, pulse
from QGL import ControlFlow

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
    ControlFlow.Wait()

# Next 2 bits are intended to let the QGL2 compiler know when a function needs to be handed a list of sequences,
# a QGL1 style argument.
# Decorate the function with @qgl2AddSequences if you want the QGL2
# compiler to add the argument to the function call, and/or add the
# sequence_list tag to indicate which argument is the (single) list of sequences argument.
# If using the tagged approach, that argument must be passed to the function or be a keyword argument (in general)
# The compiler will replace the provided value with the correct value

# Tag to indicate that an argument is a list of sequences (which are lists of pulses)
# Used by QGL2 compiler to ID variable to substitute
sequence_list = 'sequence_list'

# Decorator to insert a list of sequences as the first argument to the wrapped function
# Or replace the provided value that is a sequence_list with that from the compiler
def qgl2AddSequences(function):
    @functools.wraps(function)
    def wrap_function(*args, **kwargs):

        # FIXME: QGL2 Compiler must replace this ***********
        QGL2_LIST_OF_SEQUENCES = [[None],[None]]

        # Try to find the spot for the listOfSequences using the annotation
        idx = 0
        sig = inspect.signature(function)
        found = False
        for param in sig.parameters:
            # Look for the single parameter of type sequence_list
            if sig.parameters[param].annotation == sequence_list:
                found = True
                if param in kwargs:
                    # If it is a KW arg that was supplied, replace the value
                    kwargs[param] = QGL2_LIST_OF_SEQUENCES
                    break
                else:
                    # It will be a non keyword arg
                    if (len(args)+len(kwargs)) < len(sig.parameters) and idx == 0:
                        # If it is the first arg in the signature and not enough args were given,
                        # insert it as the first arg
                        args = tuple([QGL2_LIST_OF_SEQUENCES]) + args
                        break
                    elif idx < len(args) and (len(args)+len(kwargs)) == len(sig.parameters):
                        # If the right number of args were given and the sequence_list is one of the non kw args,
                        # replace the provided value with this one
                        # FIXME: What if kwargs had a default?
                        args = tuple(args[:idx]) + tuple([QGL2_LIST_OF_SEQUENCES]) + tuple(args[idx+1:])
                        break
                    else:
                        # Didn't get enough arguments and seq_list isn't first arg,
                        # or something else and I don't know how to handle this
                        # Raise an error?
                        print("Failed to find sequence_list arg in call to %s(%s, %s)" % (function.__name__,
                                                                                          args, kwargs))
                        break
            idx += 1
        if not found:
            if len(sig.parameters) == len(args) + len(kwargs) + 1:
                # Missing exactly one arg: put this one first
                # FIXME: What if kwargs had a default?
                return function(QGL2_LIST_OF_SEQUENCES, args, kwargs)
        return function(*args, **kwargs)
    return wrap_function

