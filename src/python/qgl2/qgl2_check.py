# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import sys

from pyqgl2.inline import QubitPlaceholder

def QGL2check(value, required_type, fp_name, fname, lineno, colno):

    if required_type == 'qbit':
        if not isinstance(value, QubitPlaceholder):
            print('%s:%d:%d: error: bad type: [%s] must be a qbit' %
                    (fname, lineno, colno, fp_name))
            sys.exit(1)

    elif required_type == 'classical':
        if isinstance(value, QubitPlaceholder):
            print('%s:%d:%d: error: bad type: [%s] must be classical' %
                    (fname, lineno, colno, fp_name))
            sys.exit(1)

    return True
