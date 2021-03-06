# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from pyqgl2.ast_util import NodeError
from pyqgl2.qreg import QRegister, QReference

def QGL2check(value, required_type, fp_name, fun_name, fname, lineno, colno):
    """
    Runtime check of an actual parameter

    Check that the given value is of the required type, and
    if it is not then print out an error message mentioning the
    name of the formal parameter to which that value was intended
    to be assigned, the name of the function being called, and the
    file name, line number, and column number of the call in the
    source code.
    """

    # TODO: should be able to tolerate actual Qubit values,
    # not just references to QRegister instances

    assert isinstance(required_type, str), 'required_type must be a str'
    assert isinstance(fp_name, str), 'fp_name must be a str'
    assert isinstance(fun_name, str), 'fun_name must be a str'
    assert isinstance(fname, str), 'fname must be a str'
    assert isinstance(lineno, int), 'lineno must be an int'
    assert isinstance(colno, int), 'colno must be a int'

    if required_type == 'qbit':
        # TODO add a check that QReference indices are within bounds
        if not isinstance(value, (QRegister, QReference)):
            print(('%s:%d:%d: error: ' +
                'param [%s] of func [%s] must be qbit') %
                    (fname, lineno, colno, fp_name, fun_name))
            NodeError.MAX_ERR_LEVEL = NodeError.NODE_ERROR_ERROR
            return False

    elif required_type == 'qbit_list':
        if ((not isinstance(value, list)) and
                (not isinstance(value, set)) and
                (not isinstance(value, tuple))):
            print(('%s:%d:%d: error: ' +
                'param [%s] of func [%s] must be qbit_list') %
                    (fname, lineno, colno, fp_name, fun_name))
            NodeError.MAX_ERR_LEVEL = NodeError.NODE_ERROR_ERROR
            return False

        for element in value:
            # this might be too persnickety, but right now
            # we must have a QRegister because we will
            # require the use_name() method be present.
            #
            if not isinstance(element, QRegister):
                print(('%s:%d:%d: error: ' +
                    'each elem of param [%s] of func [%s] must be a qbit') %
                        (fname, lineno, colno, fp_name, fun_name))
                NodeError.MAX_ERR_LEVEL = NodeError.NODE_ERROR_ERROR
                return False

    elif required_type == 'classical':
        if isinstance(value, QRegister):
            print(('%s:%d:%d: error: ' +
                'param [%s] of func [%s] must be classical') %
                    (fname, lineno, colno, fp_name, fun_name))
            NodeError.MAX_ERR_LEVEL = NodeError.NODE_ERROR_ERROR
            return False

    return True
