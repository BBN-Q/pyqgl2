#!/usr/bin/env python3
#
# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved.
#

"""
Test driver for the pyqgl2 program

Located in the source directory for the sake of simplicity
during prototyping/debugging.  The real driver is in scripts/qgl2prep
(although it may be renamed).
"""

import logging
import os
import sys

from optparse import OptionParser

# Add the necessary module paths: find the directory that this
# executable lives in, and then add paths from there to the
# pyqgl2 modules
#
# This path is relative and must be be modified if this script
# is moved
#
DIRNAME = os.path.normpath(
        os.path.abspath(os.path.dirname(sys.argv[0]) or '.'))
sys.path.append(os.path.normpath(os.path.join(DIRNAME, '..')))

from pyqgl2.importer import NameSpaces

def parse_args(argv):
    """
    Parse the parameters from the argv
    """

    parser = OptionParser()

    parser.add_option('-l', '--log-level',
            dest='log_level',
            default=logging.WARNING, type=int,
            help='Run with the given logging level [default=%default]')

    parser.add_option('-m', '--main-name',
            dest='main_name',
            default='', type=str,
            metavar='FUNCNAME',
            help='Specify a different QGL main function than the default')

    parser.add_option('-v', '--verbose',
            dest='verbose',
            default=False, action="store_true",
            help='Run in verbose mode')


    (options, fnames) = parser.parse_args(argv)

    if len(fnames) != 2:
        print('Error: a single input file is required')
        sys.exit(1)

    return options, fnames[1]

def stdout_logger(logprefix, level):
    """
    Set up a logger.

    This is just boilerplate right now, because this app generally
    sends status and error to stdout, not a log
    """

    logger = logging.getLogger(logprefix)
    logger.setLevel(level)

    formatter = logging.Formatter(
            '%(asctime)s %(name)s %(module)s:%(lineno)d %(funcName)s ' +
            '%(levelname)s: %(message)s')

    handler = logging.StreamHandler(stream=sys.stdout)

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

def main():
    (opts, input_fname) = parse_args(sys.argv)

    # do something with the opts

    # We're NOT using the logger right now, so don't even bother
    # to create it, because it will litter this directory with
    # empty log files.
    #
    # logger = stdout_logger('qgl2prep', opts.log_level)

    # Process imports in the input file, and find the main.
    # If there's no main, then bail out right away.

    importer = NameSpaces(input_fname, opts.main_name)
    if not importer.qglmain:
        print('error: no function declared as qglmain')
        sys.exit(1)

    ptree = importer.path2ast[importer.base_fname]

if __name__ == '__main__':
    main()
