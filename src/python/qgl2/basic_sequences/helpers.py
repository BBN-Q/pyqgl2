# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit_list

@qgl2decl
def create_cal_seqs(qubits: qbit_list, numRepeats, measChans: qbit_list = None, waitcmp=False):
    """
    Helper function to create a set of calibration sequences.

    Parameters
    ----------
    qubits : logical channels, e.g. (q1,) or (q1,q2) (tuple) 
    numRepeats = number of times to repeat calibration sequences (int)
    waitcmp = True if the sequence contains branching
    """
    raise Exception("Not implemented")

