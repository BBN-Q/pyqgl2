# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit

from QGL.PulsePrimitives import Id, X, MEAS, X90, flat_top_gaussian, echoCR
from QGL.Compiler import compile_to_hardware
from QGL.ChannelLibrary import EdgeFactory
from QGL.PulseSequencePlotter import plot_pulse_files

from .helpers import create_cal_seqs
from .new_helpers import addMeasPulses, addCalibration, compileAndPlot

@qgl2decl
def PiRabi(controlQ: qbit, targetQ: qbit, lengths, riseFall=40e-9, amp=1, phase=0, calRepeats=2, showPlot=False):
    """
    Variable length CX experiment.

    Parameters
    ----------
    controlQ : logical channel for the control qubit (LogicalChannel)
    targetQ: logical channel for the target qubit (LogicalChannel)
    lengths : pulse lengths of the CR pulse to sweep over (iterable)
    riseFall
    amp
    phase
    calRepeats
    showPlot : whether to plot (boolean)
    """

    # EdgeFactory returns a channel (ie qubit)
    # Note we are not redoing that one
    CRchan = EdgeFactory(controlQ, targetQ)

    # flat_top_gaussian is an addition of 3 UTheta pulses

    # The for l in lengths repeats this sequence len(lengths) times but with a diff value
    # - FIXME: is that a variant on my repeat helper I can/should generalize?

    seqs1 = []
    seqs2 = []
    for l in lengths:
        gaussian = flat_top_gaussian(CRchan, riseFall, amp=amp, phase=phase, length=l)
        seqs1.append(
            [Id(controlQ),
             gaussian])
        seqs2.append(
            [X(controlQ),
             gaussian,
             X(controlQ)])

    seqs = addMeasPulses(seqs1 + seqs2, [targetQ, controlQ])

    seqs = addCalibration(seqs, [targetQ, controlQ], calRepeats)

    compileAndPlot(seqs, 'PiRabi/PiRabi', showPlot)

@qgl2decl
def EchoCRLen(controlQ: qbit, targetQ: qbit, lengths, riseFall=40e-9, amp=1, phase=0, calRepeats=2, showPlot=False):
    """
    Variable length CX experiment, with echo pulse sandwiched between two CR opposite-phase pulses.

    Parameters
    ----------
    controlQ : logical channel for the control qubit (LogicalChannel)
    targetQ: logical channel for the target qubit (LogicalChannel)
    lengths : pulse lengths of the CR pulse to sweep over (iterable)
    riseFall
    amp
    phase
    calRepeats
    showPlot : whether to plot (boolean)
    """
    # Original: 
    # seqs = [[Id(controlQ)] + echoCR(controlQ, targetQ, length=l, phase=phase, riseFall=riseFall) + [Id(controlQ), MEAS(targetQ)*MEAS(controlQ)] \
    #         for l in lengths]+ [[X(controlQ)] + echoCR(controlQ, targetQ, length=l, phase= phase, riseFall=riseFall) + [X(controlQ), MEAS(targetQ)*MEAS(controlQ)] \
    #                             for l in lengths] + create_cal_seqs((targetQ,controlQ), calRepeats, measChans=(targetQ,controlQ))

    # FIXME: These need to be functions?

    seqs1 = []
    seqs2 = []
    for l in lengths:
        ecr = echoCR(controlQ, targetQ, length=l, phase=phase, riseFall=riseFall)
        seqs1.append(
            [Id(controlQ)] +
            ecr +
            [Id(controlQ)])
        seqs2.append(
            [X(controlQ)] +
            ecr +
            [X(controlQ)])

    seqs = addMeasPulses(seqs1 + seqs2, [targetQ, controlQ])

    seqs = addCalibration(seqs, [targetQ, controlQ], calRepeats)

    compileAndPlot(seqs, 'EchoCR/EchoCR', showPlot)

@qgl2decl
def EchoCRPhase(controlQ: qbit, targetQ: qbit, phases, riseFall=40e-9, amp=1, length=100e-9, calRepeats=2, showPlot=False):
    """
    Variable phase CX experiment, with echo pulse sandwiched between two CR opposite-phase pulses.

    Parameters
    ----------
    controlQ : logical channel for the control qubit (LogicalChannel)
    targetQ :
    phases : pulse phases of the CR pulse to sweep over (iterable)
    riseFall
    amp
    length
    calRepeats
    showPlot : whether to plot (boolean)
    """
    # Original:
    # seqs = [[Id(controlQ)] + echoCR(controlQ, targetQ, length=length, phase=ph, riseFall=riseFall) + [X90(targetQ)*Id(controlQ), MEAS(targetQ)*MEAS(controlQ)] \
    #         for ph in phases]+[[X(controlQ)] + echoCR(controlQ, targetQ, length=length, phase= ph, riseFall = riseFall) + [X90(targetQ)*X(controlQ), MEAS(targetQ)*MEAS(controlQ)] \
    #                            for ph in phases]+create_cal_seqs((targetQ,controlQ), calRepeats, measChans=(targetQ,controlQ))

    seqs1 = []
    seqs2 = []

    # FIXME: Do a with concur for those 3rd elements, and make everything else into functions

    for ph in phases:
        ecr = echoCR(controlQ, targetQ, length=length, phase=ph, riseFall=riseFall)
        seqs1.append(
            [Id(controlQ)] +
            ecr + \
            [X90(targetQ)*Id(controlQ)])

        seqs2.append(
            [X(controlQ)]  +
            ecr + \
            [X90(targetQ)* X(controlQ)])

    seqs = seqs1 + seqs2
    seqs = addMeasPulses(seqs, [targetQ, controlQ])
    seqs = addCalibration(seqs, [targetQ, controlQ], calRepeats)

    compileAndPlot(seqs, 'EchoCR/EchoCR', showPlot)
