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

from pyqgl2.ast_util import NodeError
from pyqgl2.debugmsg import DebugMsg
from pyqgl2.eval import EvalTransformer, SimpleEvaluator
from pyqgl2.flatten import Flattener
from pyqgl2.importer import NameSpaces, add_import_from_as
from pyqgl2.inline import Inliner
from pyqgl2.sequences import SequenceExtractor, get_sequence_function


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

    parser.add_argument('-C',
            dest='create_channels', default=False, action='store_true',
            help='create default channels, if none are provided')

    # db_resource_name to load using ChannelLibraries() constructor.
    # No default,
    parser.add_argument('-cl', dest='channel_library', type=str, metavar='CHANNEL_LIBRARY', default=None,
                        help='Name of Channel Library to load')

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

    parser.add_argument('-hw', dest='tohw', default=False, action='store_true',
                        help='Compile sequences to hardware (default %(default)s)')

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

# Takes filename (relative path), name of main (-m arg)
# If no main, look for function in the file with decorator @qgl2main
# toplevel_bindings is list of arguments the function takes
# saveOutput: save the generated qgl1 program? See -o flag
# intermediate_output: name of file to save intermediate/debug output to; see -S flag
def compile_function(filename,
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

    print('%s: CALLING IMPORTER' % datetime.now())
    importer = NameSpaces(filename, main_name)
    if not importer.qglmain:
        NodeError.fatal_msg(None, 'no qglmain function found')

    NodeError.halt_on_error()

    ptree = importer.qglmain

    if intermediate_output:
        ast_text_orig = pyqgl2.ast_util.ast2str(ptree)
        print(('%s: ORIGINAL CODE:\n%s' % (datetime.now(), ast_text_orig)),
              file=intermediate_fout, flush=True)

    # When QGL2 flattens various kinds of control flow and runtime
    # computations it emits QGL1 instruction that the user may not
    # have imported.
    #
    # TODO: this is a hack, but the approach of adding these
    # blindly to the namespace is also a hack.  This is a
    # placeholder until we figure out a cleaner approach.

    required_imports = ['Wait', 'Barrier', 'Goto', 'LoadCmp', 'CmpEq', 'CmpNeq',
        'CmpGt', 'CmpLt', 'BlockLabel', 'Store']

    modname = ptree.qgl_fname
    for symbol in required_imports:
        if not add_import_from_as(importer, modname, 'qgl2.qgl1', symbol):
            NodeError.error_msg(ptree, 'Could not import %s' % symbol)
    NodeError.halt_on_error()

    ptree1 = ptree

    # We may need to iterate over the inlining processes a few times,
    # because inlining may expose new things to inline.
    #
    # TODO: as a stopgap, we're going to limit iterations to 20, which
    # is enough to handle fairly deeply-nested, complex non-recursive
    # programs.  What we do is iterate until we converge (the outcome
    # stops changing) or we hit this limit.  We should attempt at this
    # point to prove that the expansion is divergent, but we don't
    # do this, but instead assume the worst if the program is complex
    # enough to look like it's "probably" divergent.
    #

    print('%s: CALLING INLINER' % datetime.now())
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

    # base_namespace = importer.path2namespace[filename]

    # if intermediate_output:
    #     text = base_namespace.pretty_print()
    #     print(('EXPANDED NAMESPACE:\n%s' % text),
    #           file=intermediate_fout, flush=True)

    new_ptree1 = ptree1

    # Try to flatten out repeat, range, ifs
    flattener = Flattener()
    print('%s: CALLING FLATTENER' % datetime.now())
    new_ptree2 = flattener.visit(new_ptree1)
    NodeError.halt_on_error()
    if intermediate_output:
        print(('%s: FLATTENED CODE:\n%s' % (datetime.now(), pyqgl2.ast_util.ast2str(new_ptree2))),
              file=intermediate_fout, flush=True)

    # TODO Is it ever necessary to replace bindings again at this point?
    # evaluator.replace_bindings(new_ptree2.body)
    # evaluator.get_state()

    if intermediate_output:
        print(('Final qglmain: %s\n' % new_ptree2.name),
              file=intermediate_fout, flush=True)

    new_ptree3 = new_ptree2

    # Done. Time to generate the QGL1

    # Try to guess the proper function name
    fname = main_name
    if not fname:
        if isinstance(ptree, ast.FunctionDef):
            fname = ptree.name
        else:
            fname = "qgl1Main"

    # Get the QGL1 function that produces the proper sequences
    print('%s: GENERATING QGL1 SEQUENCE FUNCTION' % datetime.now())
    qgl1_main = get_sequence_function(new_ptree3, fname,
            importer, evaluator.allocated_qbits, intermediate_fout,
            saveOutput, filename, setup=evaluator.setup())
    NodeError.halt_on_error()
    return qgl1_main

def qgl2_compile_to_hardware(seqs, filename, suffix=''):
    '''
    Custom compile_to_hardware for QGL2
    '''

    from QGL.Compiler import compile_to_hardware
    from QGL.Scheduler import schedule

    scheduled_seq = schedule(seqs)

    return compile_to_hardware([scheduled_seq], filename, suffix)

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

    # Handle option asking to use an existing channel library
    if opts.channel_library is not None:
        cl = None
        try:
            # This will load or create a file of the given name,
            # unless the name is the special ":memory:"
            cl = QGL.ChannelLibraries.ChannelLibrary(db_resource_name=opts.channel_library)
            qcnt = len(cl.qubits())
            print(f"Loaded Channel Library from '{opts.channel_library}' with {qcnt} qubits")
        except Exception as e:
            print(f"Failed to load Channel Library from '{opts.channel_library}': {e}")

    # We require that the CL have a slave trigger to be usable currently, otherwise
    # We create a new one if so requested, or we give up.
    if (QGL.ChannelLibraries.channelLib and
            ('slave_trig' in QGL.ChannelLibraries.channelLib)):
        print("Using ChannelLibrary from config")
    elif (opts.create_channels or opts.verbose or
            opts.intermediate_output != '' or opts.debug_level < 3):
        print("Will create and use APS2ish 3 qubit test channel library")
        # Hack. Create a basic channel library for testing
        # FIXME: Allow supplying a CL file to read?
        import test_cl
        test_cl.create_default_channelLibrary(opts.tohw)
    else:
        print('No valid ChannelLibrary found')
        sys.exit(1)

    resFunction = compile_function(
            opts.filename, opts.main_name,
            toplevel_bindings=None, saveOutput=opts.saveOutput,
            intermediate_output=opts.intermediate_output)

    if not resFunction:
        # If there aren't any Qubit operations, then we're
        # done.  The program may have been executed for
        # non-quantum effects.
        #
        print("The program in {} contains no Qubit operations?".format(opts.filename))
    else:
        # Now import the QGL1 things we need
        from QGL.PulseSequencePlotter import plot_pulse_files

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

        if opts.tohw:
            print("Compiling sequences to hardware\n")
            fileNames = qgl2_compile_to_hardware(sequences, opts.prefix,
                                                 opts.suffix)
            print(fileNames)
            if opts.showplot:
                plot_pulse_files(fileNames)
        else:
            print("\nGenerated sequences:\n")
            from QGL.Scheduler import schedule

            scheduled_seq = schedule(sequences)
            from IPython.lib.pretty import pretty
            print(pretty(scheduled_seq))

    if opts.verbose:
        print("Memory usage: {} MB".format(process.memory_info().rss // (1 << 20)))
