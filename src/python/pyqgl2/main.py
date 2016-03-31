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
import re
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
import pyqgl2.single

from pyqgl2.ast_util import NodeError
from pyqgl2.check_qbit import CheckType
from pyqgl2.check_qbit import CompileQGLFunctions
from pyqgl2.check_qbit import FindTypes
from pyqgl2.check_symtab import CheckSymtab
from pyqgl2.check_waveforms import CheckWaveforms
from pyqgl2.concur_unroll import Unroller
from pyqgl2.concur_unroll import QbitGrouper
from pyqgl2.flatten import Flattener
from pyqgl2.importer import NameSpaces
from pyqgl2.inline import Inliner
from pyqgl2.sequence import SequenceCreator
from pyqgl2.single import SingleSequence
from pyqgl2.substitute import specialize
from pyqgl2.sync import SynchronizeBlocks

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
    parser.add_argument('-show', dest='showplot', default=False, action='store_true',
                        help="show the waveform plots")
    parser.add_argument('-p', type=str, dest="prefix", metavar='PREFIX',
                        default="test/test",
                        help="Compiled file prefix")
    parser.add_argument('-s', type=str, dest="suffix", metavar='SUFFIX',
                        default="",
                        help="Compiled filename suffix")
    parser.add_argument('-o', dest='saveOutput', default=False, action='store_true',
                        help='Save compiled function to output file')

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


def main(filename, main_name=None, saveOutput=False):

    # Process imports in the input file, and find the main.
    # If there's no main, then bail out right away.

    importer = NameSpaces(filename, main_name)
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

        type_check = CheckType(filename, importer=importer)
        ptree1 = type_check.visit(ptree1)
        NodeError.halt_on_error()
        print('CHECKED CODE (iteration %d):\n%s' %
                (iteration, pyqgl2.ast_util.ast2str(ptree1)))

        ptree1 = specialize(ptree1, list(), type_check.func_defs, importer,
                context=ptree1)
        NodeError.halt_on_error()
        print('SPECIALIZED CODE (iteration %d):\n%s' %
                (iteration, pyqgl2.ast_util.ast2str(ptree1)))

        if (inliner.change_cnt == 0) and (unroller.change_cnt == 0):
            NodeError.diag_msg(None,
                    ('expansion converged after iteration %d' % iteration))
            break

    if iteration == (MAX_ITERS - 1):
        NodeError.error_msg(None,
                ('expansion did not converge after %d iterations' % MAX_ITERS))

    base_namespace = importer.path2namespace[filename]
    text = base_namespace.pretty_print()
    print('EXPANDED NAMESPACE:\n%s' % text)

    new_ptree1 = ptree1

    sym_check = CheckSymtab(filename, type_check.func_defs, importer)
    new_ptree5 = sym_check.visit(new_ptree1)
    NodeError.halt_on_error()
    print('SYMTAB CODE:\n%s' % pyqgl2.ast_util.ast2str(new_ptree5))

    grouper = QbitGrouper()
    new_ptree6 = grouper.visit(new_ptree5)
    NodeError.halt_on_error()
    print('GROUPED CODE:\n%s' % pyqgl2.ast_util.ast2str(new_ptree6))

    flattener = Flattener()
    new_ptree7 = flattener.visit(new_ptree6)
    NodeError.halt_on_error()
    print('FLATTENED CODE:\n%s' % pyqgl2.ast_util.ast2str(new_ptree7))

    sequencer = SequenceCreator()
    sequencer.visit(new_ptree7)
    print('FINAL SEQUENCES:')
    for qbit in sequencer.qbit2sequence:
        print('%s:' % qbit)
        for inst in sequencer.qbit2sequence[qbit]:
            if inst.startswith('BlockLabel'):
                txt = re.sub('BlockLabel\(\'', '', inst)
                txt = re.sub('\'.', ':', txt)
                print('    %s' % txt)
            else:
                print('         %s' % inst)

    print('Final qglmain: %s' % new_ptree7.name)

    base_namespace = importer.path2namespace[filename]
    text = base_namespace.pretty_print()
    print('FINAL CODE:\n-- -- -- -- --\n%s\n-- -- -- -- --' % text)

    sync = SynchronizeBlocks(new_ptree7)
    new_ptree8 = sync.visit(deepcopy(new_ptree7))
    print('SYNCED SEQUENCES:\n%s' % pyqgl2.ast_util.ast2str(new_ptree8))


    # singseq = SingleSequence()
    # singseq.find_sequence(new_ptree8)
    # singseq.emit_function()

    # Try to guess the proper function name
    fname = main_name
    if not fname:
        import ast
        if isinstance(ptree, ast.FunctionDef):
            fname = ptree.name
        else:
            fname = "qgl1Main"

    builder = pyqgl2.single.SingleSequence()
    if builder.find_sequence(new_ptree8):
        if saveOutput:
            code = builder.emit_function(fname)
            newf = os.path.abspath(filename[:-3] + "qgl1.py")
            with open(newf, 'w') as compiledFile:
                compiledFile.write(code)
            print("Saved compiled code to %s" % newf)
        # HACK
        # Assume we have a function creating a single qubit sequence
        # Find it and return it
        qgl1_main = pyqgl2.single.single_sequence(new_ptree8, fname)
        return qgl1_main
    else:
        print("Not a single qubit sequence producing function")
        return None

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

######
# Code below here is for testing
# It creates channels that are taken from test_Sequences APS2Helper
# Run the main with
# main.py <path to file with a qgl2decl to compile that creates
#              sequences you want to compile and plot>
#        -m <name of qgl2main if not decorated>
#        [-o if you want the compiled qgl1 function saved to a file]

# Store the given channels in the QGL ChannelLibrary
def finalize_map(mapping, channels):
    from QGL import ChannelLibrary
    for name,value in mapping.items():
        channels[name].physChan = channels[value]

        ChannelLibrary.channelLib = ChannelLibrary.ChannelLibrary()
        ChannelLibrary.channelLib.channelDict = channels
        ChannelLibrary.channelLib.build_connectivity_graph()

# Create a basic channel library
# Code stolen from QGL's test_Sequences
def chanSetup(channels=dict()):
    from QGL.Channels import LogicalMarkerChannel, Measurement, Qubit, PhysicalQuadratureChannel, PhysicalMarkerChannel, Edge
    from math import pi
    qubit_names = ['q1','q2']
    logical_names = ['digitizerTrig', 'slaveTrig']

    for name in logical_names:
        channels[name] = LogicalMarkerChannel(label=name)

    for name in qubit_names:
        mName = 'M-' + name
        mgName = 'M-' + name + '-gate'
        qgName = name + '-gate'

        mg = LogicalMarkerChannel(label=mgName)
        qg = LogicalMarkerChannel(label=qgName)

        m = Measurement(label=mName, gateChan = mg, trigChan=channels['digitizerTrig'])

        q = Qubit(label=name, gateChan=qg)
        q.pulseParams['length'] = 30e-9
        q.pulseParams['phase'] = pi/2

        channels[name] = q
        channels[mName] = m
        channels[mgName]  = mg
        channels[qgName]  = qg

    # this block depends on the existence of q1 and q2
    channels['cr-gate'] = LogicalMarkerChannel(label='cr-gate')

    q1, q2 = channels['q1'], channels['q2']
    cr = Edge(label="cr", source = q1, target = q2, gateChan = channels['cr-gate'] )
    cr.pulseParams['length'] = 30e-9
    cr.pulseParams['phase'] = pi/4
    channels["cr"] = cr

    mq1q2g = LogicalMarkerChannel(label='M-q1q2-gate')
    channels['M-q1q2-gate']  = mq1q2g
    channels['M-q1q2']       = Measurement(label='M-q1q2', gateChan = mq1q2g, trigChan=channels['digitizerTrig'])

    # Now assign physical channels
    for name in ['APS1', 'APS2', 'APS3', 'APS4', 'APS5', 'APS6']:
        channelName = name + '-12'
        channel = PhysicalQuadratureChannel(label=channelName)
        channel.samplingRate = 1.2e9
        channel.AWG = name
        channel.translator = 'APS2Pattern'
        channels[channelName] = channel

        for m in range(1,5):
            channelName = "{0}-12m{1}".format(name,m)
            channel = PhysicalMarkerChannel(label=channelName)
            channel.samplingRate = 1.2e9
            channel.AWG = name
            channel.translator = 'APS2Pattern'
            channels[channelName] = channel

    mapping = {	'digitizerTrig' : 'APS1-12m1',
                'slaveTrig'     : 'APS1-12m2',
                'q1'            : 'APS1-12',
                'q1-gate'       : 'APS1-12m3',
                'M-q1'          : 'APS2-12',
                'M-q1-gate'     : 'APS2-12m1',
                'q2'            : 'APS3-12',
                'q2-gate'       : 'APS3-12m1',
                'M-q2'          : 'APS4-12',
                'M-q2-gate'     : 'APS4-12m1',
                'cr'            : 'APS5-12',
                'cr-gate'       : 'APS5-12m1',
                'M-q1q2'        : 'APS6-12',
                'M-q1q2-gate'   : 'APS6-12m1'}

    finalize_map(mapping, channels)
    return channels

if __name__ == '__main__':
    opts = parse_args(sys.argv[1:])
    resFunction = main(opts.filename, opts.main_name, opts.saveOutput)
    if resFunction:
        # Now import the QGL1 things we need 
        from QGL.Compiler import compile_to_hardware
        from QGL.PulseSequencePlotter import plot_pulse_files
        import QGL
        import os

        # Hack. Create a basic channel library
        channels = chanSetup()

        # Create a directory for saving the results
        QGL.config.AWGDir = os.path.abspath(QGL.config.AWGDir + os.path.sep + "qgl2main")
        if not os.path.isdir(QGL.config.AWGDir):
            os.makedirs(QGL.config.AWGDir)

        # Now execute the returned function, which should produce a list of sequences
        sequences = resFunction(q=channels['q1'])

        # Now we have a QGL1 list of sequences we can act on
        fileNames = compile_to_hardware(sequences, opts.prefix, opts.suffix)
        print(fileNames)
        if opts.showplot:
            plot_pulse_files(fileNames)
    else:
        # Didn't produce a function
        pass
