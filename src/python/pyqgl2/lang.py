# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved.

class QGL2(object):

    # names of decorators, classes, and functions that
    # determine how the QGL preprocessor transforms code.
    #
    # These MUST agree with the names used in the base QGL2
    # import (currently qgl2.qgl2)
    #
    QCONCUR = 'concur'
    QMAIN = 'qgl2main'
    QDECL = 'qgl2decl'
    QIMPORT = 'qgl2import'

    QMODULE = 'qgl2'

