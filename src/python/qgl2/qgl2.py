# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
Definitions that must be loaded into each QGL2 module.

In order to be recognized by the compiler, you should include
the following snipped at the start of each module that uses
QGL2 constructs:

from qgl2.qgl2 import concur, qgl2decl, qgl2main
from qgl2.qgl2 import classical, pulse, qbit, qbit_list
from qgl2.qgl2 import Qbit
"""

class concur(object):
    """
    A degenerate class used to create "concurrent" statements via
    the "with" statement.  For example, for the following pseudocode,
    the qgl2 processor will attempt to execute stmnt1 and stmnt2
    concurrently:

        with concur():
            stmnt1
            stmnt2

    The purpose of the "concur()" is to mark these statements as
    things to execute concurrently. 

    The "with concur()" currently has no effect if executed outside
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

def qgl2main(function):
    def wrapper(*args, **kwargs):
        assert False, 'qgl2main should not be directly executed'
    return wrapper

def qgl2decl(function):
    def wrapper(*args, **kwargs):
        assert False, 'qgl2decl should not be directly executed'
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

def Qbit(chan:classical) -> qbit:
    pass
