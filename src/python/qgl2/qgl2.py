# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
Definitions that must be loaded into each QGL2 module.

In order to be recognized by the compiler, you should include
the following snipped at the start of each module that uses
QGL2 constructs:

from qgl2 import concur, qgl2decl
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

    The "with concur()" has no effect if executed outside of a qgl2
    context.

    I've included a quasi-degenerate __init__() because we've tossed
    around some ideas for how we could use pseudo-parameters to provide
    additional info to the preprocessor, but this behavior hasn't been
    defined yet.
    """

    def __init__(self, *args, **kwargs):
        pass


def qgl2decl(*qargs):
    """
    A decorator that allows the programmer to declare a function
    or method to be quantum, and to specify which parameters of
    a method are quantum bits.  It can also be used to specify
    which bits map to which parameters, in the cases where the
    programmer has this information.

    For example, the following declares that parameters "a" and "d"
    are quantum bits, and that "b", and "c" are not:

        @qtypes('a', 'd')
        def foo(a, b, c, d):
            ...

    To assign specific bits, the following declares that parameter
    "a" is qbit 1, and "d" is qbit 2.

        @qtypes(('a', 1), ('d', 2))
        def foo(a, b, c, d):
            ...

    At this time, all of the parameters must be constants (i.e. you
    cannot specify the parameter name or qbit number as the value of
    an arbitrary expression).

    Note that the parens are required: because this decorator may take
    parameters, it must be given an empty tuple in lieu of parameters.
    So the empty declaration is

        @qtypes()

    and never

        @qtypes
    """

    def inner_decorator(function):
        def wrapper(*args, **kwargs):
            function(*args, **kwargs)
        return wrapper
    return inner_decorator
