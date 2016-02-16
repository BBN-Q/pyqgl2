# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit_list, qbit

from .helpers import create_cal_seqs

from QGL.PulsePrimitives import Id, X, Y, X90, Y90, MEAS
from QGL.Compiler import compile_to_hardware
from QGL.PulseSequencePlotter import plot_pulse_files

import copy
import functools
import inspect
import operator


# Next 2 bits are intended to let the QGL2 compiler know when a function needs to be handed a list of sequences,
# a QGL1 style argument.
# Decorate the function with @qgl2AddSequences if you want the QGL2
# compiler to add the argument to the function call, and/or add the
# sequence_list tag to indicate which argument is the (single) list of sequences argument.
# If using the tagged approach, that argument must be passed to the function or be a keyword argument (in general)
# The compiler will replace the provided value with the correct value

# Tag to indicate that an argument is a list of sequences (which are lists of pulses)
# Used by QGL2 compiler to ID variable to substitute
sequence_list = 'sequence_list'

# Decorator to insert a list of sequences as the first argument to the wrapped function
# Or replace the provided value that is a sequence_list with that from the compiler
def qgl2AddSequences(function):
    @functools.wraps(function)
    def wrap_function(*args, **kwargs):

        # FIXME: QGL2 Compiler must replace this ***********
        QGL2_LIST_OF_SEQUENCES = [[None],[None]]

        # Try to find the spot for the listOfSequences using the annotation
        idx = 0
        sig = inspect.signature(function)
        found = False
        for param in sig.parameters:
            # Look for the single parameter of type sequence_list
            if sig.parameters[param].annotation == sequence_list:
                found = True
                if param in kwargs:
                    # If it is a KW arg that was supplied, replace the value
                    kwargs[param] = QGL2_LIST_OF_SEQUENCES
                    break
                else:
                    # It will be a non keyword arg
                    if (len(args)+len(kwargs)) < len(sig.parameters) and idx == 0:
                        # If it is the first arg in the signature and not enough args were given,
                        # insert it as the first arg
                        args = tuple([QGL2_LIST_OF_SEQUENCES]) + args
                        break
                    elif idx < len(args) and (len(args)+len(kwargs)) == len(sig.parameters):
                        # If the right number of args were given and the sequence_list is one of the non kw args,
                        # replace the provided value with this one
                        # FIXME: What if kwargs had a default?
                        args = tuple(args[:idx]) + tuple([QGL2_LIST_OF_SEQUENCES]) + tuple(args[idx+1:])
                        break
                    else:
                        # Didn't get enough arguments and seq_list isn't first arg,
                        # or something else and I don't know how to handle this
                        # Raise an error?
                        print("Failed to find sequence_list arg in call to %s(%s, %s)" % (function.__name__,
                                                                                          args, kwargs))
                        break
            idx += 1
        if not found:
            if len(sig.parameters) == len(args) + len(kwargs) + 1:
                # Missing exactly one arg: put this one first
                # FIXME: What if kwargs had a default?
                return function(QGL2_LIST_OF_SEQUENCES, args, kwargs)
        return function(*args, **kwargs)
    return wrap_function

# This one is qgl1 style
def addMeasPulse(listOfSequencesOn1Qubit: sequence_list, q: qbit):
    '''Add a MEAS(q) to each sequence in the given list of sequences.'''
    return [sequence + [MEAS(q)] for sequence in listOfSequencesOn1Qubit]

@qgl2decl
def measConcurrently(listNQubits: qbit_list):
    '''Concurrently measure each of the given qubits.'''
    with concur:
        for q in listNQubits:
            MEAS(q)

# This one is qgl1 style
# Variant of above to add a MEAS for each qbit used in the sequences, not just 1
def addMeasPulses(listOfSequencesOnNQubits: sequence_list, listNQubits: qbit_list):
    '''Add (one MEAS(qn) for each qubit qn in listNQubits) to each sequence in the given list of sequences.'''
    measurements = None
    for q in listNQubits:
        if measurements == None:
            measurements = MEAS(q)
        else:
            measurements *= MEAS(q)

    for sequence in listOfSequencesOnNQubits:
        sequence.append(measurements)
    return listOfSequencesOnNQubits

# What would a QGL2 style repeat look like? Is it just for _ in range?
# QGL1 style
def repeatSequences(listOfSequences: sequence_list, repeat=2):
    '''Repeat each sequence in the given list of sequences repeat times.

    For example, `[[a, 1], [b, 2]]` becomes `[[a, 1], [a, 1], [b, 2], [b, 2]]`.
    Note this could be a list of function names that then get executed.'''

    # You must copy the element before repeating it. Otherwise strange things happen later
    return [copy.copy(sequence) for sequence in listOfSequences for i in range(repeat)]

@qgl2AddSequences
def compileAndPlot(listOfSequences: sequence_list, filePrefix, showPlot=False):
    '''Compile the listOfSequences to hardware using the given filePrefix, 
    print the filenames, and optionally plot the pulse files.

    NOTE: The QGL2 compiler must fill in the listOfSequences in the decorator.'''
    fileNames = compile_to_hardware(listOfSequences, filePrefix)
    print(fileNames)

    if showPlot:
        plot_pulse_files(fileNames)

# QGL1 style method
# For QGL2, simply do create_cal_seqs((tupleOfQubits), numRepeats)
def addCalibration(listOfSequences: sequence_list, tupleOfQubits: qbit_list, numRepeats=2):
    '''Add on numRepeats calibration sequences of the given tuple of qubits to the given
    list of sequences.'''
    # Tack on the calibration sequences
    listOfSequences += create_cal_seqs((tupleOfQubits), numRepeats)
    return listOfSequences

# Helpers here for AllXY that produce pairs of pulses on the same qubit
# Produce the state |0>
@qgl2decl
def IdId(q: qbit):
    # no pulses
    Id(q)
    Id(q)

@qgl2decl
def XX(q: qbit):
    # pulse around same axis
    X(q)
    X(q)

@qgl2decl
def YY(q: qbit):
    # pulse around same axis
    Y(q)
    Y(q)

@qgl2decl
def XY(q: qbit):
    # pulsing around orthogonal axes
    X(q)
    Y(q)

@qgl2decl
def YX(q: qbit):
    # pulsing around orthogonal axes
    Y(q)
    X(q)

# These next produce a |+> or |i> state (equal superposition of |0> + |1>)
@qgl2decl
def X90Id(q: qbit):
    # single pulses
    X90(q)
    Id(q)

@qgl2decl
def Y90Id(q: qbit):
    # single pulses
    Y90(q)
    Id(q)

@qgl2decl
def X90Y90(q: qbit):
    # pulse pairs around orthogonal axes with 1e error sensititivity
    X90(q)
    Y90(q)

@qgl2decl
def Y90X90(q: qbit):
    # pulse pairs around orthogonal axes with 1e error sensititivity
    Y90(q)
    X90(q)

@qgl2decl
def X90Y(q: qbit):
    # pulse pairs with 2e sensitivity
    X90(q)
    Y(q)

@qgl2decl
def Y90X(q: qbit):
    # pulse pairs with 2e sensitivity
    Y90(q)
    X(q)

@qgl2decl
def XY90(q: qbit):
    # pulse pairs with 2e sensitivity
    X(q)
    Y90(q)

@qgl2decl
def YX90(q: qbit):
    # pulse pairs with 2e sensitivity
    Y(q)
    X90(q)

@qgl2decl
def X90X(q: qbit):
    # pulse pairs around common axis with 3e error sensitivity
    X90(q)
    X(q)

@qgl2decl
def XX90(q: qbit):
    # pulse pairs around common axis with 3e error sensitivity
    X(q)
    X90(q)

@qgl2decl
def Y90Y(q: qbit):
    # pulse pairs around common axis with 3e error sensitivity
    Y90(q)
    Y(q)

@qgl2decl
def YY90(q: qbit):
    # pulse pairs around common axis with 3e error sensitivity
    Y(q)
    Y90(q)

# These next create the |1> state
@qgl2decl
def XId(q: qbit):
    # single pulses
    X(q)
    Id(q)

@qgl2decl
def YId(q: qbit):
    # single pulses
    Y(q)
    Id(q)

@qgl2decl
def X90X90(q: qbit):
    # pulse pairs
    X90(q)
    X90(q)

@qgl2decl
def Y90Y90(q: qbit):
    # pulse pairs
    Y90(q)
    Y90(q)
