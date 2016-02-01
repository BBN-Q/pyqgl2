# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit

from QGL.PulsePrimitives import X, Id, MEAS, X90, U90
from QGL.Compiler import compile_to_hardware
from QGL.PulseSequencePlotter import plot_pulse_files

from .helpers import create_cal_seqs

from scipy.constants import pi

@qgl2decl
def InversionRecovery(qubit: qbit, delays, showPlot=False, calRepeats=2, suffix=False):
    """
    Inversion recovery experiment to measure qubit T1

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    delays : delays after inversion before measurement (iterable; seconds)
    showPlot : whether to plot (boolean)
    calRepeats : how many repetitions of calibration pulses (int)

    Returns
    -------
    plotHandle : handle to plot window to prevent destruction
    """
    raise NotImplementedError("Not implemented")

    # Original: 
    # # Create the basic sequences
    # seqs = [[X(qubit), Id(qubit, d), MEAS(qubit)] for d in delays]

    # # Tack on the calibration scalings
    # seqs += create_cal_seqs((qubit,), calRepeats)

    # fileNames = compile_to_hardware(seqs, 'T1'+('_'+qubit.label)*suffix+'/T1'+('_'+qubit.label)*suffix)
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)

@qgl2decl
def Ramsey(qubit: qbit, pulseSpacings, TPPIFreq=0, showPlot=False, calRepeats=2, suffix=False):
    """
    Variable pulse spacing Ramsey (pi/2 - tau - pi/2) with optional TPPI.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    pulseSpacings : pulse spacings (iterable; seconds)
    TPPIFreq : frequency for TPPI phase updates of second Ramsey pulse (Hz)
    showPlot : whether to plot (boolean)
    calRepeats : how many repetitions of calibration pulses (int)

    Returns
    -------
    plotHandle : handle to plot window to prevent destruction
    """
    raise NotImplementedError("Not implemented")

    # Original:
    # # Create the phases for the TPPI
    # phases = 2*pi*TPPIFreq*pulseSpacings

    # # Create the basic Ramsey sequence
    # seqs = [[X90(qubit), Id(qubit, d), U90(qubit, phase=phase), MEAS(qubit)] 
    #         for d,phase in zip(pulseSpacings, phases)]

    # # Tack on the calibration scalings
    # seqs += create_cal_seqs((qubit,), calRepeats)

    # fileNames = compile_to_hardware(seqs, 'Ramsey'+('_'+qubit.label)*suffix+'/Ramsey'+('_'+qubit.label)*suffix)
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)

