# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# from QGL.PulseShapes import tanh

import numpy as np

# a local copy of QGL.PulseShapes.tanh, because pulling in
# QGL/__init__.py causes QGL2 grief.
# See RabiWidth
# - FIXME: No longer needed?
def local_tanh(amp=1, length=0, sigma=0, cutoff=2, sampling_rate=1e9, **params):
    '''
    A rounded constant shape from the sum of two tanh shapes.
    '''
    numPts = int(np.round(length * sampling_rate))
    xPts = np.linspace(-length / 2, length / 2, numPts)
    x1 = -length / 2 + cutoff * sigma
    x2 = +length / 2 - cutoff * sigma
    return amp * 0.5 * (np.tanh((xPts - x1) / sigma) + np.tanh(
                (x2 - xPts) / sigma)).astype(np.complex)

