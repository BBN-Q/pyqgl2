# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import QGL.PulseShapes
from QGL.PulsePrimitives import Utheta, MEAS, X, Id
from QGL.Compiler import compile_to_hardware
from QGL.PulseSequencePlotter import plot_pulse_files

from .helpers import create_cal_seqs

from functools import reduce
import operator

from qgl2.qgl2 import qgl2decl, qbit, qbit_list

@qgl2decl
def RabiAmp(qubit: qbit, amps, phase=0, showPlot=False):
    """

    Variable amplitude Rabi nutation experiment.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel)
    amps : pulse amplitudes to sweep over (iterable)
    phase : phase of the pulse (radians)
    showPlot : whether to plot (boolean)

    Returns
    -------
    plotHandle : handle to plot window to prevent destruction
    """
    raise NotImplementedError("Not implemented")

    # Original:
    # seqs = [[Utheta(qubit, amp=amp, phase=phase), MEAS(qubit)] for amp in amps]

    # fileNames = compile_to_hardware(seqs, 'Rabi/Rabi')
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)

@qgl2decl
def RabiWidth(qubit: qbit, widths, amp=1, phase=0, shapeFun=QGL.PulseShapes.tanh, showPlot=False):
    """

    Variable pulse width Rabi nutation experiment.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel)
    widths : pulse widths to sweep over (iterable)
    phase : phase of the pulse (radians, default = 0)
    shapeFun : shape of pulse (function, default = PulseShapes.tanh)
    showPlot : whether to plot (boolean)

    Returns
    -------
    plotHandle : handle to plot window to prevent destruction
    """
    raise NotImplementedError("Not implemented")

    # Original: 
    # seqs = [[Utheta(qubit, length=l, amp=amp, phase=phase, shapeFun=shapeFun), MEAS(qubit)] for l in widths]

    # fileNames = compile_to_hardware(seqs, 'Rabi/Rabi')
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)

@qgl2decl
def RabiAmp_NQubits(qubits: qbit_list, amps, phase=0, showPlot=False,
                    measChans: qbit_list = None, docals=False, calRepeats=2):
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

    Returns
    -------
    plotHandle : handle to plot window to prevent destruction
    """
    raise NotImplementedError("Not implemented")

    # Original:
    # if measChans is None:
    #     measChans = qubits

    # seqs = [[reduce(operator.mul, [Utheta(q, amp=amp, phase=phase) for q in qubits]),MEAS(*measChans)] for amp in amps]

    # if docals:
    #     seqs += create_cal_seqs(qubits, calRepeats, measChans=measChans)

    # fileNames = compile_to_hardware(seqs, 'Rabi/Rabi')
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)

@qgl2decl
def RabiAmpPi(qubit: qbit, mqubit: qbit, amps, phase=0, showPlot=False):
    """

    Variable amplitude Rabi nutation experiment.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel)
    amps : pulse amplitudes to sweep over (iterable)
    phase : phase of the pulse (radians)
    showPlot : whether to plot (boolean)

    Returns
    -------
    plotHandle : handle to plot window to prevent destruction
    """
    raise NotImplementedError("Not implemented")

    # Original:
    # seqs = [[X(mqubit),Utheta(qubit, amp=amp, phase=phase), X(mqubit), MEAS(mqubit)] for amp in amps]

    # fileNames = compile_to_hardware(seqs, 'Rabi/Rabi')
    # print(fileNames)

    # if showPlot:
    #     plotWin = plot_pulse_files(fileNames)
    #     return plotWin

@qgl2decl
def SingleShot(qubit: qbit, showPlot = False):
    """
    2-segment sequence with qubit prepared in |0> and |1>, useful for single-shot fidelity measurements and kernel calibration
    """
    raise NotImplementedError("Not implemented")

    # Original:
    # seqs = [[Id(qubit), MEAS(qubit)], [X(qubit), MEAS(qubit)]]
    # filenames = compile_to_hardware(seqs, 'SingleShot/SingleShot')
    # print(filenames)

    # if showPlot:
    #     plot_pulse_files(filenames)

@qgl2decl
def PulsedSpec(qubit: qbit, specOn = True, showPlot = False):
    """
    Measurement preceded by a qubit pulse if specOn = True
    """
    raise NotImplementedError("Not implemented")

    # Original:
    # qPulse = X(qubit) if specOn else Id(qubit)
    # seqs = [[qPulse, MEAS(qubit)]]
    # filenames = compile_to_hardware(seqs, 'Spec/Spec')
    # print(filenames)

    # if showPlot:
    #     plot_pulse_files(filenames)

@qgl2decl
def Swap(qubit: qbit, mqubit: qbit, delays, showPlot=False):
    """
    Variable amplitude Rabi nutation experiment.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel)
    amps : pulse amplitudes to sweep over (iterable)
    phase : phase of the pulse (radians)
    showPlot : whether to plot (boolean)

    Returns
    -------
    plotHandle : handle to plot window to prevent destruction
    """
    raise NotImplementedError("Not implemented")

    # Original:
    # seqs = [[X(qubit), X(mqubit), Id(mqubit, d), MEAS(mqubit)*MEAS(qubit)] for d in delays] + create_cal_seqs((mqubit,qubit), 2, measChans=(mqubit,qubit))

    # fileNames = compile_to_hardware(seqs, 'Rabi/Rabi')
    # print(fileNames)

    # if showPlot:
    #     plotWin = plot_pulse_files(fileNames)
    #     return plotWin
