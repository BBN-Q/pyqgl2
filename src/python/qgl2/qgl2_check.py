# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import sys

from pyqgl2.inline import QubitPlaceholder
from pyqgl2.ast_util import NodeError

def QGL2check(value, required_type, fp_name, fun_name, fname, lineno, colno):

    assert isinstance(required_type, str), 'required_type must be a str'
    assert isinstance(fp_name, str), 'fp_name must be a str'
    assert isinstance(fun_name, str), 'fun_name must be a str'
    assert isinstance(fname, str), 'fname must be a str'
    assert isinstance(lineno, int), 'lineno must be an int'
    assert isinstance(colno, int), 'colno must be a int'

    if required_type == 'qbit':
        if not isinstance(value, QubitPlaceholder):
            print(('%s:%d:%d: error: ' +
                'param [%s] of func [%s] must be qbit') %
                    (fname, lineno, colno, fp_name, fun_name))
            NodeError.MAX_ERR_LEVEL = NodeError.NODE_ERROR_ERROR

    elif required_type == 'classical':
        if isinstance(value, QubitPlaceholder):
            print(('%s:%d:%d: error: ' +
                'param [%s] of func [%s] must be classical') %
                    (fname, lineno, colno, fp_name, fun_name))
            NodeError.MAX_ERR_LEVEL = NodeError.NODE_ERROR_ERROR

    return True

def QGL2check_vec(checks):
    """
    Combine multiple checks (from a vector of checks) so all the
    checks are performed, even if one or more of them fail.
    This is useful because typically when a programmer makes
    one type mistake, they make several, so we might as well try
    to tell them about as many as possible instead of exiting
    after detecting the first error.

    Each check is a tuple that will be used as the positional
    parameters to QGL2check.  QGL2check makes an attempt to
    validate its parameters and aborts the program if it detects
    problems.
    """

    for check in checks:
        QGL2check(*check)

    return True
