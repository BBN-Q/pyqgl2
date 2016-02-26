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
# Note: the "realpath" makes this work even if the script is named
# by a symlink instead of its true location.
#
DIRNAME = os.path.normpath(
        os.path.realpath(
            os.path.abspath(os.path.dirname(sys.argv[0]) or '.')))
sys.path.append(os.path.normpath(os.path.join(DIRNAME, '..')))

import pyqgl2.ast_util
import pyqgl2.inline

from pyqgl2.ast_util import NodeError
from pyqgl2.check_qbit import CheckType
from pyqgl2.check_qbit import CompileQGLFunctions
from pyqgl2.check_qbit import FindTypes
from pyqgl2.check_symtab import CheckSymtab
from pyqgl2.check_waveforms import CheckWaveforms
from pyqgl2.concur_unroll import Unroller
from pyqgl2.concur_unroll import QbitGrouper
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
        NodeError.fatal_msg(None, 'no qglmain function found')

    NodeError.halt_on_error()

    ptree = importer.qglmain

    print('-- -- -- -- --')
    ast_text_orig = pyqgl2.ast_util.ast2str(ptree)
    print('ORIGINAL CODE:\n%s' % ast_text_orig)

    ptree1 = ptree

    # We may need to iterate over the inline/unroll processes
    # a few times, because inlining may expose new things to unroll,
    # and vice versa.
    #
    # TODO: as a stopgap, we're going to limit iterations to 20, which
    # is enough to handle fairly deeply-nested, complex non-recursive
    # programs.  What we do is iterate until we converge (the outcome
    # stops changing) or we hit this limit.  We should attempt at this
    # point attempt prove that the expansion is divergent, but we don't
    # do this, but instead assume the worst if the program is complex
    # enough to look like it's "probably" divergent.
    #
    MAX_ITERS = 20
    for iteration in range(MAX_ITERS):

        inliner = Inliner(importer)
        ptree1 = inliner.inline_function(ptree1)
        NodeError.halt_on_error()

        print('INLINED CODE (iteration %d):\n%s' %
                (iteration, pyqgl2.ast_util.ast2str(ptree1)))

        unroller = Unroller()
        ptree1 = unroller.visit(ptree1)
        NodeError.halt_on_error()

        print('UNROLLED CODE (iteration %d):\n%s' %
                (iteration, pyqgl2.ast_util.ast2str(ptree1)))

        if (inliner.change_cnt == 0) and (unroller.change_cnt == 0):
            NodeError.diag_msg(None,
                    ('expansion converged after iteration %d' % iteration))
            break

    if iteration == (MAX_ITERS - 1):
        NodeError.error_msg(None,
                ('expansion did not converge after %d iterations' % MAX_ITERS))

    base_namespace = importer.path2namespace[opts.filename]
    text = base_namespace.pretty_print()
    print('EXPANDED NAMESPACE:\n%s' % text)

    new_ptree1 = ptree1

    type_check = CheckType(opts.filename, importer=importer)
    new_ptree2 = type_check.visit(new_ptree1)
    NodeError.halt_on_error()
    print('CHECKED CODE:\n%s' % pyqgl2.ast_util.ast2str(new_ptree2))

    sym_check = CheckSymtab(opts.filename, type_check.func_defs, importer)
    new_ptree3 = sym_check.visit(new_ptree2)
    NodeError.halt_on_error()
    print('SYMTAB CODE:\n%s' % pyqgl2.ast_util.ast2str(new_ptree3))

    new_ptree5 = specialize(new_ptree3, list(), type_check.func_defs, importer)
    NodeError.halt_on_error()
    print('SPECIALIZED CODE:\n%s' % pyqgl2.ast_util.ast2str(new_ptree5))

    grouper = QbitGrouper()
    new_ptree6 = grouper.visit(new_ptree5)
    NodeError.halt_on_error()
    print('GROUPED CODE:\n%s' % pyqgl2.ast_util.ast2str(new_ptree6))

    print('Final qglmain: %s' % new_ptree6.name)

    base_namespace = importer.path2namespace[opts.filename]
    text = base_namespace.pretty_print()
    print('FINAL CODE:\n-- -- -- -- --\n%s\n-- -- -- -- --' % text)

    """
    wav_check = CheckWaveforms(type_check.func_defs, importer)
    new_ptree8 = wav_check.visit(new_ptree7)
    NodeError.halt_on_error()
    """

    """
    stmnt_list = base_namespace.namespace2ast().body
    for stmnt in stmnt_list:
        concur_checker = CompileQGLFunctions()
        concur_checker.visit(stmnt)
    """

    """
    find_types = FindTypes(importer)
    find_types.visit(new_ptree6)
    print('PARAMS %s ' % find_types.parameter_names)
    print('LOCALS %s ' % find_types.local_names)
    """


if __name__ == '__main__':
    main()
