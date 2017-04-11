# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
Definitions that must be loaded into each QGL2 module.

In order to be recognized by the compiler, you should include
the following snippet at the start of each module that uses
QGL2 constructs:

from qgl2.qgl2 import qgl2decl, qgl2main, QRegister
from qgl2.qgl2 import classical, pulse, qbit, qbit_list, sequence, control
"""

from functools import wraps

def qgl2main(function):
    @wraps(function)
    def wrapper(*f_args, **f_kwargs):
        return function
    wrapper.__qgl2_wrapper__ = 'qgl2decl'
    return wrapper

def qgl2decl(function):
    @wraps(function)
    def wrapper(*f_args, **f_kwargs):
        return function
    wrapper.__qgl2_wrapper__ = 'qgl2decl'
    return wrapper

def qgl2stub(import_path=None, origName=None):
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

    def deco(func):

        @wraps(func)

        def wrapper(*f_args, **f_kwargs):
            return func(*f_args, **f_kwargs)

        wrapper.__qgl2_wrapper__ = 'qgl2stub'
        wrapper.__qgl_implicit_import__ = import_path
        return wrapper

    return deco

def qgl2meas(import_path=None):
    '''
    Mark a function as a stub for a QGL1 measurement. These differ from
    qgl2stub's because measurements return run-time values.

    import_path gives the name of the module containing the definition of
    the measurement.
    '''
    def deco(function):
        @wraps(function)
        def wrapper(*f_args, **f_kwargs):
            return function(*f_args, **f_kwargs)
        wrapper.__qgl2_wrapper__ = 'qgl2meas'
        wrapper.__qgl2_implicit_import = import_path
        return wrapper

    return deco

def QRegister(*args):
    pass

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
