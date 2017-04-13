# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# QGL2 simplified versions of AllXY

from qgl2.qgl2 import qgl2decl, qreg, QRegister
from qgl2.util import init
from qgl2.qgl1 import MEAS

from qgl2.qgl1 import Id, X, Y, X90, Y90

@qgl2decl
def doAllXY(q:qreg):
    twentyOnePulsePairs = [
            # no pulses to measure |0>
            (Id, Id),
            # pulse around same axis
            (X, X), (Y, Y),
            # pulse around orthogonal axes
            (X, Y), (Y, X),
            # These produce a |+> or |i> state
            (X90, Id), (Y90, Id),
            # pulse pairs around orthogonal axes with 1e error sensititivity
            (X90, Y90), (Y90, X90),
            # pulse pairs with 2e sensitivity
            (X90, Y), (Y90, X), (X, Y90), (Y, X90),
            # pulse pairs around common axis with 3e error sensitivity
            (X90, X), (X, X90), (Y90, Y), (Y, Y90),
            # These create the |1> state
            (X, Id), (Y, Id),
            (X90, X90), (Y90, Y90) ]

    # For each of the 21 pulse pairs
    for (f1, f2) in twentyOnePulsePairs:
        # Repeat it twice and do a MEAS at the end of each
        for i in range(2):
            init(q)
            f1(q)
            f2(q)
            MEAS(q)
