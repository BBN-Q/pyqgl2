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

import ast
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

from pyqgl2.ast_util import NodeError
from pyqgl2.check_qbit import CheckType
from pyqgl2.check_qbit import CompileQGLFunctions
from pyqgl2.check_qbit import FindTypes
from pyqgl2.check_symtab import CheckSymtab
from pyqgl2.check_waveforms import CheckWaveforms
from pyqgl2.concur_unroll import Unroller
from pyqgl2.concur_unroll import QbitGrouper
from pyqgl2.debugmsg import DebugMsg
from pyqgl2.eval import EvalTransformer, SimpleEvaluator
from pyqgl2.flatten import Flattener
from pyqgl2.grouper import AddBarriers
from pyqgl2.grouper import AddSequential
from pyqgl2.grouper import MarkReferencedQbits
from pyqgl2.grouper import QbitGrouper2
from pyqgl2.importer import NameSpaces, add_import_from_as
from pyqgl2.inline import Inliner
from pyqgl2.repeat import RepeatTransformer
from pyqgl2.sequence import SequenceCreator
from pyqgl2.sequences import SequenceExtractor, get_sequence_function
from pyqgl2.substitute import specialize
from pyqgl2.sync import SynchronizeBlocks


def parse_args(argv):
    """
    Parse the parameters from the argv
    """

    parser = ArgumentParser(description='Prototype QGL2 driver')

    # NOTE: filename is a positional parameter!
    parser.add_argument('filename',
            type=str, metavar='INPUT-FILENAME',
            default='',
            help='input filename')

    parser.add_argument('-D', '--debug-level',
            dest='debug_level', type=int, metavar='LEVEL',
            default=DebugMsg.NONE,
            help=('Specify the debugging level (0=all, 4=none)' +
                    '[default=%(default)d)]'))

    parser.add_argument('-m',
            dest='main_name', type=str, metavar='FUNCNAME',
            default='',
            help='Specify a different QGL main function than the default')

    parser.add_argument('-o',
            dest='saveOutput',
            default=False, action='store_true',
            help='Save compiled function to output file')

    parser.add_argument('-p',
            type=str, dest="prefix", metavar='PATH-PREFIX',
            default="test/test",
            help="Compiled file prefix [default=%(default)s]")

    parser.add_argument('-s',
            type=str, dest="suffix", metavar='FILENAME-SUFFIX',
            default="",
            help="Compiled filename suffix")

    parser.add_argument('-S', '--save-intermediate',
            type=str, dest='intermediate_output', metavar='SAVE-FILENAME',
            default='',
            help='Save intermediate output to the given file')

    parser.add_argument('-show',
            dest='showplot', default=False, action='store_true',
            help="show the waveform plots")

    parser.add_argument('-v', dest='verbose',
            default=False, action='store_true',
            help='Run in verbose mode')

    options = parser.parse_args(argv)

    # for the sake of consistency and brevity, convert the path
    # to a relative path, so that the diagnostic messages match
    # the internal representation

    options.filename = os.path.relpath(options.filename)

    # If the file we're sourcing is not in the current
    # directory, add its directory to the search path
    #
    source_dir = os.path.dirname(options.filename)
    if source_dir:
        sys.path.append(os.path.normpath(source_dir))

    if options.verbose:
        NodeError.MUTE_ERR_LEVEL = NodeError.NODE_ERROR_NONE

    DebugMsg.set_level(options.debug_level)

    return options


def compileFunction(filename, main_name=None, saveOutput=False,
                    intermediate_output=None):

    # Always open up a file for the intermediate output,
    # even if it's just /dev/null, so we don't have to
    # muddy up the code with endless checks for whether
    # we're supposed to save the intermediate output
    #
    if not intermediate_output:
        intermediate_output = '/dev/null'

    if intermediate_output:
        try:
            intermediate_fout = open(intermediate_output, 'w')
        except BaseException as exc:
            NodeError.fatal_msg(None,
                    ('cannot save intermediate output in [%s]' %
                        intermediate_output))

    # Process imports in the input file, and find the main.
    # If there's no main, then bail out right away.

    # The 'filename' could really be the source for the function
    code = None
    # Detect that ths is code, not a filename
    # FIXME: Is there a better way to do this?
    if ("qgl2decl" in filename or "qgl2main" in filename) and "def " in filename:
        NodeError.diag_msg(None, "Treating filename as code")
        code = filename
        filename = sys.argv[0] # Could use <stdin> instead
    else:
        try:
            relPath = os.path.relpath(filename)
        except Exception as e:
            # If that wasn't a good path, treat it as code
            NodeError.diag_msg(None, "Failed to make relpath from %s: %s" % (filename, e))
            code = filename
            filename = sys.argv[0] # Could use <stdin> instead
#            filename = "<stdin>"

    importer = NameSpaces(filename, main_name, code)
    if not importer.qglmain:
        NodeError.fatal_msg(None, 'no qglmain function found')

    NodeError.halt_on_error()

    ptree = importer.qglmain

    ast_text_orig = pyqgl2.ast_util.ast2str(ptree)
    print(('ORIGINAL CODE:\n%s' % ast_text_orig),
            file=intermediate_fout, flush=True)

    # if Wait() and Sync() aren't accessible from the namespace
    # used by the qglmain, then things are going to fail later;
    # might as well fail quickly
    #
    # TODO: this is a hack, but the approach of adding these
    # blindly to the namespace is also a hack.  This is a
    # placeholder until we figure out a cleaner approach.
    #
    # if not importer.resolve_sym(ptree.qgl_fname, 'Sync'):

    modname = ptree.qgl_fname
    if not (add_import_from_as(importer, modname, 'qgl2.qgl1', 'Wait') and
            add_import_from_as(importer, modname, 'qgl2.qgl1', 'Sync') and
            add_import_from_as(importer, modname, 'qgl2.qgl1', 'Barrier')):
        NodeError.error_msg(ptree,
                'Wait() and/or Sync() and/or Barrier() cannot be found: missing imports?')
        NodeError.halt_on_error()

    ptree1 = ptree

    # We may need to iterate over the inlining and specialization
    # processes a few times, because inlining may expose new things
    # to specialize, and vice versa.
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

        print('ITERATION %d' % iteration)

        inliner = Inliner(importer)
        ptree1 = inliner.inline_function(ptree1)
        NodeError.halt_on_error()

        print(('INLINED CODE (iteration %d):\n%s' %
                (iteration, pyqgl2.ast_util.ast2str(ptree1))),
                file=intermediate_fout, flush=True)

        # unroller = Unroller(importer)
        # ptree1 = unroller.visit(ptree1)
        # NodeError.halt_on_error()

        # print(('UNROLLED CODE (iteration %d):\n%s' %
        #         (iteration, pyqgl2.ast_util.ast2str(ptree1))),
        #         file=intermediate_fout, flush=True)

        type_check = CheckType(filename, importer=importer)
        ptree1 = type_check.visit(ptree1)
        NodeError.halt_on_error()
        print(('CHECKED CODE (iteration %d):\n%s' %
                (iteration, pyqgl2.ast_util.ast2str(ptree1))),
                file=intermediate_fout, flush=True)

        # ptree1 = specialize(ptree1, list(), type_check.func_defs, importer,
        #         context=ptree1)
        # NodeError.halt_on_error()
        # print(('SPECIALIZED CODE (iteration %d):\n%s' %
        #         (iteration, pyqgl2.ast_util.ast2str(ptree1))),
        #         file=intermediate_fout, flush=True)

        # If we include the unroller, or check for changes by the
        # specializer, then we would also check for their changes here.
        # Right now the unroller is not used (unrolling is done
        # within the evaluator)

        if inliner.change_cnt == 0:
            NodeError.diag_msg(None,
                    ('expansion converged after iteration %d' % iteration))
            break

    if iteration == (MAX_ITERS - 1):
        NodeError.error_msg(None,
                ('expansion did not converge after %d iterations' % MAX_ITERS))

    evaluator = EvalTransformer(SimpleEvaluator(importer, None))

    print('CALLING EVALUATOR')
    ptree1 = evaluator.visit(ptree1)
    NodeError.halt_on_error()

    print('EVALUATOR RESULT:\n%s' % pyqgl2.ast_util.ast2str(ptree1))
    # It's very hard to read the intermediate form, before the
    # QBIT names are added, so we don't save this right now.
    # print(('EVALUATOR RESULT:\n%s' % pyqgl2.ast_util.ast2str(ptree1)),
    #         file=intermediate_fout, flush=True)

    # Dump out all the variable bindings, for debugging purposes
    #
    # print('EV total state:')
    # evaluator.print_state()

    evaluator.replace_bindings(ptree1.body)

    print('EVALUATOR REBINDINGS:\n%s' % pyqgl2.ast_util.ast2str(ptree1))
    print(('EVALUATOR + REBINDINGS:\n%s' % pyqgl2.ast_util.ast2str(ptree1)),
            file=intermediate_fout, flush=True)

    # ptree1 = specialize(ptree1, list(), type_check.func_defs, importer,
    #         context=ptree1)
    # NodeError.halt_on_error()
    # print(('SPECIALIZED CODE (iteration %d):\n%s' %
    #         (iteration, pyqgl2.ast_util.ast2str(ptree1))),
    #         file=intermediate_fout, flush=True)

    # If we got raw code, then we may have no source file to use
    if not filename or filename == '<stdin>':
        text = '<stdin>'
    else:
        base_namespace = importer.path2namespace[filename]
        text = base_namespace.pretty_print()

    print(('EXPANDED NAMESPACE:\n%s' % text),
            file=intermediate_fout, flush=True)

    new_ptree1 = ptree1

    # Make sure that functions that take qbits are getting qbits
    sym_check = CheckSymtab(filename, type_check.func_defs, importer)
    new_ptree5 = sym_check.visit(new_ptree1)
    NodeError.halt_on_error()
    print(('SYMTAB CODE:\n%s' % pyqgl2.ast_util.ast2str(new_ptree5)),
            file=intermediate_fout, flush=True)

    # grouper = QbitGrouper(evaluator.eval_state.locals_stack[-1])
    # new_ptree6 = grouper.visit(new_ptree5)
    # NodeError.halt_on_error()
    # print(('GROUPED CODE:\n%s' % pyqgl2.ast_util.ast2str(new_ptree6)),
    #         file=intermediate_fout, flush=True)

    MarkReferencedQbits.marker(new_ptree5,
            local_vars=evaluator.eval_state.locals_stack[-1])

    seq = AddSequential()
    new_ptree5 = seq.visit(new_ptree5)
    NodeError.halt_on_error()
    print(('SEQUENTIAL CODE:\n%s' % pyqgl2.ast_util.ast2str(new_ptree5)),
            file=intermediate_fout, flush=True)

    # barr = AddBarriers()
    # new_ptree5 = barr.visit(new_ptree5)
    # NodeError.halt_on_error()
    # print(('BARRIER CODE:\n%s' % pyqgl2.ast_util.ast2str(new_ptree5)),
    #         file=intermediate_fout, flush=True)

    # Take with-infunc and with-concur blocks and produce with-grouped
    # and with-group blocks
    #
    grouper = QbitGrouper2()
    new_ptree6 = grouper.group(new_ptree5,
            local_vars=evaluator.eval_state.locals_stack[-1])
    NodeError.halt_on_error()
    print(('GROUPED CODE:\n%s' % pyqgl2.ast_util.ast2str(new_ptree6)),
            file=intermediate_fout, flush=True)

    # TODO: move the RepeatTransformer to before the grouper,
    # and make sure that it doesn't find things that include
    # any barriers.  We aren't certain how to handle barriers
    # as part of repeat blocks yet.
    #
    # repeater = RepeatTransformer()
    # new_ptree6 = repeater.visit(new_ptree6)
    # NodeError.halt_on_error()
    # print(('QREPEAT CODE:\n%s' % pyqgl2.ast_util.ast2str(new_ptree6)),
    #         file=intermediate_fout, flush=True)

    # Try to flatten out repeat, range, ifs
    flattener = Flattener()
    new_ptree7 = flattener.visit(new_ptree6)
    NodeError.halt_on_error()
    print(('FLATTENED CODE:\n%s' % pyqgl2.ast_util.ast2str(new_ptree7)),
            file=intermediate_fout, flush=True)

    evaluator.replace_bindings(new_ptree7.body)

    # We're not going to print this, at least not for now,
    # although it's sometimes a useful pretty-printing
    if False:
        sequencer = SequenceCreator()
        sequencer.visit(new_ptree7)
        NodeError.halt_on_error()

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

    print(('Final qglmain: %s' % new_ptree7.name),
            file=intermediate_fout, flush=True)

    # These values are set above
    #base_namespace = importer.path2namespace[filename]
    #text = base_namespace.pretty_print()
    print(('FINAL CODE:\n-- -- -- -- --\n%s\n-- -- -- -- --' % text),
            file=intermediate_fout, flush=True)

    sync = SynchronizeBlocks(new_ptree7)
    new_ptree8 = sync.visit(deepcopy(new_ptree7))
    NodeError.halt_on_error()
    print(('SYNCED SEQUENCES:\n%s' % pyqgl2.ast_util.ast2str(new_ptree8)),
            file=intermediate_fout, flush=True)

    # Done. Time to generate the QGL1

    # Try to guess the proper function name
    fname = main_name
    if not fname:
        if isinstance(ptree, ast.FunctionDef):
            fname = ptree.name
        else:
            fname = "qgl1Main"

    # Get the QGL1 function that produces the proper sequences
    # But if we started with raw code, we may have no filename
    filen = filename
    if not filename or filename == '<stdin>':
        filen = "myprogram.py"
    qgl1_main = get_sequence_function(new_ptree8, fname,
            importer, intermediate_fout, saveOutput, filen,
            setup=evaluator.setup())
    NodeError.halt_on_error()
    return qgl1_main

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

def getAWG(channel):
    '''Given a channel, find its AWG'''
    from QGL.Channels import LogicalChannel, Measurement, Qubit, PhysicalChannel
    import logging
    logger = logging.getLogger('QGL.Compiler.qgl2')
    phys = channel
    awg = None
    if channel is None:
        logger.debug("None channel has no AWG")
        return None
    if hasattr(channel, 'physChan'):
        phys = channel.physChan
        # logger.debug("Channel '%s' has physical channel '%s'", channel, phys)
    elif not isinstance(channel, PhysicalChannel):
        logger.debug("No physChan attribute on channel '%s'", channel)

    # if isinstance(channel, Measurement):
    #     logger.debug("'%s' uses gate: %s, trigger: %s", channel, channel.gateChan, channel.trigChan)
    # if isinstance(channel, Qubit):
    #     logger.debug("'%s' has gate: '%s'", channel, channel.gateChan)
    if hasattr(phys, 'AWG'):
        awg = phys.AWG
        # logger.debug("Physical Channel '%s' had AWG '%s'", phys, awg)
    else:
        logger.error("Config incomplete? Found no AWG for '%s'", channel)

    return awg

def qgl2_compile_to_hardware(seqs, filename, suffix=''):
    '''Custom compile_to_hardware for QGL2 that calls
    c2h once per sequence, specifically asking that the slaveTrigger be added only for the single 
    channel that actually shares an AWG with the slaveTrigger.
    Return is a list of filenames.'''
    from QGL.Compiler import find_unique_channels, compile_to_hardware
    from QGL.Channels import Qubit as qgl1Qubit
    from QGL import ChannelLibrary
    from pyqgl2.evenblocks import replaceBarriers
    import logging
    logger = logging.getLogger('QGL.Compiler.qgl2')

    # Find the channel for each sequence
    seqIdxToChannelMap = dict()
    for idx, seq in enumerate(seqs):
        chs = find_unique_channels(seq)
        for ch in chs:
            # FIXME: Or just exclude Measurement channels?
            if isinstance(ch, qgl1Qubit):
                seqIdxToChannelMap[idx] = ch
                logger.debug("Sequence %d is channel %s", idx, ch)
                logger.debug(" - which is AWG '%s'", getAWG(ch))
                break

    # Hack: skip the empty sequence(s) now before doing anything else
    useseqs = list()
    decr = 0 # How much to decrement the index
    toDecr = dict() # Map of old index to amount to decrement
    for idx, seq in enumerate(seqs):
        if idx not in seqIdxToChannelMap:
            # Indicates an error usually, but could be a channel in the program that doesn nothing
            logger.debug("Sequence %d has no channel - skip", idx)
            decr = decr+1
            continue
        if decr:
            toDecr[idx] = decr
            logger.debug("Will shift index of sequence %d by %d", idx, decr)
        useseqs.append(seq)
    seqs = useseqs
    if decr:
        newmap = dict()
        for ind in seqIdxToChannelMap:
            if ind in toDecr:
                newmap[ind-decr] = seqIdxToChannelMap[ind]
                logger.debug("Sequence %d (channel %s) is now sequence %d", ind, seqIdxToChannelMap[ind], ind-decr)
            elif ind in seqIdxToChannelMap:
                logger.debug("Sequence %d keeping map to %s", ind, seqIdxToChannelMap[ind])
                newmap[ind] = seqIdxToChannelMap[ind]
            else:
                logger.debug("Dropping (empty) sequence %d", ind)
        seqIdxToChannelMap = newmap

    # Try to replace Barrier commands with Id pulses where possible, else with Sync/Wait
    seqs = replaceBarriers(seqs, seqIdxToChannelMap)

    # Find the sequence whose channel's AWG is same as slave Channel, if
    # any. Avoid sequences without a qubit channel if any.
    slaveSeqInd = None
    slaveTrig = None
    slaveAWG = None
    try:
        slaveTrig = ChannelLibrary.channelLib['slaveTrig']
        slaveAWG = getAWG(slaveTrig)
    except KeyError as ke:
        logger.warning("Found no slave trigger configured")

    # Note there will be 1 digitizer per measurement channel, on same AWG
    # as its meas channel

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Slave trig is on AWG '%s'", slaveAWG)
    for idx, seq in enumerate(seqs):
        seqChan = seqIdxToChannelMap.get(idx, None)
        if seqChan and getAWG(seqChan) == slaveAWG:
            slaveSeqInd = idx
            logger.debug("Found slave trigger on sequence %d with channel %s", idx, seqChan)
            break

    # If nothing in the program uses the slave's AWG, pick any channel in use
    if slaveSeqInd is None:
        slaveSeqInd = list(seqIdxToChannelMap.keys())[0]
        logger.debug("Randomly putting slaveTrig on sequence %d", slaveSeqInd)

    # Now we call c2h for each seq
    # Start as a set so filenames are unique,
    # but return as a list so it can be a dictionary key
    files = set()
    for idx, seq in enumerate(seqs):
        doSlave = False
        if idx == slaveSeqInd:
            logger.debug("Asking for slave trigger with sequence %d", idx)
            doSlave = True
        else:
            logger.debug("Asking for sequence %d", idx)

        newfiles = compile_to_hardware([seq], filename, suffix, qgl2=True, addQGL2SlaveTrigger=doSlave)
        if newfiles:
            logger.debug("Produced files: %s", newfiles)
            files = files.union(newfiles)
        else:
            logger.debug("Produced no new files")
    return list(files)

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
    from QGL.ChannelLibrary import QubitFactory, MeasFactory, EdgeFactory
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

        m = MeasFactory(label=mName, gateChan = mg, trigChan=channels['digitizerTrig'])

        q = QubitFactory(label=name, gateChan=qg)
        q.pulseParams['length'] = 30e-9
        q.pulseParams['phase'] = pi/2

        channels[name] = q
        channels[mName] = m
        channels[mgName]  = mg
        channels[qgName]  = qg

    # this block depends on the existence of q1 and q2
    channels['cr-gate'] = LogicalMarkerChannel(label='cr-gate')

    q1, q2 = channels['q1'], channels['q2']
    cr = None
    try:
        cr = EdgeFactory(q1, q2)
    except:
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

    import QGL
    if QGL.ChannelLibrary.channelLib and 'slaveTrig' in QGL.ChannelLibrary.channelLib:
        print("Using ChannelLibrary from config")
    else:
        # Hack. Create a basic channel library
        print("Creating an APS2ish config with 2 Qubits for testing")
        chanSetup()

    resFunction = compileFunction(opts.filename, opts.main_name, opts.saveOutput,
                                  intermediate_output=opts.intermediate_output)
    if resFunction:
        # Now import the QGL1 things we need 
        from QGL.PulseSequencePlotter import plot_pulse_files
        from QGL.ChannelLibrary import QubitFactory
        import os

        # Create a directory for saving the results
        QGL.config.AWGDir = os.path.abspath(QGL.config.AWGDir + os.path.sep + "qgl2main")
        if not os.path.isdir(QGL.config.AWGDir):
            os.makedirs(QGL.config.AWGDir)

        # Now execute the returned function, which should produce a list of sequences
        # Supply a bunch of qbit variables to cover usual cases
        # For other cases, write your own main().
        sequences = resFunction(q=QubitFactory('q1'),qubit=QubitFactory('q1'),q1=QubitFactory('q1'),controlQ=QubitFactory('q1'),q2=QubitFactory('q2'),mqubit=QubitFactory('q2'),targetQ=QubitFactory('q2'))

        # In verbose mode, turn on DEBUG python logging for the QGL Compiler
        if opts.verbose:
            import logging
            from QGL.Compiler import set_log_level
            # Note this acts on QGL.Compiler at DEBUG by default
            # Could specify other levels, loggers
            set_log_level()

        # Now we have a QGL1 list of sequences we can act on
        fileNames = qgl2_compile_to_hardware(sequences, opts.prefix,
                                        opts.suffix)
        print(fileNames)
        if opts.showplot:
            plot_pulse_files(fileNames)
    else:
        # Didn't produce a function
        pass
