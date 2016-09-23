# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# See RabiMin for more function QGL2 versions of these functions.

import QGL.PulseShapes
from QGL.PulsePrimitives import Utheta, MEAS, X, Id
from QGL.Compiler import compile_to_hardware
from QGL.PulseSequencePlotter import plot_pulse_files

from qgl2.basic_sequences.helpers import create_cal_seqs
from qgl2.basic_sequences.new_helpers import compileAndPlot
from qgl2.util import init
from pyqgl2.main import compileFunction

from functools import reduce
import operator
import os.path

from qgl2.qgl2 import qgl2decl, qbit, qbit_list, qgl2main, concur, sequence
from qgl2.qgl1 import Utheta, MEAS, X, Id, QubitFactory
import numpy as np

@qgl2decl
def doRabiAmp(q:qbit, amps, phase):
    for amp in np.linspace(0,1,11):
        init(q)
        Utheta(q, amp=amp, phase=phase)
        MEAS(q)

# currently ignores all arguments except 'qubit'
def RabiAmp(qubit, amps, phase=0, showPlot=False):
    """
    Variable amplitude Rabi nutation experiment.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel)
    amps : pulse amplitudes to sweep over (iterable)
    phase : phase of the pulse (radians)
    showPlot : whether to plot (boolean)
    """
    resFunction = compileFunction(
        os.path.relpath(__file__),
        "doRabiAmp",
        (qubit, amps, phase)
        )
    seqs = resFunction()
    return seqs

    fileNames = qgl2_compile_to_hardware(seqs, "Rabi/Rabi")
    print(fileNames)
    if showPlot:
        plot_pulse_files(fileNames)

@qgl2decl
def doRabiWidth(q:qbit, widths, amp, phase, shape):
    for l in widths:
        init(q)
        # FIXME: QGL2 loses the import needed for this QGL function
        Utheta(q, length=l, amp=amp, phase=phase, shapeFun=shape)
        MEAS(q)

def RabiWidth(qubit, widths, amp=1, phase=0, shapeFun=QGL.PulseShapes.tanh, showPlot=False):
    """
    Variable pulse width Rabi nutation experiment.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel)
    widths : pulse widths to sweep over (iterable)
    phase : phase of the pulse (radians, default = 0)
    shapeFun : shape of pulse (function, default = PulseShapes.tanh)
    showPlot : whether to plot (boolean)
    """

    resFunction = compileFunction(
        os.path.relpath(__file__),
        "doRabiWidth"
        (qubit, widths, amp, phase, shapeFun)
        )
    seqs = resFunction()
    return seqs

    fileNames = qgl2_compile_to_hardware(seqs, "Rabi/Rabi")
    print(fileNames)
    if showPlot:
        plot_pulse_files(fileNames)

@qgl2decl
def doRabiAmp_NQubits(qubits: qbit_list, amps, phase,
                    measChans: qbit_list, docals, calRepeats):
    for amp in amps:
        with concur:
            for q in qubits:
                init(q)
                Utheta(q, amp=amp, phase=phase)
        with concur:
            for m in measChans:
                MEAS(m)

    if docals:
        create_cal_seqs(qubits, calRepeats, measChans)

def RabiAmp_NQubitsq1(qubits, amps, phase=0, showPlot=False,
                    measChans=None, docals=False, calRepeats=2):
    """
    Variable amplitude Rabi nutation experiment for an arbitrary number of qubits simultaneously

    Parameters
    ----------
    qubits : tuple of logical channels to implement sequence (LogicalChannel)
    amps : pulse amplitudes to sweep over for all qubits (iterable)
    phase : phase of the pulses (radians)
    showPlot : whether to plot (boolean)
    measChans : tuble of qubits to be measured (LogicalChannel)
    docals, calRepeats: enable calibration sequences, repeated calRepeats times
    """

    if measChans is None:
        measChans = qubits

    resFunction = compileFunction(
        os.path.relpath(__file__),
        "doRabiWidth",
        (qubits, amps, phase, measChans, docals, calRepeats)
        )
    seqs = resFunction()
    return seqs

    fileNames = qgl2_compile_to_hardware(seqs, "Rabi/Rabi")
    print(fileNames)
    if showPlot:
        plot_pulse_files(fileNames)

@qgl2decl
def doRabiAmpPi(qubit: qbit, mqubit: qbit, amps, phase):
    for amp in amps:
        with concur:
            init(qubit)
            init(mqubit)
        X(mqubit)
        Utheta(qubit, amp=amp, phase=phase)
        X(mqubit)
        MEAS(mqubit)

def RabiAmpPi(qubit: qbit, mqubit: qbit, amps, phase=0, showPlot=False):
    """
    Variable amplitude Rabi nutation experiment.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel)
    amps : pulse amplitudes to sweep over (iterable)
    phase : phase of the pulse (radians)
    showPlot : whether to plot (boolean)
    """
    resFunction = compileFunction(
        os.path.relpath(__file__),
        "doRabiAmpPi",
        (qubit, mqubit, amps, phase)
        )
    seqs = resFunction()
    return seqs

    fileNames = qgl2_compile_to_hardware(seqs, "Rabi/Rabi")
    print(fileNames)
    if showPlot:
        plot_pulse_files(fileNames)

@qgl2decl
def doSingleShot(qubit: qbit):
    """
    2-segment sequence with qubit prepared in |0> and |1>, useful for single-shot fidelity measurements and kernel calibration
    """
    init(qubit)
    Id(qubit)
    MEAS(qubit)
    init(qubit)
    X(qubit)
    MEAS(qubit)

def SingleShot(qubit: qbit, showPlot=False):
    """
    2-segment sequence with qubit prepared in |0> and |1>, useful for single-shot fidelity measurements and kernel calibration
    """
    resFunction = compileFunction(
        os.path.relpath(__file__),
        "doSingleShot",
        (qubit,)
        )
    seqs = resFunction()
    return seqs

    fileNames = qgl2_compile_to_hardware(seqs, "SingleShot/SingleShot")
    print(fileNames)
    if showPlot:
        plot_pulse_files(fileNames)

@qgl2decl
def doPulsedSpec(qubit: qbit, specOn):
    init(qubit)
    if specOn:
        X(qubit)
    else:
        Id(qubit)
    MEAS(qubit)

def PulsedSpec(qubit, specOn=True, showPlot=False):
    """
    Measurement preceded by a qubit pulse if specOn = True
    """
    resFunction = compileFunction(
        os.path.relpath(__file__),
        "doSingleShot",
        (qubit,)
        )
    seqs = resFunction()
    return seqs

    fileNames = qgl2_compile_to_hardware(seqs, "Spec/Spec")
    print(fileNames)
    if showPlot:
        plot_pulse_files(fileNames)

@qgl2decl
def doSwap(qubit: qbit, mqubit: qbit, delays):
    # Original:
    # seqs = [[X(qubit), X(mqubit), Id(mqubit, d), MEAS(mqubit)*MEAS(qubit)] for d in delays] + create_cal_seqs((mqubit,qubit), 2, measChans=(mqubit,qubit))

    # fileNames = compile_to_hardware(seqs, 'Rabi/Rabi')
    # print(fileNames)

    # if showPlot:
    #     plotWin = plot_pulse_files(fileNames)
    #     return plotWin
    for d in delays:
        with concur:
            init(qubit)
            init(mqubit)
        X(qubit)
        X(mqubit)
        Id(mqubit, d)
        with concur:
            MEAS(mqubit)
            MEAS(qubit)

    create_cal_seqs((mqubit, qubit), 2)

def Swap(qubit, mqubit, delays, showPlot=False):
    """
    Variable amplitude Rabi nutation experiment.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel)
    amps : pulse amplitudes to sweep over (iterable)
    phase : phase of the pulse (radians)
    showPlot : whether to plot (boolean)
    """
    resFunction = compileFunction(
        os.path.relpath(__file__),
        "doSwap",
        (qubit,)
        )
    seqs = resFunction()
    return seqs

    fileNames = qgl2_compile_to_hardware(seqs, "Swap/Swap")
    print(fileNames)
    if showPlot:
        plot_pulse_files(fileNames)
