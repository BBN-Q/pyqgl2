# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
Definitions that must be loaded into each QGL2 module.

In order to be recognized by the compiler, you should include
the following snipped at the start of each module that uses
QGL2 constructs:

from qgl2.qgl2 import concur, qgl2decl, qgl2main
from qgl2.qgl2 import classical, pulse, qbit, qbit_list, sequence, control, GATHER_SEQUENCES
from qgl2.qgl1 import *
"""

from qgl2.qgl1 import Sync, Wait

class SimpleWithObject(object):
    """
    Base class that defines a degenerate __enter__ and __exit__
    method, so that instances of this class or its subclasses
    can be used as "with" objects.

    (somewhat unexpectedly, the base object class does not
    include any __exit__ method at all, although it *does*
    include an __enter__ method)
    """

    def __init__(self, *args, **kwargs):
        """
        Provided in case a superclass calls it, but does nothing
        """
        pass

    def __enter__(self):
        return True

    def __exit__(self, extype, value, traceback):
        """
        A degenerate __exit__ that passes all exceptions through
        """

        return False


class Concur(SimpleWithObject):
    """
    A degenerate class used to create "concurrent" statements via
    the "with" statement.  For example, for the following pseudocode,
    the qgl2 processor will attempt to execute stmnt1 and stmnt2
    concurrently:

        with Concur():
            stmnt1
            stmnt2

    The purpose of the "concur()" is to mark these statements as
    things to execute concurrently. 

    The "with Concur()" currently has no effect if executed outside
    of a qgl2 context.  If the statements don't have any side
    effects, executing them concurrently or sequentially should
    have the same effect. (it's tempting to have it be an error,
    however, because even though it should behave correctly, it
    means that the programmer is confused)

    I've included a quasi-degenerate __init__() because we've tossed
    around some ideas for how we could use pseudo-parameters to provide
    additional info to the preprocessor, but this behavior hasn't been
    defined yet.
    """

    def __init__(self, *args, **kwargs):
        pass


class Seq(SimpleWithObject):
    """
    Similar to Concur, but used to create "sequences" of statements
    via the "with" statement.  For example, for the following pseudocode,
    the qgl2 processor will attempt to execute stmnt1 and stmnt2 in
    sequence, while concurrently attempting to execute stmnt3 and stmnt4
    in sequence:

        with Concur():
            with Seq():
                stmnt1
                stmnt2
            with Seq():
                stmnt3
                stmnt4

    The "with Seq()" currently has no effect if executed outside
    of a qgl2 context.

    This bit of syntax may go away, once we can infer things
    more cleanly, but I'm keeping it for prototyping purposes.
    """

    def __init__(self, *args, **kwargs):
        pass


def qgl2main(function):
    def wrapper(*f_args, **f_kwargs):
        return function
    return wrapper

def qgl2decl(function):
    def wrapper(*f_args, **f_kwargs):
        return function
    return wrapper

def qgl2stub(function, **args):
    '''
    Mark a function as a stub for a QGL1 function, and add
    proper annotations.

    Check the arguments, but do not inline the contents.

    If there is a second arg, then it must be a string that defines
    the name of the module (relative to the active import path)
    containing the definition of the stub.  If a third arg is
    also defined, it contains the original name of the symbol
    in that module.  For example, if the function being decorated
    as a stub is named 'foo', and it is defined in module
    'a.b.c' as 'bar', then its stub decorator would be

    @qgl2stub('a.b.c', 'bar')

    and this would instruct the preprocessor to add an import
    of the form

    from a.b.c import bar as foo

    in the output QGL code.
    '''

    def wrapper(*f_args, **f_kwargs):
        return function
    return wrapper

# Symbols used for method signature annotation.  Their value has
# no meaning; they're only assigned a value so that Python considers
# them to be valid symbols.
#
# These names might need to change if they are confused with local symbols
#
classical = True
qbit = True
qbit_list = True
pulse = True
sequence = True
control = True

concur = Concur()
seq = Seq()

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

@qgl2decl
def init(q: qbit) -> pulse:
    """
    Sync() and then Wait()

    Annotated as returning a pulse for backwards compatibility.
    """

    Sync()
    Wait()
