# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit_list, qgl2main, concur

from QGL.PulsePrimitives import Id, MEAS, X
from QGL.Compiler import compile_to_hardware
from QGL.PulseSequencePlotter import plot_pulse_files
from QGL.ControlFlow import qif, qwait

from .helpers import create_cal_seqs
from .new_helpers import compileAndPlot, init

from functools import reduce
from itertools import product
import operator

# Note that measChans should have a default value that is identical to qubits
def Resetq1_orig(qubits: qbit_list, measDelay = 1e-6, signVec = None,
          doubleRound = True, buf = 30e-9, showPlot=False, measChans: qbit_list = None, docals=True, calRepeats=2):
    """
    Variable amplitude Rabi nutation experiment for an arbitrary number of qubits simultaneously

    Parameters
    ----------
    qubits : tuple of logical channels to implement sequence (LogicalChannel)
    measDelay : delay between end of measuerement and LOADCMP
    signVec : conditions for feedback. List of 0 (flip if signal is above threshold) and 1 (flip if below) for each qubit. Default = 0 for all qubits
    doubleRound : if true, double round of feedback
    showPlot : whether to plot (boolean)
    measChans : tuble of qubits to be measured (LogicalChannel)
    docals, calRepeats: enable calibration sequences, repeated calRepeats times
    """

    # This will produce 2^numQubits sequences, such that in each
    # sequence we try a different combination of the bits in the
    # comparison register.
    # Each sequence does some calibration like pulses, measurements,
    # then a bunch of qifs with all the possible different masks, then
    # measure again.
    # And if doubleRound is set, do it again.

    # Note that the if clause to the qif depends on the sign of the
    # qubit: Default is ID, X like in calibration sequences.

    # Original:
    # if measChans is None:
    #     measChans = qubits

    # if signVec == None:
    #     signVec = [0]*len(qubits)

    # states = create_cal_seqs(qubits,1,measChans=measChans)
    # FbSet = [Id, X]
    # FbSet2 = [X, Id]
    # FbGates = []

    # for count in range(len(qubits)):
    #     FbGates += [FbSet] if signVec[count]==0 else [FbSet2]
    # FbSeq = [reduce(operator.mul, [p(q) for p,q in zip(pulseSet, qubits)]) for pulseSet in product(*FbGates)]
    # seqs = [state + [MEAS(*measChans), Id(qubits[0],measDelay), qwait('CMP'), Id(qubits[0],buf)] + [branch for b in [qif(fbcount,[FbSeq[count]]) for fbcount in range(len(states))] for branch in b] + [MEAS(*measChans)] for count, state in enumerate(states)]

    # if doubleRound:
    #     seqs = [seq + [Id(qubits[0],measDelay), qwait('CMP'), Id(qubits[0],buf)] + [branch for b in [qif(fbcount,[FbSeq[count]]) for fbcount in range(2**len(qubits))] for branch in b] + [MEAS(*measChans)] for seq in seqs]
    # print(seqs[0])
    # if docals:
    #     seqs += create_cal_seqs(qubits, calRepeats, measChans=measChans)

    # fileNames = compile_to_hardware(seqs, 'Reset/Reset')

    # if showPlot:
    #     plot_pulse_files(fileNames)


    # signVec determines the order that the product(Id, X) sets end up
    # in
    # That is, the product() thing means we'll do all combos of Id,X
    # for each qubit, but we vary the order of those

    if measChans is None:
        measChans = qubits

    # Calibrate sequence for the qubits - there will be 2^len(qubits)
    # states
    # Note that the calibration sequence is the un-inverted entry in
    # FbGates below, and there are as many calibration sequences as
    # there are entries in FbSeq
    # Each sequence in the final result will start with one of these
    # calibration sequences
    calSeqs = create_cal_seqs(qubits,1,measChans=measChans)

    # This next block creates something called FbSeq. This is like
    # calSeqs, except that for some qubits the "calibration sequence"
    # is inverted (X, ID).
    # Each of these becomes the if pulse in the qif() clauses in each
    # sequence in the final result.
    # There will be 2^numQubits of these - 1 per final sequence

    # Default signVec to 0 for all qubits
    if signVec == None:
        signVec = [0]*len(qubits)

    # Collect the gates in 1 sequence
    FbGates = []

    # Sometimes state assignments are 'flipped'. Hence this code.
    # Create the FbGates sequences: Each of 2 gates per qubit, based on the
    # signVec
    # Note that QGL2 does not yet handle this kind of function reference
    for count in range(len(qubits)):
        if signVec[count] == 0:
            FbGates += [[Id, X]] # This is the order used in calibration
        else:
            FbGates += [[X, Id]] # This is inverted

    # This will be a sequence of concurrent pulses (in each, 1 per
    # qubit)
    # of length 2^# qubits
    # This is used as the If clause of the qifs below
    # So one of these per sequence in the final result
    FbSeq = []

    # Each set is length of # of qubits
    # But this is full set of combinations of Id and X in the order
    # determined by signVec
    for pulseSet in product(*FbGates):
        # Each entry is concurrently doing a pulse on each qubit
        allPulsePairs = []
        for pulse, qubit in zip(pulseSet, qubits):
            allPulsePairs.append(pulse(qubit))
        FbSeq.append(
            reduce(operator.mul, allPulsePairs)
        )

    # FbSeq is now a sequence of concurrent pulses (in each, Id
    # or X per qubit), of length 2^# qubits
    # EG for 2 qubits of opposite signVec, it gives:
    # [Id(q1)*X(q2), Id(q1)*Id(q2), X(q1)*X(q2), X(q1)*Id(q2)]

    # FbSeq is of same length as calSeqs: 2^#qubits, and made of
    # similar pulses - though the calibration sequences include MEAS pulses

    # seqs is the final result list of sequences
    seqs = []
    # For each calibrate sequence create an element in seqs
    # calSeq is aka state - but why?
    for count, calSeq in enumerate(calSeqs):
        # qifs: for each calibrate there's a qif using that index as the
        # mask, with the test (if clause) being the matching pulse in FbSeq for
        # this calibrate sequence
        # Put another way, we call qif on every mask from 1 to
        # 2^numQubits, each time using the Pulse from FbSeq for this
        # sequence / calibration sequence in the final result.

        # Note a qif is a sequence of pulses, really
        qElse = [FbSeq[count]]
        qifs = []
        for fbcount in range(2**len(qubits)):
            qifs.append(qif(fbcount, qElse))

        # Tease apart the pieces of the qifs and add those all to a
        # new branches sequence. That is, turn [[1, 2, 3], [4, 5, 6]]
        # into [1, 2, 3, 4, 5, 6]
        branches = []
        # qifInstance aka b
        for qifInstance in qifs:
            for branch in qifInstance:
                branches.append(branch)

        # Now create the sequence
        seqs.append(
            calSeq +
            [
                MEAS(*measChans),
                Id(qubits[0],measDelay),
                qwait('CMP'),
                Id(qubits[0],buf)
            ] +
            branches +
            [MEAS(*measChans)]
        )

    # if doubleRound:
    #     seqs = [seq + [Id(qubits[0],measDelay), qwait('CMP'), Id(qubits[0],buf)] + [branch for b in [qif(fbcount,[FbSeq[count]]) for fbcount in range(2**len(qubits))] for branch in b] + [MEAS(*measChans)] for seq in seqs]
    # print(seqs[0])

    # If doubling, add to each sequence Id, qwait, Id, a bunch of
    # qifs, and some concurrent MEAS calls
    # That is, roughly double each sequence, but skip the initial MEAS
    # and the qifs all use a single if clause.
    if doubleRound:
        # FIXME: This 'count' is just the last count from the last
        # calibrate sequence? Really? Seems arbitrary whether this is
        # IdX or XId - does it not matter?
        # Other than that, the qifs created here are idential to the
        # last set of qifs created above
        qElse = [FbSeq[count]]

        qifs = []
        for fbcount in range(2**len(qubits)):
            qifs.append(qif(fbcount, qElse))

        # Tease apart the pieces of the qifs and add those all to a
        # new branches sequence, flattening a list of lists into a
        # single list
        branches = []
        # qifInstance aka b
        for qifInstance in qifs:
            for branch in qifInstance:
                branches.append(branch)

        # Now add the new pulses to each sequence - not just the last one
        for seq in seqs:
            seq.append(
                    [
                        Id(qubits[0], measDelay),
                        qwait('CMP'),
                        Id(qubits[0], buf)
                    ] +
                    branches +
                    [MEAS(*measChans)]
                )

    # If we're doing calibration too, add that at the very end
    # - another 2^numQubits * calRepeats sequences
    if docals:
        seqs += create_cal_seqs(qubits, calRepeats, measChans=measChans)

    # Be sure to un-decorate this function to make it work without the
    # QGL2 compiler
    compileAndPlot(seqs, 'Reset/Reset', showPlot)

@qgl2decl
def qreset(qubits: qbit_list, measDelay, signVec, buf, measChans):
    # Produces a sequence like:
    # Id(qubits[0], measDelay)
    # qwait(CMP)
    # Id(qubits[0], buf)
    # 2^numQubits qif calls, 1 per possible comparison value
    # MEAS*MEAS

    # For each qubit, build the set of feedback actions to perform when
    # receiving a zero or one in the comparison register
    # We'll cover all combinations of Id,X on each qubit
    # ordering Id,X appropriately based on signVec, and will supply
    # the if clause in the qifs

    # Produce a list of sets of pulses to do concurrently
    # Each entry in list has numQubits entries
    # We don't actually evaluate the gates here - do it later when in
    # the right place
    # [
    #     [[gate, q1],[gate2, q2]],
    #     [[gate, q1], [g,q2]],
    #     [[gate, q1], [g, q2]]
    # ]
    # The goal is to produce
    # a sequence of concurrent pulses (in each, Id
    # or X per qubit), of length 2^# qubits
    # EG for 2 qubits of opposite signVec, it gives:
    # [Id(q1)*X(q2), Id(q1)*Id(q2), X(q1)*X(q2), X(q1)*Id(q2)]
    # FIXME: Is qgl2decl un-necessary here?
    @qgl2decl
    def makePulsesList(qubits: qbit_list, signVec):
        FbGates = []
        for count, q in enumerate(qubits):
            fbg = []
            if signVec[count] == 0:
                for gate in [Id, X]:
                    fbg.append([gate, q])
            else: # inverted logic for when qubit state is flipped
                for gate in [X, Id]:
                    fbg.append([gate, q])
            FbGates.append(fbg)
        FbSeq = []
        for pulseSet in product(*FbGates):
            FbSeq.append(pulseSet)
        return FbSeq

    # Make the pulses list once
    pulsesList = makePulsesList(qubits, signVec)

    # Pick the proper pulseSet from the pulsesList
    # And evaluate the set concurrently
    @qgl2decl
    def ifClause(count, pulsesList):
        with concur:
            for pq in pulsesList[count]:
                pq[0](pq[1])

    # First wait for the measurement to have
    # happened to all qubits, account for physical delays
    Id(qubits[0], measDelay)
    # Load register
    qwait('CMP')
    # Wait for the chamber to quiet down and be
    # ready for more calls
    Id(qubits[0], buf)

    # Create a branch for each possible comparison value
    # Each qif / branch uses a different mask, and the corresponding
    # pair of gates (created above)
    for count in range(2**len(qubits)):
        qif(count, ifClause(count, pulsesList))

    with concur:
        for q in measChans:
            MEAS(q)

def qresetq1(qubits: qbit_list, measDelay, signVec, buf, measChans):
    # Produces a sequence like:
    # Id(qubits[0], measDelay)
    # qwait(CMP)
    # Id(qubits[0], buf)
    # 2^numQubits qif calls, 1 per possible comparison value
    # MEAS*MEAS

    # Note that old code did the MEAS on measChans and this is on qubits

    # For each qubit, build the set of feedback actions to perform when
    # receiving a zero or one in the comparison register
    FbGates = []
    # FbSeq will cover all combinations of Id,X on each qubit,
    # ordering Id,X appropriately based on signVec, and will supply
    # the if clause in the qifs
    for count, q in enumerate(qubits):
        if signVec[count] == 0:
            FbGates.append([gate(q) for gate in [Id, X]])
        else: # inverted logic for when qubit state is flipped
            FbGates.append([gate(q) for gate in [X, Id]])

    FbSeq = []
    for pulseSet in product(*FbGates):
        FbSeq.append(reduce(operator.mul, pulseSet))
#    FbSeq = [reduce(operator.mul, pulseSet) for pulseSet in product(*FbGates)]

    # FbSeq is now a sequence of concurrent pulses (in each, Id
    # or X per qubit), of length 2^# qubits
    # EG for 2 qubits of opposite signVec, it gives:
    # [Id(q1)*X(q2), Id(q1)*Id(q2), X(q1)*X(q2), X(q1)*Id(q2)]

    # Load register
    seq = [Id(qubits[0], measDelay), qwait('CMP'), Id(qubits[0], buf)]

    # Create a branch for each possible comparison value
    # Each qif / branch uses a different mask, and the corresponding
    # pair of gates (created above)
    for count in range(2**len(qubits)):
        seq += qif(count, [FbSeq[count]])
    seq += [MEAS(*tuple(measChans))]

    return seq

# This version from Blake who says it fixes bugs in the original
# Note that measChans should have a default value that is identical to
# qubits
@qgl2decl
def Reset(qubits: qbit_list, measDelay = 1e-6, signVec = None,
           doubleRound = True, buf = 30e-9, showPlot=False,
           measChans: qbit_list = None, docals=True, calRepeats=2):
    """
    Variable amplitude Rabi nutation experiment for an arbitrary number of qubits simultaneously

    Parameters
    ----------
    qubits : tuple of logical channels to implement sequence (LogicalChannel)
    measDelay : delay between end of measuerement and LOADCMP
    signVec : conditions for feedback. List of 0 (flip if signal is above threshold) and 1 (flip if below) for each qubit. Default = 0 for all qubits
    doubleRound : if true, double round of feedback
    showPlot : whether to plot (boolean)
    measChans : tuble of qubits to be measured (LogicalChannel)
    docals, calRepeats: enable calibration sequences, repeated calRepeats times
    """
    # This will produce 2^numQubits sequences, such that in each
    # sequence we try a different combination of the bits in the
    # comparison register.
    # Each sequence does some calibration-like pulses, measurements,
    # then a bunch of qifs with all the possible different masks, then
    # measure again.
    # And if doubleRound is set, do it again.
    # This program tests the result of "resetting" starting from all
    # computational basis states

    # Note that the if clause to the qif depends on the sign of the
    # qubit: Default is ID, X like in calibration sequences.
    if measChans is None:
        measChans = qubits

    # signVec defaults to 0
    # If it is 1 then the state is 'flipped' and we'll
    # reverse the corresponding (Id, X) pulses
    if signVec == None:
        signVec = [0]*len(qubits)
    signVec = tuple(signVec)

    initialPulses = [Id, X]
    initialPulsesList = tuple(product(initialPulses, repeat=len(qubits)))

    @qgl2decl
    def doOneInitialPulse(pulseSet):
        # then do each pulse on each qubit concurrently
        # Get all combinations of the pulses and qubits
        # doing the pulse on the qubit
        # Do the pulses concurrently for this pulseSet
        with concur:
            for pulse,qubit in zip(pulseSet, qubits):
                pulse(qubit)
        # Add on the measurement pulses (done concurrently)
        with concur:
            for chan in measChans:
                MEAS(chan)

    # There will be 2^numQubits sequences
    for count in range(2**len(qubits)):
        # Each sequence will start with what looks like a calibration
        # sequence
        # Really we're just re-using that function because it creates all
        # computation basis states followed by measurements.

        # Do the initial pulse for this entry
        doOneInitialPulse(initialPulsesList[count])

        # After that, each will have a standard block (see qreset)
        qreset(qubits, measDelay, signVec, buf, measChans)

        # If doubling, add to each sequence
        # The same standard block from above
        if doubleRound:
            qreset(qubits, measDelay, signVec, buf, measChans)

        # Add a final qwait('CMP') (bug in original implementation of Reset)
        qwait('CMP')

    # If we're doing calibration too, add that at the very end
    # - another 2^numQubits * calRepeats sequences
    if docals:
        create_cal_seqs(qubits, calRepeats, measChans=measChans)

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    compileAndPlot('Reset/Reset', showPlot)

# This version from Blake who says it fixes bugs in the original
# Note that measChans should have a default value that is identical to qubits
def Resetq1(qubits: qbit_list, measDelay = 1e-6, signVec = None,
           doubleRound = True, buf = 30e-9, showPlot=False,
           measChans: qbit_list = None, docals=True, calRepeats=2):
    """
    Variable amplitude Rabi nutation experiment for an arbitrary number of qubits simultaneously

    Parameters
    ----------
    qubits : tuple of logical channels to implement sequence (LogicalChannel)
    measDelay : delay between end of measuerement and LOADCMP
    signVec : conditions for feedback. List of 0 (flip if signal is above threshold) and 1 (flip if below) for each qubit. Default = 0 for all qubits
    doubleRound : if true, double round of feedback
    showPlot : whether to plot (boolean)
    measChans : tuble of qubits to be measured (LogicalChannel)
    docals, calRepeats: enable calibration sequences, repeated calRepeats times
    """
    # This will produce 2^numQubits sequences, such that in each
    # sequence we try a different combination of the bits in the
    # comparison register.
    # Each sequence does some calibration-like pulses, measurements,
    # then a bunch of qifs with all the possible different masks, then
    # measure again.
    # And if doubleRound is set, do it again.
    # This program tests the result of "resetting" starting from all
    # computational basis states

    # Note that the if clause to the qif depends on the sign of the
    # qubit: Default is ID, X like in calibration sequences.
    if measChans is None:
        measChans = qubits

    # signVec defaults to 0
    # If it is 1 then the state is 'flipped' and we'll
    # reverse the corresponding (Id, X) pulses
    if signVec == None:
        signVec = [0]*len(qubits)
    signVec = tuple(signVec)

    # Collect the final result sequences here
    seqs = []

    # Each sequence will start with what looks like a calibration
    # sequence
    # Really we're just re-using that function because it creates all
    # computation basis states followed by measurements.
    # After that, each will have a standard block (see qreset)
    # There will be 2^numQubits sequences
    for prep in create_cal_seqs(qubits, 1):
        seqs.append(
            prep +
            [qresetq1(qubits, measDelay, signVec, buf, measChans)]
            )

    # If doubling, add to each sequence
    # The same standard block from above
    if doubleRound:
        for seq in seqs:
            seq.append(qresetq1(qubits, measDelay, signVec, buf, measChans))

    # Add a final qwait('CMP') (bug in original implementation of Reset)
    for seq in seqs:
        seq.append(qwait('CMP'))

    # If we're doing calibration too, add that at the very end
    # - another 2^numQubits * calRepeats sequences
    if docals:
        seqs += create_cal_seqs(qubits, calRepeats, measChans=measChans)

    # Be sure to un-decorate this function to make it work without the
    # QGL2 compiler
    compileAndPlot(seqs, 'Reset/Reset', showPlot)

@qgl2decl
def qreset_Blake2(q: qbit, measDelay, buf, measSign):
    m = MEAS(q)
    # FIXME: In future, QGL2
    # Compiler inserts Id(measDelay+buf) or just buf if HW is fixed,
    # plus qwait
    if m * measSign == 1:
        X(q)

@qgl2decl
def qreset_Blake(q: qbit, measDelay, buf, measSign):
    m = MEAS(q)
    Id(q, measDelay) # Wait to be sure signal reaches all qbits

    # a new instruction Blake invented to ensure
    # result is loaded into the register
    qwait(q, 'CMP')

    # Wait for the photons in the chamber to decay
    Id(q, buf)
    if m * measSign == 1:
        X(q)


# FIXME:
# How to create intermediate versions of Reset?
# 1: Do qwait(CMP) instead of qwait(q, CMP)
# 2: Translate signVec 0 (old style input) to 1 and non-0 to -1
# 3:include measChans in method sig but ignore it
# 4: But the big one is replacing the qifs with if m & measSign: not
# clear how to handle that

# Note no measChans arg - it is always the qubits
# Also note signVec is no -1 or 1, not 0 and not 0
# Those 2 things make this Reset() incompatible with the QGL1 version
@qgl2decl
def Reset_Blake(qubits: qbit_list, measDelay = 1e-6, signVec = None,
          doubleRound = True, buf = 30e-9, showPlot = False,
          docals = True, calRepeats=2):

    # FIXME: is this the right default?
    # signVec defaults to 1
    if signVec == None:
        signVec = [1]*len(qubits)
    signVec = tuple(signVec)
    # FIXME: what will it take for QGL2 compiler to support this.
    # Would it help to assign the result of product to a variable
    # first?
    # Or the result of zip()?
    for prep in product([Id,X], repeat=len(qubits)):
        with concur:
            for p,q,ct in zip(prep, qubits, range(len(qubits))):
                init(q) # FIXME: Should mark 'beginning' of list of
                        # expts, like QGL1 'WAIT'
                p(q) # Do the initial pulse for this entry
                qreset_Blake(q, measDelay, buf, signVec[ct])
                if doubleRound:
                    qreset_Blake(q, measDelay, buf, signVec[ct])
                MEAS(q)
                # a new instruction Blake invented to ensure
                # result is loaded into the register
                qwait(q, 'CMP')

    # If we're doing calibration too, add that at the very end
    # - another 2^numQubits * calRepeats sequences
    if docals:
        create_cal_seqs(qubits, calRepeats)

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    compileAndPlot('Reset/Reset', showPlot)

# Imports for testing only
from qgl2.qgl2 import Qbit
from QGL.Channels import Qubit, LogicalMarkerChannel, Edge
import QGL.ChannelLibrary as ChannelLibrary
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

    # this block depends on the existence of q1 and q2
#    crgate = LogicalMarkerChannel(label='cr-gate')

#    cr = Edge(label="cr", source = q1, target = q2, gateChan = crgate )
#    cr.pulseParams['length'] = 30e-9
#    cr.pulseParams['phase'] = pi/4

#    ChannelLibrary.channelLib = ChannelLibrary.ChannelLibrary()
#    ChannelLibrary.channelLib.channelDict = {
#        'q1-gate': qg1,
#        'q1': q1,
#        'q2-gate': qg2,
#        'q2': q2,
#        'cr-gate': crgate,
#        'cr': cr
#    }
#    ChannelLibrary.channelLib.build_connectivity_graph()

    # But the current qgl2 compiler doesn't understand Qubits, only
    # Qbits. So use that instead when running through the QGL2
    # compiler, but comment this out when running directly.
    q1 = Qbit(1)
    q2 = Qbit(2)
    Reset([q1, q2])

if __name__ == "__main__":
    main()
