from qgl2.qgl2 import qgl2decl, qbit, sequence
from .helpers import create_cal_seqs
from .qgl2_plumbing import init
from qgl2.qgl1 import Qubit, X, Id, MEAS, U90
import numpy as np
from numpy import pi

@qgl2decl
def doInversionRecovery() -> sequence:
    # delays = np.linspace(0, 5e-6, 11)
    q = Qubit('q1')
    for d in [  0.00000000e+00,   5.00000000e-07,   1.00000000e-06,
                1.50000000e-06,   2.00000000e-06,   2.50000000e-06,
                3.00000000e-06,   3.50000000e-06,   4.00000000e-06,
                4.50000000e-06,   5.00000000e-06]:
        init(q)
        X(q)
        Id(q, d)
        MEAS(q)

    # Tack on calibration
    # FIXME: This doesn't yet work in QGL2
#    create_cal_seqs((q,), 2)

@qgl2decl
def doRamsey() -> sequence:
    q = Qubit('q1')
    TPPIFreq=1e6
    # FIXME: QGL2 doesn't deal well with the call to np.arange
    pulseS = [  1.00000000e-07,   2.00000000e-07,   3.00000000e-07,
         4.00000000e-07,   5.00000000e-07,   6.00000000e-07,
         7.00000000e-07,   8.00000000e-07,   9.00000000e-07,
         1.00000000e-06,   1.10000000e-06,   1.20000000e-06,
         1.30000000e-06,   1.40000000e-06,   1.50000000e-06,
         1.60000000e-06,   1.70000000e-06,   1.80000000e-06,
         1.90000000e-06,   2.00000000e-06,   2.10000000e-06,
         2.20000000e-06,   2.30000000e-06,   2.40000000e-06,
         2.50000000e-06,   2.60000000e-06,   2.70000000e-06,
         2.80000000e-06,   2.90000000e-06,   3.00000000e-06,
         3.10000000e-06,   3.20000000e-06,   3.30000000e-06,
         3.40000000e-06,   3.50000000e-06,   3.60000000e-06,
         3.70000000e-06,   3.80000000e-06,   3.90000000e-06,
         4.00000000e-06,   4.10000000e-06,   4.20000000e-06,
         4.30000000e-06,   4.40000000e-06,   4.50000000e-06,
         4.60000000e-06,   4.70000000e-06,   4.80000000e-06,
         4.90000000e-06,   5.00000000e-06,   5.10000000e-06,
         5.20000000e-06,   5.30000000e-06,   5.40000000e-06,
         5.50000000e-06,   5.60000000e-06,   5.70000000e-06,
         5.80000000e-06,   5.90000000e-06,   6.00000000e-06,
         6.10000000e-06,   6.20000000e-06,   6.30000000e-06,
         6.40000000e-06,   6.50000000e-06,   6.60000000e-06,
         6.70000000e-06,   6.80000000e-06,   6.90000000e-06,
         7.00000000e-06,   7.10000000e-06,   7.20000000e-06,
         7.30000000e-06,   7.40000000e-06,   7.50000000e-06,
         7.60000000e-06,   7.70000000e-06,   7.80000000e-06,
         7.90000000e-06,   8.00000000e-06,   8.10000000e-06,
         8.20000000e-06,   8.30000000e-06,   8.40000000e-06,
         8.50000000e-06,   8.60000000e-06,   8.70000000e-06,
         8.80000000e-06,   8.90000000e-06,   9.00000000e-06,
         9.10000000e-06,   9.20000000e-06,   9.30000000e-06,
         9.40000000e-06,   9.50000000e-06,   9.60000000e-06,
         9.70000000e-06,   9.80000000e-06,   9.90000000e-06]
    #pulseSpacings=np.arange(100e-9, 10e-6, 100e-9)
    # Create the phases for the TPPI
    phases = 2*pi*TPPIFreq*pulseS
    # Create the basic Ramsey sequence
    # FIXME: QGL2 doesn't deal well with this call to zip
    for d,phase in zip(pulseS, phases):
        init(q)
        X90(q)
        Id(q, d)
        U90(q, phase=phase)
        MEAS(q)

    # Tack on calibration
    # FIXME: create_cal_seqs doesn't yet work in QGL2
    create_cal_seqs((q,), calRepeats)
