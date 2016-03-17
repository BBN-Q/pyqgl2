# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved.

class QGL2(object):

    # names of decorators, classes, and functions that
    # determine how the QGL preprocessor transforms code.
    #
    # These MUST agree with the names used in the base QGL2
    # import (currently qgl2.qgl2)
    #
    QCONCUR = 'concur'
    QSEQ = 'seq'
    QMAIN = 'qgl2main'
    QDECL = 'qgl2decl'
    # A stub for a QGL1 function: It's QGL2 but don't inline it
    QSTUB = 'qgl2stub'

    QMODULE = 'qgl2'

    QBIT_ALLOC = 'Qbit'

    CLASSICAL = 'classical'
    PULSE = 'pulse'
    QBIT = 'qbit'
    QBIT_LIST = 'qbit_list'
    # like a Wait
    CONTROL = 'control'
    # A sequence of pulses
    SEQUENCE = 'sequence'
