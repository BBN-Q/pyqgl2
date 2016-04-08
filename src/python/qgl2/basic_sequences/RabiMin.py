# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit, sequence, concur
from qgl2.qgl1 import Qubit, Utheta, MEAS
from .qgl2_plumbing import init
import numpy as np

# For use with pyqgl2.main
# Note hard coded amplitudes and phase
@qgl2decl
def doRabiAmp() -> sequence:
    q = Qubit('q1') # Default qubit that will be replaced
    with concur: # QGL2 artifact that will be removed
        # QGL2 cannot yet handle evaluating this itself
#        for amp in np.linspace(0,1,11):
        for amp in [ 0. ,  0.1,  0.2,  0.3,  0.4,  0.5,  0.6,  0.7,  0.8,  0.9,  1. ]:
            init(q)
            Utheta(q, amp=amp, phase=0)
            MEAS(q)
