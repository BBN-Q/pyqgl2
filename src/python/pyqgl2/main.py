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
from pyqgl2.quickcopy import quickcopy
from datetime import datetime

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
from pyqgl2.debugmsg import DebugMsg
from pyqgl2.eval import EvalTransformer, SimpleEvaluator
from pyqgl2.flatten import Flattener
from pyqgl2.grouper import AddSequential
from pyqgl2.grouper import MarkReferencedQbits
from pyqgl2.grouper import QbitGrouper2
from pyqgl2.importer import NameSpaces, add_import_from_as
from pyqgl2.inline import Inliner
from pyqgl2.repeat import RepeatTransformer
from pyqgl2.sequence import SequenceCreator
from pyqgl2.sequences import SequenceExtractor, get_sequence_function
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


def compileFunction(filename,
                    main_name=None,
                    toplevel_bindings=None,
                    saveOutput=False,
                    intermediate_output=None):

    NodeError.reset()

    print('\n\nCOMPILING [%s] main %s' %
            (filename, main_name if main_name else '(default)'))

    # Use whether intermediate_output is None to decide
    # whether to call printout blocks at all
    # Old code set intermediate_output to /dev/null

    if intermediate_output:
        try:
            intermediate_fout = open(intermediate_output, 'w')
        except BaseException as exc:
            NodeError.fatal_msg(None,
                    ('cannot save intermediate output in [%s]' %
                        intermediate_output))
    else:
        intermediate_fout = None

    # Process imports in the input file, and find the main.
    # If there's no main, then bail out right away.

    try:
        rel_path = os.path.relpath(filename)
        filename = rel_path
    except Exception as e:
        # If that wasn't a good path, give up immediately
        NodeError.error_msg(
                None, "Failed to make relpath from %s: %s" % (filename, e))

    NodeError.halt_on_error()

    importer = NameSpaces(filename, main_name)
    if not importer.qglmain:
        NodeError.fatal_msg(None, 'no qglmain function found')

    NodeError.halt_on_error()

    ptree = importer.qglmain

    if intermediate_output:
        ast_text_orig = pyqgl2.ast_util.ast2str(ptree)
        print(('%s: ORIGINAL CODE:\n%s' % (datetime.now(), ast_text_orig)),
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

    # We may need to iterate over the inlining processes a few times,
    # because inlining may expose new things to inline.
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

        print('%s: ITERATION %d' % (datetime.now(), iteration))

        inliner = Inliner(importer)
        ptree1 = inliner.inline_function(ptree1)
        NodeError.halt_on_error()

        if intermediate_output:
            print(('INLINED CODE (iteration %d):\n%s' %
                   (iteration, pyqgl2.ast_util.ast2str(ptree1))),
                  file=intermediate_fout, flush=True)

        type_check = CheckType(filename, importer=importer)
        # ptree1 = type_check.visit(ptree1)
        NodeError.halt_on_error()
        # if intermediate_output:
        #     print(('CHECKED CODE (iteration %d):\n%s' %
        #            (iteration, pyqgl2.ast_util.ast2str(ptree1))),
        #           file=intermediate_fout, flush=True)

        if inliner.change_cnt == 0:
            NodeError.diag_msg(None,
                    ('expansion converged after iteration %d' % iteration))
            break

    if iteration == (MAX_ITERS - 1):
        NodeError.error_msg(None,
                ('expansion did not converge after %d iterations' % MAX_ITERS))

    # transform passed toplevel_bindings into a local_context dictionary
    arg_names = [x.arg for x in ptree1.args.args]
    if isinstance(toplevel_bindings, tuple):
        if len(arg_names) != len(toplevel_bindings):
            NodeError.error_msg(None,
                'Invalid number of arguments supplied to qgl2main')
        local_context = {name: quickcopy(value) for name, value in zip(arg_names, toplevel_bindings)}
    elif isinstance(toplevel_bindings, dict):
        invalid_args = toplevel_bindings.keys() - arg_names
        if len(invalid_args) > 0:
            NodeError.error_msg(None,
                'Invalid arguments supplied to qgl2main: {}'.format(invalid_args))
        missing_args = arg_names - toplevel_bindings.keys()
        if len(missing_args) > 0:
            NodeError.error_msg(None,
                'Missing arguments for qgl2main: {}'.format(missing_args))
        local_context = quickcopy(toplevel_bindings)
    elif toplevel_bindings:
        NodeError.error_msg(None,
                'Unrecognized type for toplevel_bindings: {}'.format(type(toplevel_bindings)))
    else:
        local_context = None
    NodeError.halt_on_error()

    evaluator = EvalTransformer(SimpleEvaluator(importer, local_context))

    print('%s: CALLING EVALUATOR' % datetime.now())
    ptree1 = evaluator.visit(ptree1)
    NodeError.halt_on_error()

    if DebugMsg.ACTIVE_LEVEL < 3:
        print('%s: EVALUATOR RESULT:\n%s' % (datetime.now(), pyqgl2.ast_util.ast2str(ptree1)))
    # It's very hard to read the intermediate form, before the
    # QBIT names are added, so we don't save this right now.
    # print(('EVALUATOR RESULT:\n%s' % pyqgl2.ast_util.ast2str(ptree1)),
    #         file=intermediate_fout, flush=True)

    # Dump out all the variable bindings, for debugging purposes
    #
    # print('EV total state:')
    # evaluator.print_state()

    evaluator.replace_bindings(ptree1.body)

    if DebugMsg.ACTIVE_LEVEL < 3:
        print('%s: EVALUATOR REBINDINGS:\n%s' % (datetime.now(),
                                                 pyqgl2.ast_util.ast2str(ptree1)))
    if intermediate_output:
        print(('EVALUATOR + REBINDINGS:\n%s' % pyqgl2.ast_util.ast2str(ptree1)),
              file=intermediate_fout, flush=True)

    base_namespace = importer.path2namespace[filename]
    text = base_namespace.pretty_print()

    if intermediate_output:
        print(('EXPANDED NAMESPACE:\n%s' % text),
              file=intermediate_fout, flush=True)

    new_ptree1 = ptree1

    # Make sure that functions that take qbits are getting qbits
    new_ptree5 = new_ptree1
    # sym_check = CheckSymtab(filename, type_check.func_defs, importer)
    # new_ptree5 = sym_check.visit(new_ptree1)
    NodeError.halt_on_error()
    if intermediate_output:
        print(('%s: SYMTAB CODE:\n%s' % (datetime.now(), pyqgl2.ast_util.ast2str(new_ptree5))),
              file=intermediate_fout, flush=True)

    MarkReferencedQbits.marker(new_ptree5,
            local_vars=evaluator.eval_state.locals_stack[-1])

    seq = AddSequential()
    new_ptree5 = seq.visit(new_ptree5)
    NodeError.halt_on_error()
    if intermediate_output:
        print(('%s: SEQUENTIAL CODE:\n%s' % (datetime.now(), pyqgl2.ast_util.ast2str(new_ptree5))),
              file=intermediate_fout, flush=True)

    # Take with-infunc and with-concur blocks and produce with-grouped
    # and with-group blocks
    #
    grouper = QbitGrouper2()
    new_ptree6 = grouper.group(new_ptree5,
            local_vars=evaluator.eval_state.locals_stack[-1])
    NodeError.halt_on_error()
    if intermediate_output:
        print(('%s: GROUPED CODE:\n%s' % (datetime.now(), pyqgl2.ast_util.ast2str(new_ptree6))),
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
    if intermediate_output:
        print(('%s: FLATTENED CODE:\n%s' % (datetime.now(), pyqgl2.ast_util.ast2str(new_ptree7))),
              file=intermediate_fout, flush=True)

    evaluator.replace_bindings(new_ptree7.body)
    evaluator.get_state()

    # We're not going to print this, at least not for now,
    # although it's sometimes a useful pretty-printing
    if False:
        sequencer = SequenceCreator()
        sequencer.visit(new_ptree7)
        NodeError.halt_on_error()

        if DebugMsg.ACTIVE_LEVEL < 3:
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

    if intermediate_output:
        print(('Final qglmain: %s' % new_ptree7.name),
              file=intermediate_fout, flush=True)

    # These values are set above
    #base_namespace = importer.path2namespace[filename]
    #text = base_namespace.pretty_print()
    if intermediate_output:
        print(('%s: FINAL CODE:\n-- -- -- -- --\n%s\n-- -- -- -- --' % (datetime.now(), text)),
              file=intermediate_fout, flush=True)

    sync = SynchronizeBlocks(new_ptree7)
    new_ptree8 = sync.visit(quickcopy(new_ptree7))
    NodeError.halt_on_error()
    if intermediate_output:
        print(('%s: SYNCED SEQUENCES:\n%s' % (datetime.now(), pyqgl2.ast_util.ast2str(new_ptree8))),
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
    qgl1_main = get_sequence_function(new_ptree8, fname,
            importer, intermediate_fout, saveOutput, filename,
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

################
# Helpers for qgl2_compile_to_hardware follow

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

def getNonEmptySequences(seqs, seqIdxToChannelMap, seqIdxToEdgeMap):
    '''
    Filter the set of sequences to only include non-empty sequences.
    Reset indices in the 2 maps to match.
    Return a tuple of (newly revised) seqs, seqIdxToChannelMap, seqIdxToEdgeMap
    '''
    import logging

    logger = logging.getLogger('QGL.Compiler.qgl2')

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
        newEdgeMap = dict()
        for ind in seqIdxToChannelMap:
            if ind in toDecr:
                newmap[ind-decr] = seqIdxToChannelMap[ind]
                if ind in seqIdxToEdgeMap:
                    newEdgeMap[ind-decr] = seqIdxToEdgeMap[ind]
                logger.debug("Sequence %d (channel %s) is now sequence %d", ind, seqIdxToChannelMap[ind], ind-decr)
            elif ind in seqIdxToChannelMap:
                logger.debug("Sequence %d keeping map to %s", ind, seqIdxToChannelMap[ind])
                newmap[ind] = seqIdxToChannelMap[ind]
                if ind in seqIdxToEdgeMap:
                    newEdgeMap[ind] = seqIdxToEdgeMap[ind]
            else:
                logger.debug("Dropping (empty) sequence %d", ind)
        seqIdxToChannelMap = newmap
        seqIdxToEdgeMap = newEdgeMap
    return (seqs, seqIdxToChannelMap, seqIdxToEdgeMap)

def getEdgesToCompile(seqIdxToEdgeMap, awgToSeqIdxMap, seqIdxToChannelMap):
    '''
    Compute the list of edges to compile for each sequence and return it
    Build a per sequence list of the edges that share an AWG with that sequence (Qubit),
    falling back to picking the sequence matching the source of the edge
    '''
    import logging

    logger = logging.getLogger('QGL.Compiler.qgl2')

    seqIdxToEdgeToCompileMap = dict() # int to list of Edges to actually compile on that sequence

    # Find the AWG and therefore sequence for each edge
    # For each sequence look at the edges it uses and build that li
    for idx in seqIdxToEdgeMap:
        for e in seqIdxToEdgeMap[idx]:
            ea = getAWG(e)
            # If that AWG is one that maps to a sequence, put the Edge there
            if ea in awgToSeqIdxMap:
                ei = awgToSeqIdxMap[ea]
                eaCh = seqIdxToChannelMap[ei]
                if not ei in seqIdxToEdgeToCompileMap:
                    seqIdxToEdgeToCompileMap[ei] = list()
                # Only add the Edge once (since we'll see the Edge a couple times at least)
                if not e in seqIdxToEdgeToCompileMap[ei]:
                    seqIdxToEdgeToCompileMap[ei].append(e)
                    logger.debug("%s uses AWG %s as does channel %s, so compile Edge when doing sequence %d", e, ea, eaCh, ei)
            else:
                # The AWG for the edge is not the AWG for any sequence
                # So we want to pick a sequence randomly
                # Use that for the source
                source = e.source
                sourceI = -1
                for sip in seqIdxToChannelMap:
                    if seqIdxToChannelMap[sip] == source:
                        sourceI = sip
                        break
                if sourceI == -1:
                    # Didn't find e.source as a channel for any of the sequences - shouldn't happen
                    raise Exception("Couldn't find sequence for %s source %s" % (e, source))
                sea = getAWG(source)
                if not sourceI in seqIdxToEdgeToCompileMap:
                    seqIdxToEdgeToCompileMap[sourceI] = list()
                if not e in seqIdxToEdgeToCompileMap[sourceI]:
                    seqIdxToEdgeToCompileMap[sourceI].append(e)
                    logger.debug("%s uses own AWG %s, so compile when doing source %s (idx %d, AWG %s)", e, ea, source, sourceI, sea)
    return seqIdxToEdgeToCompileMap

def getSlaveTriggerSequence(seqs, seqIdxToChannelMap):
    '''
    Get the sequence index on which to compile the slave trigger.
    Use the sequence that shares an AWG with the slaveTrigger, if any.
    Avoid sequences with no qubit.
    If no sequence matches the AWG of the slave trigger,
    any sequence is OK - pick the first.
    '''
    from QGL import ChannelLibrary
    import logging

    logger = logging.getLogger('QGL.Compiler.qgl2')
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
    return slaveSeqInd

def countChannelsInSequences(seqs):
    '''
    Count the channels used on each sequence, returning in seqToChToCnt dict by seq index.
    Also gather list of Edges used on each sequence in seqIdxToEdgeMap.
    Finally, produce a set of unique channels used in these sequences.
    Return (seqToChToCnt, seqIdxToEdgeMap, channels)
    '''
    from QGL.Compiler import find_unique_channels
    from QGL.Channels import Qubit as qgl1Qubit
    from QGL.Channels import Edge
    from QGL.PatternUtils import flatten
    from qgl2.qgl1control import Barrier
    import collections
    import logging

    logger = logging.getLogger('QGL.Compiler.qgl2')

    seqIdxToEdgeMap = dict() # int to list of Edges used on that sequence

    # First, build a count of use of Qubits by sequence
    # This is only spot where we fully walk the sequences ideally
    # Here we also find Edges used on each sequence
    seqToChToCnt = dict()
    channels = set()
    for idx, seq in enumerate(seqs):
        seqToChToCnt[idx] = dict()
        thischannels = find_unique_channels(seq) # Does flatten()
        for ch in thischannels:
            if isinstance(ch, Edge):
                if not idx in seqIdxToEdgeMap:
                    seqIdxToEdgeMap[idx] = list()
                if not ch in seqIdxToEdgeMap[idx]:
                    seqIdxToEdgeMap[idx].append(ch)
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug("Sequence %d uses %s", idx, ch)
                        logger.debug(" - which is AWG '%s'", getAWG(ch))
            if not isinstance(ch, qgl1Qubit):
                continue
            seqToChToCnt[idx][ch] = 0
            channels.add(ch)

        # For Qubits, count # of pulses that reference them
        # Here we assume a list in the sequence only happens if QGL2 got
        # a stub that produces a list, so it couldn't know what is used within that stub
        # If we do not use flatten, counts match what QGL2 saw
        # If we do use flatten, we can see what QGL1 will see and detect hidden bugs
#        for step in seq: # Do not flatten, so counts match what QGL2 used
        for step in flatten(seq):
            if hasattr(step, 'channel'):
                if isinstance(step.channel, qgl1Qubit):
                    seqToChToCnt[idx][step.channel] += 1
                elif isinstance(step.channel, collections.Iterable):
                    # Nominally a sequence element could be a PulseBlock
                    # that returns a list of channels
                    for ch in step.channel:
                        if isinstance(ch, qgl1Qubit):
                            seqToChToCnt[idx][ch] += 1

    logger.debug("From sequences got channel set: %s", channels)

    # Is any of the rest of the code in this method ever used?

    # If however we failed to find a channel for every sequence,
    # Look at Barriers and the source/target of edges
    # EG if a channel is referenced in args to a stub,
    # but then not used in a pulse (e.g. only to create an edge)
    # EG: a program that only does echoCR
    if len(channels) < len(seqs):
        # Missing some channels probably
        logger.debug("Found %d channels for %d sequences", len(channels), len(seqs))
        # Try looking at Barriers and Edges
        for idx, seq in enumerate(seqs):
            for step in seq:
                if isinstance(step, Barrier):
                    extras = step.chanlist or []
                    for ch in extras:
                        if ch not in channels:
                            logger.debug("Sequence %d had Barrier that mentioned new channel %s", idx, ch)
                            channels.add(ch)
                        # Note we add this channel as a key in the counts even if it wasn't "new"
                        if ch not in seqToChToCnt[idx]:
                            seqToChToCnt[idx][ch] = 0 # FIXME: 1?
            if idx not in seqIdxToEdgeMap:
                continue
            for edge in seqIdxToEdgeMap[idx]:
                if edge.source not in channels:
                    logger.debug("Sequence %d had Edge %s whose source is new: %s", idx, edge, edge.source)
                    channels.add(edge.source)
                # Note we add this channel as a key in the counts even if it wasn't "new"
                if edge.source not in seqToChToCnt[idx]:
                    seqToChToCnt[idx][edge.source] = 0 # FIXME: 1?
                if edge.target not in channels:
                    logger.debug("Sequence %d had Edge %s whose target is new: %s", idx, edge, edge.target)
                    channels.add(edge.target)
                # Note we add this channel as a key in the counts even if it wasn't "new"
                if edge.target not in seqToChToCnt[idx]:
                    seqToChToCnt[idx][edge.target] = 0 # FIXME: 1?
        logger.debug("... now have %d channels", len(channels))

    if len(channels) > len(seqs):
        logger.warning("Sequences use more channels (%d) than there are sequences (%d)!", len(channels), len(seqs))
    return (seqToChToCnt, seqIdxToEdgeMap, channels)

def mapQubitsToSequences(seqs):
    '''
    For given sequences, map qubits to sequence indices,
    and find the list of Edges used on each sequence.
    Return seqIdxToChannelMap, seqIdxToEdgeMap
    '''
    from QGL.Compiler import find_unique_channels
    from QGL.Channels import Qubit as qgl1Qubit
    from QGL.Channels import Edge
    from qgl2.qgl1control import Barrier
    import copy
    import logging

    logger = logging.getLogger('QGL.Compiler.qgl2')

    # First, count the use of each channel on each sequence,
    # get a list of Edges used on each sequence,
    # and get a set of the channels in use:
    (seqToChToCnt, seqIdxToEdgeMap, channels) = countChannelsInSequences(seqs)

    # Rest of this code is about properly mapping sequences and channels

    for seq in seqToChToCnt:
        for ch in seqToChToCnt[seq]:
            logger.debug("Sequence %d uses %s %d times", seq, ch, seqToChToCnt[seq][ch])

    seqIdxToChannelMap = dict() # int to Qubit

    # Use these to track if there are seqs/chs yet to map
    remainingChannels = copy.copy(channels)
    remainingSequences = set(range(len(seqs)))

    # In QGL2 when we group things by qbit, we insert at the beginning a special
    # Barrier with a name that starts with "group_marker" and is on only the local qbit
    # We look at that and use that to decide which Qubit this sequence is for.
    # This should only be wrong in case of a QGL2 bug, or a qgl1stub that uses a
    # different qbit than it was given as an argument (QGL2 user error I think).
    for idx, seq in enumerate(seqs):
        # If the seq has a single Barrier named group_marker* then pull out its Qubit - that's the channel
        bMarker = None
        for idx2, elem in enumerate(seq):
            if isinstance(elem, Barrier) and elem.value.startswith('group_marker'):
                if bMarker:
                    # 2nd group_marker on same sequence: a QGL2 error
                    logger.error("Sequence %d found 2nd group_marker at %d. 1st: %s, 2nd: %s", idx, idx2, bMarker, elem)
                    bMarker = None
                    break
                else:
                    logger.debug("Sequence %d had group_marker at %d: %s", idx, idx2, elem)
                    bMarker = elem
        if bMarker:
            if len(bMarker.chanlist) != 1:
                # QGL2 Error: Should be exactly 1
                # FIXME: Raise Exception?
                logger.error("Sequence %d group_marker %s doesn't list a single Qubit: %s", idx, bMarker, bMarker.chanlist)
                continue
            ch = bMarker.chanlist[0]
            if ch in seqIdxToChannelMap.values():
                # QGL2 error: Channel in 2 different group_marker barriers
                for i2 in seqIdxToChannelMap:
                    if seqIdxToChannelMap[i2] == ch:
                        # FIXME: Raise Exception?
                        logger.error("Sequence %d group_marker %s says this sequence is %s, but that Qubit is already assigned to sequence %d", idx, bMarker, ch, i2)
                        break
                continue
            if ch not in remainingChannels:
                # QGL2 error likely covered above
                # FIXME: Raise Exception?
                logger.error("Sequence %d group_marker %s lists only a qbit no longer remaining: %s", idx, bMarker, ch)
                continue
            logger.debug("Based on group_marker Barrier, assign sequence %d to %s", idx, ch)
            seqIdxToChannelMap[idx] = ch
            remainingChannels.discard(ch)
            remainingSequences.discard(idx)

            # Log at debug if a sequence has non-0 count for channel it is not assigned to
            # Can happen, eg from echoCR
            for ch2 in seqToChToCnt[idx]:
                if seqToChToCnt[idx][ch2] and ch2 != ch:
                    logger.debug("Sequence %d is channel %s, but uses %s %d times", idx, ch, ch2, seqToChToCnt[idx][ch2])
        else:
            # QGL2 error, unless this sequence is the empty one for Wait/Sync that used to happen
            logger.warning("Sequence %d had no group_marker Barrier to indicate it's Qubit", idx)

    # log at higher level if sequence has pulses for channel that is not
    # assigned to any sequence (bug/error)
    for seq in seqToChToCnt:
        for ch in seqToChToCnt[seq]:
            if not seqToChToCnt[seq][ch]:
                continue
            if ch in seqIdxToChannelMap.values():
                # Already log this situation above
                # This is EG from echoCR
                if seqIdxToChannelMap[seq] != ch:
                    logger.debug("Sequence %d has %d pulses on %s we will not compile (that channel is compiled elsewhere)", seq, seqToChToCnt[seq][ch], ch)
                continue

            # This could happen eg if a programmer wrote a stub that creates/uses a new Qubit
            # (or a QGL2 bug)
            logger.warning("Sequence %d uses channel %s %d times that is not assigned to any sequence (uncompiled pulses)", seq, ch, seqToChToCnt[seq][ch])

    if not remainingChannels:
        # Really there should be 0 remaining Sequences
        # But allow for 1 for 'no qubit', though that's really a QGL2 bug too
        if len(remainingSequences) > 1:
            logger.warning("More than 1 unassigned sequences but out of channels? %s", remainingSequences)
        return (seqIdxToChannelMap, seqIdxToEdgeMap)

    # Log warnings: shouldn't get here
    # Likely indicates QGL2 error, or programmer who introduced a new Qubit inside a stub
    logger.error("Failed to find mapping of all Qubits to sequences. Pulses on these Qubits will not be compiled: %s! %d unmapped sequences remain.", remainingChannels, len(remainingSequences))

    # FIXME: Raise exception?
    return (seqIdxToChannelMap, seqIdxToEdgeMap)

def qgl2_compile_to_hardware(seqs, filename, suffix=''):
    '''Custom compile_to_hardware for QGL2 that calls
    c2h once per sequence, specifically asking that the slaveTrigger be added only for the single
    channel that actually shares an AWG with the slaveTrigger,
    and ensuring Edges are only compiled once.
    Return is a list of filenames.'''
    from QGL.Compiler import compile_to_hardware
    from QGL.PatternUtils import flatten
    from QGL.PulseSequencer import Pulse, CompositePulse

    from pyqgl2.evenblocks import replaceBarriers

    import collections
    import logging

    logger = logging.getLogger('QGL.Compiler.qgl2')

    # Find the channel for each sequence, and the edges
    # on each sequence
    (seqIdxToChannelMap, seqIdxToEdgeMap) = mapQubitsToSequences(seqs)

    # Hack: skip the empty sequence(s) now before doing anything else
    (seqs, seqIdxToChannelMap, seqIdxToEdgeMap) = getNonEmptySequences(seqs, seqIdxToChannelMap, seqIdxToEdgeMap)

    # Try to replace Barrier commands with Id pulses where possible, else with Sync/Wait
    seqs = replaceBarriers(seqs, seqIdxToChannelMap)

    # Assign AWGs
    awgToSeqIdxMap = dict() # awg to int sequence index
    for seq in seqIdxToChannelMap:
        awg = getAWG(seqIdxToChannelMap[seq])
        awgToSeqIdxMap[awg] = seq
        logger.debug("Sequence %d is on AWG %s", seq, awg)

    # Build a per sequence list of the edges that share an AWG with that sequence (Qubit),
    # falling back to picking the sequence matching the source of the edge
    # Produce dict of seq index (int) to list of edges to actually compile on that sequence
    seqIdxToEdgeToCompileMap = getEdgesToCompile(seqIdxToEdgeMap, awgToSeqIdxMap, seqIdxToChannelMap)
    # Now I have a per idx list of Edges that are OK To compile with that sequence

    # Pick the sequence with which to compile the slave Trigger.
    # Find the sequence whose channel's AWG is same as slave Channel, if
    # any. Avoid sequences without a qubit channel if any.
    # Fall back on picking the first sequence.
    slaveSeqInd = getSlaveTriggerSequence(seqs, seqIdxToChannelMap)

    # Now we call c2h for each seq
    # Start files list as a set so filenames are unique,
    # but return as a list so it can be a dictionary key
    files = set()
    for idx, seq in enumerate(seqs):
        # List of OK edges to compile for this sequence
        edges = list()
        if idx in seqIdxToEdgeToCompileMap:
            edges = seqIdxToEdgeToCompileMap[idx]
        logger.debug("c_to_h compiling only edges %s, Qubit %s", edges, seqIdxToChannelMap[idx])

        doSlave = False
        if idx == slaveSeqInd:
            logger.debug("Asking for slave trigger with sequence %d", idx)
            doSlave = True
        else:
            logger.debug("Asking for sequence %d", idx)

        # Some stubs are functions that return a list of pulses (echoCR),
        # so an element of the sequence is itself a list. We don't want that. So flatten it out
        hasList = False
        for el in seq:
            if isinstance(el, collections.Iterable) and not isinstance(el, (str, Pulse, CompositePulse)) :
                hasList = True
                break
        if hasList:
            logger.debug("Flattening sequence %d", idx)
            newS = []
            for el in flatten(seq):
                newS.append(el)
            seq = newS

        newfiles = compile_to_hardware([seq], filename, suffix, qgl2=True, addQGL2SlaveTrigger=doSlave, edgesToCompile=edges, qubitToCompile=seqIdxToChannelMap[idx])
        if newfiles:
            logger.debug("Produced files: %s", newfiles)
            for nfile in newfiles:
                if nfile in files:
                    logger.warning("Filename overlap: %s", nfile)
            files = files.union(newfiles)
        else:
            logger.debug("Produced no new files")
    return list(files)

######
# Run the main with
# main.py <path to file with a qgl2decl to compile that creates
#              sequences you want to compile and plot>
#        -m <name of qgl2main if not decorated>
#        [-o if you want the compiled qgl1 function saved to a file]
#####

if __name__ == '__main__':
    import psutil
    opts = parse_args(sys.argv[1:])
    if opts.verbose:
        process = psutil.Process(os.getpid())
        print("Memory usage: {} MB".format(process.memory_info().rss // (1 << 20)))

    import QGL
    if QGL.ChannelLibrary.channelLib and 'slaveTrig' in QGL.ChannelLibrary.channelLib:
        print("Using ChannelLibrary from config")
    elif opts.verbose or opts.intermediate_output != '' or opts.debug_level < 3:
        print("Using APS2ish 3 qubit test channel library")
        # Hack. Create a basic channel library for testing
        import test.helpers
        test.helpers.channel_setup()
    else:
        sys.exit("No valid ChannelLibrary found")

    resFunction = compileFunction(
            opts.filename, opts.main_name,
            toplevel_bindings=None, saveOutput=opts.saveOutput,
            intermediate_output=opts.intermediate_output)
    if resFunction:
        # Now import the QGL1 things we need
        from QGL.PulseSequencePlotter import plot_pulse_files
        from QGL.ChannelLibrary import QubitFactory
        import os

        # Now execute the returned function, which should produce a list of sequences
        sequences = resFunction()

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
    if opts.verbose:
        print("Memory usage: {} MB".format(process.memory_info().rss // (1 << 20)))
