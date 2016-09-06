# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import sys

from pyqgl2.inline import QubitPlaceholder
from pyqgl2.ast_util import NodeError

def QGL2check(value, required_type, fp_name, fun_name, fname, lineno, colno):

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
