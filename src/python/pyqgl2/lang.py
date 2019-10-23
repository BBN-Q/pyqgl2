# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved.

class QGL2(object):

    # names of decorators, classes, and functions that
    # determine how the QGL preprocessor transforms code.
    #
    # These MUST agree with the names used in the base QGL2
    # import (currently qgl2.qgl2)
    #
    QINFUNC = 'infunc'
    QMAIN = 'qgl2main'
    QDECL = 'qgl2decl'
    # A stub for a QGL1 function: It's QGL2 but don't inline it
    QSTUB = 'qgl2stub'
    QMEAS = 'qgl2meas'

    QMODULE = 'qgl2'

    QBIT_ALLOC = 'QRegister'
    QVAL_ALLOC = 'QValue'

    CLASSICAL = 'classical'
    PULSE = 'pulse'
    # A QRegister (containing 1+ qubits)
    QBIT = 'qreg'
    # DO NOT USE
    #    QBIT_LIST = 'qreg_list'
    # like a Wait
    CONTROL = 'control'
    # A sequence of pulses
    SEQUENCE = 'sequence'

    REPEAT = 'Qrepeat'
    FOR = 'Qfor'
    ITER = 'Qiter'

    CHECK_FUNC = 'QGL2check'
    CHECK_FUNC_VEC_ATTR = 'qgl2_check_vector'
