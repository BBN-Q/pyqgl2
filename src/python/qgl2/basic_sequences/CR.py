# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit, qgl2main, concur

from QGL.PulsePrimitives import Id, X, MEAS, X90, flat_top_gaussian, echoCR
from QGL.Compiler import compile_to_hardware
from QGL.ChannelLibraries import EdgeFactory

from qgl2.basic_sequences.helpers import create_cal_seqs
from qgl2.basic_sequences.new_helpers import addMeasPulses, addCalibration, compileAndPlot, measConcurrently
from qgl2.util import init

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

    # FIXME: QGL2 doesn't understand these for loops yet

    # Sequence 1: Id(control), gaussian(l), measure both
    for l in lengths:
        with concur:
            init(controlQ)
            init(targetQ)
        Id(controlQ)
        flat_top_gaussian(CRchan, riseFall, amp=amp, phase=phase, length=l)
        measConcurrently([targetQ, controlQ])

    # Sequence 2: X(control), gaussian(l), X(control), measure both
    for l in lengths:
        with concur:
            init(controlQ)
            init(targetQ)
        X(controlQ)
        flat_top_gaussian(CRchan, riseFall, amp=amp, phase=phase, length=l)
        X(controlQ)
        measConcurrently([targetQ, controlQ])

    # Then do calRepeats calibration sequences
    create_cal_seqs([targetQ, controlQ], calRepeats)

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    compileAndPlot('PiRabi/PiRabi', showPlot)

def PiRabiq1(controlQ: qbit, targetQ: qbit, lengths, riseFall=40e-9, amp=1, phase=0, calRepeats=2, showPlot=False):
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

    # Be sure to un-decorate this function to make it work without the
    # QGL2 compiler
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

    # Sequence1:
    for l in lengths:
        with concur:
            init(controlQ)
            init(targetQ)
        Id(controlQ)
        echoCR(controlQ, targetQ, length=l, phase=phase,
               riseFall=riseFall)
        Id(controlQ)
        measConcurrently([targetQ, controlQ])

    # Sequence 2
    for l in lengths:
        with concur:
            init(controlQ)
            init(targetQ)
        X(controlQ)
        echoCR(controlQ, targetQ, length=l, phase=phase,
               riseFall=riseFall)
        X(controlQ)
        measConcurrently([targetQ, controlQ])

    # Then do calRepeats calibration sequences
    create_cal_seqs([targetQ, controlQ], calRepeats)

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    compileAndPlot('EchoCR/EchoCR', showPlot)

def EchoCRLenq1(controlQ: qbit, targetQ: qbit, lengths, riseFall=40e-9, amp=1, phase=0, calRepeats=2, showPlot=False):
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

    # Be sure to un-decorate this function to make it work without the
    # QGL2 compiler
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

    # Sequence 1
    for ph in phases:
        with concur:
            init(controlQ)
            init(targetQ)
        Id(controlQ)
        echoCR(controlQ, targetQ, length=length, phase=ph,
               riseFall=riseFall)
        with concur:
            X90(targetQ)
            Id(controlQ)
        measConcurrently([targetQ, controlQ])

    # Sequence 2
    for ph in phases:
        with concur:
            init(controlQ)
            init(targetQ)
        X(controlQ)
        echoCR(controlQ, targetQ, length=length, phase=ph,
               riseFall=riseFall)
        with concur:
            X90(targetQ)
            X(controlQ)
        measConcurrently([targetQ, controlQ])

    # Then do calRepeats calibration sequences
    create_cal_seqs([targetQ, controlQ], calRepeats)

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    compileAndPlot('EchoCR/EchoCR', showPlot)

def EchoCRPhaseq1(controlQ: qbit, targetQ: qbit, phases, riseFall=40e-9, amp=1, length=100e-9, calRepeats=2, showPlot=False):
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

    # Be sure to un-decorate this function to make it work without the
    # QGL2 compiler
    compileAndPlot(seqs, 'EchoCR/EchoCR', showPlot)

# Imports for testing only
from qgl2.qgl1 import QubitFactory, Qubit
from QGL.Channels import Qubit, LogicalMarkerChannel, Edge
import QGL.ChannelLibraries as ChannelLibraries
import numpy as np
from math import pi

@qgl2main
def main():
    # Set up 2 qbits, following model in QGL/test/test_Sequences

    # FIXME: Cannot use these in current QGL2 compiler, because
    # a: QGL2 doesn't understand creating class instances, and 
    # b: QGL2 currently only understands the fake Qbits
#    qg1 = LogicalMarkerChannel(label="q1-gate")
#    q1 = Qubit(label='q1', gate_chan=qg1)
#    q1.pulseParams['length'] = 30e-9
#    q1.pulseParams['phase'] = pi/2

#    qg2 = LogicalMarkerChannel(label="q2-gate")
#    q2 = Qubit(label='q2', gate_chan=qg2)
#    q2.pulseParams['length'] = 30e-9
#    q2.pulseParams['phase'] = pi/2

    # this block depends on the existence of q1 and q2
#    crgate = LogicalMarkerChannel(label='cr-gate')

#    cr = Edge(label="cr", source = q1, target = q2, gate_chan = crgate )
#    cr.pulseParams['length'] = 30e-9
#    cr.pulseParams['phase'] = pi/4

#    ChannelLibraries.channelLib = ChannelLibraries.ChannelLibraries()
#    ChannelLibraries.channelLib.channelDict = {
#        'q1-gate': qg1,
#        'q1': q1,
#        'q2-gate': qg2,
#        'q2': q2,
#        'cr-gate': crgate,
#        'cr': cr
#    }
#    ChannelLibraries.channelLib.build_connectivity_graph()

    # Use stub Qubits, but comment this out when running directly.
    q1 = QubitFactory("q1")
    q2 = QubitFactory("q2")

    print("Run PiRabi")
    PiRabi(q1, q2, np.linspace(0, 4e-6, 11))
    print("Run EchoCRLen")
    EchoCRLen(q1, q2, np.linspace(0, 2e-6, 11))
    print("Run EchoCRPhase")
    EchoCRPhase(q1, q2, np.linspace(0, pi/2, 11))

if __name__ == "__main__":
    main()
