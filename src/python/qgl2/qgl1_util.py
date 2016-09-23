# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# TODO this should be part of QGL, not in QGL2

from QGL.ControlFlow import Sync, Wait

def init_real(q):
    return [
        Sync(),
        Wait()
    ]
