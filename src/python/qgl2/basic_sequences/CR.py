# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit

from QGL.PulsePrimitives import Id, X, MEAS, X90, flat_top_gaussian, echoCR
from QGL.Compiler import compile_to_hardware
from QGL.ChannelLibrary import EdgeFactory
from QGL.PulseSequencePlotter import plot_pulse_files

from .helpers import create_cal_seqs

@qgl2decl
def PiRabi(controlQ: qbit, targetQ: qbit, lengths, riseFall=40e-9, amp=1, phase=0, calRepeats=2, showPlot=False):
    """
    Variable length CX experiment.

    Parameters
    ----------
    controlQ : logical channel for the control qubit (LogicalChannel)
    targetQ: logical channel for the target qubit (LogicalChannel)
    lengths : pulse lengths of the CR pulse to sweep over (iterable)
    showPlot : whether to plot (boolean)

    Returns
    -------
    plotHandle : handle to plot window to prevent destruction
    """
    raise NotImplementedError("Not implemented")

    # Original:
    # CRchan = EdgeFactory(controlQ, targetQ)
    # seqs = [[Id(controlQ),
    #          flat_top_gaussian(CRchan, riseFall, amp=amp, phase=phase, length=l),
    #          MEAS(targetQ)*MEAS(controlQ)] for l in lengths] + \
    #     [[X(controlQ),
    #       flat_top_gaussian(CRchan, riseFall, amp=amp, phase=phase, length=l),
    #       X(controlQ),
    #       MEAS(targetQ)*MEAS(controlQ)] for l in lengths] + \
    #     create_cal_seqs([targetQ,controlQ], calRepeats, measChans=(targetQ,controlQ))

    # fileNames = compile_to_hardware(seqs, 'PiRabi/PiRabi')
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)

@qgl2decl
def EchoCRLen(controlQ: qbit, targetQ: qbit, lengths, riseFall=40e-9, amp=1, phase=0, calRepeats=2, showPlot=False):
    """
    Variable length CX experiment, with echo pulse sandwiched between two CR opposite-phase pulses.

    Parameters
    ----------
    controlQ : logical channel for the control qubit (LogicalChannel)
    targetQ: logical channel for the target qubit (LogicalChannel)
    lengths : pulse lengths of the CR pulse to sweep over (iterable)
    showPlot : whether to plot (boolean)

    Returns
    -------
    plotHandle : handle to plot window to prevent destruction
    """
    raise NotImplementedError("Not implemented")

    # Original: 
    # seqs = [[Id(controlQ)] + echoCR(controlQ, targetQ, length=l, phase=phase, riseFall=riseFall) + [Id(controlQ), MEAS(targetQ)*MEAS(controlQ)] \
    #         for l in lengths]+ [[X(controlQ)] + echoCR(controlQ, targetQ, length=l, phase= phase, riseFall=riseFall) + [X(controlQ), MEAS(targetQ)*MEAS(controlQ)] \
    #                             for l in lengths] + create_cal_seqs((targetQ,controlQ), calRepeats, measChans=(targetQ,controlQ))

    # fileNames = compile_to_hardware(seqs, 'EchoCR/EchoCR')
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)

@qgl2decl
def EchoCRPhase(controlQ: qbit, targetQ: qbit, phases, riseFall=40e-9, amp=1, length=100e-9, calRepeats=2, showPlot=False):
    """
    Variable phase CX experiment, with echo pulse sandwiched between two CR opposite-phase pulses.

    Parameters
    ----------
    controlQ : logical channel for the control qubit (LogicalChannel)
    CRchan: logical channel for the cross-resonance pulse (LogicalChannel) 
    phases : pulse phases of the CR pulse to sweep over (iterable)
    showPlot : whether to plot (boolean)

    Returns
    -------
    plotHandle : handle to plot window to prevent destruction
    """
    raise NotImplementedError("Not implemented")

    # Original:
    # seqs = [[Id(controlQ)] + echoCR(controlQ, targetQ, length=length, phase=ph, riseFall=riseFall) + [X90(targetQ)*Id(controlQ), MEAS(targetQ)*MEAS(controlQ)] \
    #         for ph in phases]+[[X(controlQ)] + echoCR(controlQ, targetQ, length=length, phase= ph, riseFall = riseFall) + [X90(targetQ)*X(controlQ), MEAS(targetQ)*MEAS(controlQ)] \
    #                            for ph in phases]+create_cal_seqs((targetQ,controlQ), calRepeats, measChans=(targetQ,controlQ))

    # fileNames = compile_to_hardware(seqs, 'EchoCR/EchoCR')
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)
