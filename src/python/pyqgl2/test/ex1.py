# Copyright 2016 by Raytheon BBN Technologies Corp. All Rights Reserved.

# Pull in the symbols that QGL2 uses to embellish the
# Python3 syntax.  This must be done in every Python
# file that uses any of these symbols.
#
from qgl2.qgl2 import concur, qgl2decl, qgl2main
from qgl2.qgl2 import classical, pulse, qbit, qbit_list
from qgl2.qgl2 import Qbit

def test_loops(a:qbit, b:qbit):

    x = Qbit(1)
    x = r
    v1 = MEAS(d)

    with concur:
        while True:
            v1 = MEAS(d)
            X90(qbit1)
            if v1:
                break

        while True:
            v2 = MEAS(b)
            Y90(qbit2)
            if v2:
                break

    with concur:
        print('fred')



