
# Copyright 2016 by Raytheon BBN Technologies Corp. All Rights Reserved.

# Pull in the symbols that QGL2 uses to embellish the
# Python3 syntax.  This must be done in every Python
# file that uses any of these symbols.
#
from qgl2.qgl2 import concur, qgl2decl, qgl2main
from qgl2.qgl2 import classical, pulse, qbit, qbit_list
from qgl2.qgl1 import QubitFactory, MEAS, X


@qgl2decl
def initq(a:qbit, b:qbit):

    with concur:
        while MEAS(a):
            X(a)
        while MEAS(b):
            X(b)


@qgl2main
def main():

    q1 = QubitFactory("1")
    q2 = QubitFactory("2")
    initq(q1,q2)
    print ("Completed QGL main")
