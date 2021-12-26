
# System imports aren't quite working yet.
#
import os
import re
import sys

# Pull in the symbols that QGL2 uses to embellish the
# Python3 syntax.  This must be done in every Python
# file that uses any of these symbols.
#
from qgl2.qgl2 import concur, qgl2decl, qgl2main
from qgl2.qgl2 import classical, pulse, qreg
from qgl2.qgl1 import QubitFactory

# Examples of import and from statements

# Note you must run from this file's directory for this import to work
from level1 import foo

def not_qgl():
    """ a function that isn't QGL """
    print("not qgl")

@qgl2decl
def alpha(chan) -> qreg:
    # you can't create a qreg in a return statement
    # with a non string argument
    # so this is wrong
    return foo(chan)

@qgl2decl
def beta(chan:classical) -> qreg:
    return alpha(chan)

@qgl2main
def main():

    q1 = beta(1)
    q2 = beta(2)

def example_use():
    print('About to do QGL main')
    main()
    print('Did QGL main')


