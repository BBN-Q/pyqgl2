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
from copy import deepcopy

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

import pyqgl2.ast_util
import pyqgl2.inline

from pyqgl2.ast_util import NodeError
from pyqgl2.check_qbit import CheckType
from pyqgl2.check_qbit import CompileQGLFunctions
from pyqgl2.check_qbit import FindTypes
from pyqgl2.check_symtab import CheckSymtab
from pyqgl2.check_waveforms import CheckWaveforms
from pyqgl2.importer import NameSpaces
from pyqgl2.inline import Inliner
from pyqgl2.substitute import specialize


def parse_args(argv):
    """
    Parse the parameters from the argv
    """

    parser = ArgumentParser(description='Prototype QGL2 driver')

    parser.add_argument(
            '-m', dest='main_name', default='', type=str, metavar='FUNCNAME',
            help='Specify a different QGL main function than the default')

    parser.add_argument(
            '-v', dest='verbose', default=False, action='store_true',
            help='Run in verbose mode')

    parser.add_argument('filename', type=str, metavar='FILENAME',
            help='input filename')

    options = parser.parse_args(argv)

    # for the sake of consistency and brevity, convert the path
    # to a relative path, so that the diagnostic messages match
    # the internal representation

    options.filename = os.path.relpath(options.filename)

    # If the file we're sourcing is not in the current
    # directory, add its directory to the search path
    #
    source_dir = os.path.dirname(options.filename)
    if not source_dir:
        sys.path.append(os.path.normpath(source_dir))

    return options


def main():
    opts = parse_args(sys.argv[1:])

    # Process imports in the input file, and find the main.
    # If there's no main, then bail out right away.

    importer = NameSpaces(opts.filename, opts.main_name)
    if not importer.qglmain:
        NodeError.fatal_msg('no qglmain function found')

    NodeError.halt_on_error()

    ptree = importer.qglmain

    print('-- -- -- -- --')
    ast_text_orig = pyqgl2.ast_util.ast2str(ptree)
    print('ORIGINAL CODE:\n%s' % ast_text_orig)

    inliner = Inliner(importer)
    new_ptree = inliner.inline_function(ptree)
    NodeError.halt_on_error()

    print('MODIFIED CODE:\n%s' % pyqgl2.ast_util.ast2str(new_ptree))

    print('-- -- -- -- --')
    print('INLINED CODE:\n%s' % pyqgl2.ast_util.ast2str(new_ptree))
    print('-- -- -- -- --')

    # make sure that we didn't clobber anything while we did
    # the processing (this is an incomplete test--it doesn't
    # check anything except the qglmain)
    #
    ast_text_orig2 = pyqgl2.ast_util.ast2str(ptree)
    if ast_text_orig != ast_text_orig2:
        print('error: the original definition was clobbered')

    base_namespace = importer.path2namespace[opts.filename]
    text = base_namespace.pretty_print()
    print(text)

    type_check = CheckType(opts.filename, importer=importer)
    new_ptree2 = type_check.visit(new_ptree)

    NodeError.halt_on_error()

    print('CHECKED CODE:\n%s' % pyqgl2.ast_util.ast2str(new_ptree2))

    sym_check = CheckSymtab(opts.filename, type_check.func_defs, importer)
    new_ptree3 = sym_check.visit(new_ptree2)

    NodeError.halt_on_error()

    print('SYMTAB CODE:\n%s' % pyqgl2.ast_util.ast2str(new_ptree3))

    new_ptree4 = specialize(new_ptree3, list(), type_check.func_defs, importer)

    NodeError.halt_on_error()

    print('Final qglmain: %s' % new_ptree4.name)
    print('Final CODE:\n-- -- -- -- --')

    base_namespace = importer.path2namespace[opts.filename]
    text = base_namespace.pretty_print()
    print(text)
    print('-- -- -- -- --')

    type_check = CheckType(opts.filename, importer=importer)
    new_ptree5 = type_check.visit(new_ptree4)

    NodeError.halt_on_error()

    wav_check = CheckWaveforms(type_check.func_defs, importer)
    new_ptree6 = wav_check.visit(new_ptree5)

    NodeError.halt_on_error()

    """
    stmnt_list = base_namespace.namespace2ast().body
    for stmnt in stmnt_list:
        concur_checker = CompileQGLFunctions()
        concur_checker.visit(stmnt)
    """

    find_types = FindTypes(importer)
    find_types.visit(new_ptree6)
    print('PARAMS %s ' % find_types.parameter_names)
    print('LOCALS %s ' % find_types.local_names)


if __name__ == '__main__':
    main()
