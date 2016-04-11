# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import QGL.PulseShapes
from QGL.PulsePrimitives import Utheta, MEAS, X, Id
from QGL.Compiler import compile_to_hardware
from QGL.PulseSequencePlotter import plot_pulse_files

from .helpers import create_cal_seqs
from .new_helpers import compileAndPlot
from .qgl2_plumbing import init

from functools import reduce
import operator

from qgl2.qgl2 import qgl2decl, qbit, qbit_list, qgl2main, concur
from qgl2.qgl1 import Utheta, MEAS, X, Id
import numpy as np

def RabiAmpq1(qubit: qbit, amps, phase=0, showPlot=False):
    """
    Variable amplitude Rabi nutation experiment.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel)
    amps : pulse amplitudes to sweep over (iterable)
    phase : phase of the pulse (radians)
    showPlot : whether to plot (boolean)
    """

    # Original:
    # seqs = [[Utheta(qubit, amp=amp, phase=phase), MEAS(qubit)] for amp in amps]

    # fileNames = compile_to_hardware(seqs, 'Rabi/Rabi')
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)

    seqs = []
    for amp in amps:
        seq = []
        seq.append(Utheta(qubit, amp=amp, phase=phase))
        seq.append(MEAS(qubit))
        seqs.append(seq)

    # Be sure to un-decorate this function to make it work without the
    # QGL2 compiler
    compileAndPlot(seqs, 'Rabi/Rabi', showPlot)

# For use with pyqgl2.main
# Note hard coded amplitudes and phase
@qgl2decl
def doRabiAmp() -> sequence:
    q = Qubit('q1')

    # FIXME: QGL2 can't handle evaluating this itself
#        for amp in np.linspace(0,1,11):
    for amp in [ 0. ,  0.1,  0.2,  0.3,  0.4,  0.5,  0.6,  0.7,  0.8,  0.9,  1. ]:
        init(q)
        Utheta(q, amp=amp, phase=0)
        MEAS(q)

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
    """

    # Original:
    # seqs = [[Utheta(qubit, amp=amp, phase=phase), MEAS(qubit)] for amp in amps]

    # fileNames = compile_to_hardware(seqs, 'Rabi/Rabi')
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)

    for amp in amps:
        init(qubit)
        Utheta(qubit, amp=amp, phase=phase)
        MEAS(qubit)

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    compileAndPlot('Rabi/Rabi', showPlot)

def RabiWidthq1(qubit: qbit, widths, amp=1, phase=0, shapeFun=QGL.PulseShapes.tanh, showPlot=False):
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

    # Original: 
    # seqs = [[Utheta(qubit, length=l, amp=amp, phase=phase, shapeFun=shapeFun), MEAS(qubit)] for l in widths]

    # fileNames = compile_to_hardware(seqs, 'Rabi/Rabi')
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)

    seqs = []
    for l in widths:
        seq = []
        seq.append(Utheta(qubit, length=l, amp=amp, phase=phase, shapeFun=shapeFun))
        seq.append(MEAS(qubit))
        seqs.append(seq)

    # Be sure to un-decorate this function to make it work without the
    # QGL2 compiler
    compileAndPlot(seqs, 'Rabi/Rabi', showPlot)

@qgl2decl
def doRabiWidth() -> sequence:
    q = Qubit("q1")

#        for l in np.linspace(0, 5e-6, 11):
    for l in [  0.00000000e+00,   5.00000000e-07,   1.00000000e-06,
                1.50000000e-06,   2.00000000e-06,   2.50000000e-06,
                3.00000000e-06,   3.50000000e-06,   4.00000000e-06,
                4.50000000e-06,   5.00000000e-06]:
        init(q)
        # FIXME: QGL2 loses the import needed for this QGL function
        Utheta(q, length=l, amp=1, phase=0, shapeFun=QGL.PulseShapes.tanh)
        MEAS(q)

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
    """

    # Original: 
    # seqs = [[Utheta(qubit, length=l, amp=amp, phase=phase, shapeFun=shapeFun), MEAS(qubit)] for l in widths]

    # fileNames = compile_to_hardware(seqs, 'Rabi/Rabi')
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)

    for l in widths:
        init(qubit)
        Utheta(qubit, length=l, amp=amp, phase=phase, shapeFun=shapeFun)
        MEAS(qubit)

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    compileAndPlot('Rabi/Rabi', showPlot)

def RabiAmp_NQubitsq1(qubits: qbit_list, amps, phase=0, showPlot=False,
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
    """
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
    if measChans is None:
        measChans = qubits
    seqs = []
    for amp in amps:
        seq = []
        pulses = [Utheta(q, amp=amp, phase=phase) for q in qubits]
        seq.append(reduce(operator.mul, pulses))
        seq.append(MEAS(*measChans))
        seqs.append(seq)

    if docals:
        seqs += create_cal_seqs(qubits, calRepeats, measChans=measChans)

    # Be sure to un-decorate this function to make it work without the
    # QGL2 compiler
    compileAndPlot(seqs, 'Rabi/Rabi', showPlot)

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
    """
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
    if measChans is None:
        measChans = qubits

    for amp in amps:
        with concur:
            for q,ct in zip(qubits, range(len(qubits))):
                init(q)
                Utheta(q, amp=amp, phase=phase)
                MEAS(measChans[ct])

    if docals:
        create_cal_seqs(qubits, calRepeats, measChans=measChans)

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    compileAndPlot('Rabi/Rabi', showPlot)

def RabiAmpPiq1(qubit: qbit, mqubit: qbit, amps, phase=0, showPlot=False):
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
    # Original:
    # seqs = [[X(mqubit),Utheta(qubit, amp=amp, phase=phase), X(mqubit), MEAS(mqubit)] for amp in amps]

    # fileNames = compile_to_hardware(seqs, 'Rabi/Rabi')
    # print(fileNames)

    # if showPlot:
    #     plotWin = plot_pulse_files(fileNames)
    #     return plotWin

    seqs = []
    for amp in amps:
        seq = []
        seq.append(X(mqubit))
        seq.append(Utheta(qubit, amp=amp, phase=phase))
        seq.append(X(mqubit))
        seq.append(MEAS(mqubit))
        seqs.append(seq)

    # Be sure to un-decorate this function to make it work without the
    # QGL2 compiler
    return compileAndPlot(seqs, 'Rabi/Rabi', showPlot)

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
    # Original:
    # seqs = [[X(mqubit),Utheta(qubit, amp=amp, phase=phase), X(mqubit), MEAS(mqubit)] for amp in amps]

    # fileNames = compile_to_hardware(seqs, 'Rabi/Rabi')
    # print(fileNames)

    # if showPlot:
    #     plotWin = plot_pulse_files(fileNames)
    #     return plotWin

    for amp in amps:
        with concur:
            init(qubit)
            init(mqubit)
        X(mqubit)
        Utheta(qubit, amp=amp, phase=phase)
        X(mqubit)
        MEAS(mqubit)

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    return compileAndPlot('Rabi/Rabi', showPlot)

def SingleShotq1(qubit: qbit, showPlot = False):
    """
    2-segment sequence with qubit prepared in |0> and |1>, useful for single-shot fidelity measurements and kernel calibration
    """
    # Original:
    # seqs = [[Id(qubit), MEAS(qubit)], [X(qubit), MEAS(qubit)]]
    # filenames = compile_to_hardware(seqs, 'SingleShot/SingleShot')
    # print(filenames)

    # if showPlot:
    #     plot_pulse_files(filenames)
    seqs = [
        [
            Id(qubit),
            MEAS(qubit)
        ],
        [
            X(qubit),
            MEAS(qubit)
        ]
    ]

    # Be sure to un-decorate this function to make it work without the
    # QGL2 compiler
    compileAndPlot(seqs, 'SingleShot/SingleShot', showPlot)

@qgl2decl
def SingleShot(qubit: qbit, showPlot = False):
    """
    2-segment sequence with qubit prepared in |0> and |1>, useful for single-shot fidelity measurements and kernel calibration
    """
    # Original:
    # seqs = [[Id(qubit), MEAS(qubit)], [X(qubit), MEAS(qubit)]]
    # filenames = compile_to_hardware(seqs, 'SingleShot/SingleShot')
    # print(filenames)

    # if showPlot:
    #     plot_pulse_files(filenames)
    init(qubit)
    Id(qubit)
    MEAS(qubit)
    init(qubit)
    X(qubit)
    MEAS(qubit)

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    compileAndPlot('SingleShot/SingleShot', showPlot)

def PulsedSpecq1(qubit: qbit, specOn = True, showPlot = False):
    """
    Measurement preceded by a qubit pulse if specOn = True
    """

    # Original:
    # qPulse = X(qubit) if specOn else Id(qubit)
    # seqs = [[qPulse, MEAS(qubit)]]
    # filenames = compile_to_hardware(seqs, 'Spec/Spec')
    # print(filenames)

    # if showPlot:
    #     plot_pulse_files(filenames)

    if specOn:
        seq = [X(qubit)]
    else:
        seq = [Id(qubit)]
    seq.append(MEAS(qubit))
    seqs = [seq]

    # Be sure to un-decorate this function to make it work without the
    # QGL2 compiler
    compileAndPlot(seqs, 'Spec/Spec', showPlot)

@qgl2decl
def PulsedSpec(qubit: qbit, specOn = True, showPlot = False):
    """
    Measurement preceded by a qubit pulse if specOn = True
    """

    # Original:
    # qPulse = X(qubit) if specOn else Id(qubit)
    # seqs = [[qPulse, MEAS(qubit)]]
    # filenames = compile_to_hardware(seqs, 'Spec/Spec')
    # print(filenames)

    # if showPlot:
    #     plot_pulse_files(filenames)

    init(qubit)
    if specOn:
        X(qubit)
    else:
        Id(qubit)
    MEAS(qubit)

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    compileAndPlot('Spec/Spec', showPlot)

def Swapq1(qubit: qbit, mqubit: qbit, delays, showPlot=False):
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
    # Original:
    # seqs = [[X(qubit), X(mqubit), Id(mqubit, d), MEAS(mqubit)*MEAS(qubit)] for d in delays] + create_cal_seqs((mqubit,qubit), 2, measChans=(mqubit,qubit))

    # fileNames = compile_to_hardware(seqs, 'Rabi/Rabi')
    # print(fileNames)

    # if showPlot:
    #     plotWin = plot_pulse_files(fileNames)
    #     return plotWin
    seqs = []
    for d in delays:
        seq = []
        seq.append(X(qubit))
        seq.append(X(mqubit))
        seq.append(Id(mqubit, d))
        seq.append(MEAS(mqubit)*MEAS(qubit))
        seqs.append(seq)

    seqs += create_cal_seqs((mqubit, qubit), 2)

    # Be sure to un-decorate this function to make it work without the
    # QGL2 compiler
    return compileAndPlot(seqs, 'Rabi/Rabi', showPlot)

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

    cal_seqs((mqubit, qubit), 2)

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    return compileAndPlot('Rabi/Rabi', showPlot)

# Imports for testing only
from QGL.Channels import Qubit, LogicalMarkerChannel, Measurement
from QGL import ChannelLibrary
from qgl2.qgl1 import Qubit
import numpy as np
from math import pi

@qgl2main
def main():
    # Set up 2 qbits, following model in QGL/test/test_Sequences

    # FIXME: Cannot use these in current QGL2 compiler, because
    # a: QGL2 doesn't understand creating class instances, and 
    # b: QGL2 currently only understands the fake Qbits
#    qg1 = LogicalMarkerChannel(label="q1-gate")
#    q1 = Qubit(label='q1', gateChan=qg1)
#    q1.pulseParams['length'] = 30e-9
#    q1.pulseParams['phase'] = pi/2
#    qg2 = LogicalMarkerChannel(label="q2-gate")
#    q2 = Qubit(label='q2', gateChan=qg2)
#    q2.pulseParams['length'] = 30e-9
#    q2.pulseParams['phase'] = pi/2

#    sTrig = LogicalMarkerChannel(label='slaveTrig')
#    dTrig = LogicalMarkerChannel(label='digitizerTrig')
#    Mq1 = '';
#    Mq1gate = LogicalMarkerChannel(label='M-q1-gate')
#    m = Measurement(label='M-q1', gateChan = Mq1gate, trigChan = dTrig)

#    ChannelLibrary.channelLib = ChannelLibrary.ChannelLibrary()
#    ChannelLibrary.channelLib.channelDict = {
#        'q1-gate': qg1,
#        'q1': q1,
#        'q2-gate': qg2,
#        'q2': q2,
#        'slaveTrig': sTrig,
#        'digitizerTrig': dTrig,
#        'M-q1': m,
#        'M-q1-gate': Mq1gate
#    }
#    ChannelLibrary.channelLib.build_connectivity_graph()

    # Use stub Qubits, but comment this out when running directly.
    q1 = Qubit("q1")
    q2 = Qubit("q2")

    RabiAmp(q1,  np.linspace(0, 5e-6, 11))
    RabiWidth(q1,  np.linspace(0, 5e-6, 11))
    RabiAmp_NQubits((q1, q2), np.linspace(0, 5e-6, 11))
    RabiAmpPi(q1, q2, np.linspace(0, 5e-6, 11))
    SingleShot(q1)
    PulsedSpec(q1)

if __name__ == "__main__":
    main()
