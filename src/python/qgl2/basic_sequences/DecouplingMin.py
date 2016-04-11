import numpy as np
from qgl2.qgl2 import qgl2decl, sequence, qbit
from qgl2.qgl1 import Qubit, X90, Id, Y, U90, MEAS, X90
from qgl2.control import *
from .qgl2_plumbing import init
from .helpers import create_cal_seqs

@qgl2decl
def doHahnEcho() -> sequence:
    q = Qubit('q1')
#    pulseSpacings = np.linspace(0, 5e-6, 11)
#    pulseSpacings = [  0.00000000e+00,   5.00000000e-07,   1.00000000e-06,
#                       1.50000000e-06,   2.00000000e-06,   2.50000000e-06,
#                       3.00000000e-06,   3.50000000e-06,   4.00000000e-06,
#                       4.50000000e-06,   5.00000000e-06]
#    periods = 0
#    for k in range(len(pulseSpacings)):
    for spacing in [  0.00000000e+00,   5.00000000e-07,   1.00000000e-06,
                      1.50000000e-06,   2.00000000e-06,   2.50000000e-06,
                      3.00000000e-06,   3.50000000e-06,   4.00000000e-06,
                      4.50000000e-06,   5.00000000e-06]:
        init(q)
        X90(q)
        # FIXME: spacing arg to Id confuses compiler
        Id(q, length=spacing)
        Y(q)
        Id(q, length=spacing)
#        U90(q, phase=2*pi*periods/len(pulseSpacings)*k)
        U90(q, phase=0)
        MEAS(q)

#    calRepeats = 2
    # FIXME: create_cal_seqs will not yet work in QGL2
#    create_cal_seqs((q,), 2)


@qgl2decl
def doCPMG() -> sequence:
    q = Qubit('q1')

    # FIXME: QGL2 functions cannot be nested
#    @qgl2decl
#    def idPulse(q: qbit) -> pulse:
#        # FIXME: arg confuses QGL2 compiler if not a kwarg
#        Id(q, length=(500e-9 - q.pulseParams['length'])/2)

    # FIXME: QGL2 doesn't understand these for loops yet

    # Create numPulses sequences
    for rep in [0, 2, 4, 6]:
        init(q)
        X90(q)
        # Repeat the t-180-t block rep times
        for _ in range(rep):
            # FIXME: QGL2 functions cannot be nested
            #idPulse(q)
            Id(q, length=(500e-9 - q.pulseParams['length'])/2)
            Y(q)
            Id(q, length=(500e-9 - q.pulseParams['length'])/2)
            #idPulse(q)
        X90(q)
        MEAS(q)

    # Tack on calibration
    # FIXME: create_cal_seqs will not yet work in QGL2
#    create_cal_seqs((q,), 2)
