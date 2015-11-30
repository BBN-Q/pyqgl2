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

import os
import sys

from argparse import ArgumentParser

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

    parser = ArgumentParser(description='Prototype QGL2 driver')

    parser.add_argument(
            '-m', dest='main_name', default='', type=str, nargs=1,
            metavar='FUNCNAME',
            help='Specify a different QGL main function than the default')

    parser.add_argument(
            '-v', dest='verbose', default=False, action='store_true',
            help='Run in verbose mode')

    (options, fnames) = parser.parse_args(argv)

    if len(fnames) != 2:
        print('Error: a single input file is required')
        sys.exit(1)

    return options, fnames[1]


def main():
    (opts, input_fname) = parse_args(sys.argv)

    # Process imports in the input file, and find the main.
    # If there's no main, then bail out right away.

    importer = NameSpaces(input_fname, opts.main_name)
    if not importer.qglmain:
        print('error: no function declared as qglmain')
        sys.exit(1)

    ptree = importer.path2ast[importer.base_fname]

if __name__ == '__main__':
    main()
