# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# Note: This code is QGL not QGL2

# This file contains code to replace Barrier instructions with appropriate Id()
# pulses to make channels line up without using a Wait where possible.
# Where not possible, it replaces the Barrier with Sync then Wait.
# See replaceBarriers().

# Some assumptions:
# * All channels have identical # of Barriers
# * LoadRepeat comes before label and before the Repeat
# * Currently, cannot be a Barrier between the start label and the Repeat
#   * That must change
# * Currently Call must go to something later.
#   * That must change
# * Currently, cannot be a Barrier between Call and its Return
#   * That must change
# * When all channels start with a Barrier, make it a Wait

from QGL.ControlFlow import Goto, Call, Return, LoadRepeat, Repeat, Wait, LoadCmp, Sync, ComparisonInstruction, ControlInstruction, Barrier
from QGL.PulseSequencer import Pulse, CompositePulse, PulseBlock
from QGL.BlockLabel import BlockLabel
from QGL.PulsePrimitives import Id

import logging

logger = logging.getLogger('QGL.Compiler.qgl2')

# Convenience functions to identify pulse/control elements
def isWait(pulse): return isinstance(pulse, Wait)
def isBarrier(pulse): return isinstance(pulse, Barrier)
def isSync(pulse): return isinstance(pulse, Sync)
def isCMP(pulse): return isinstance(pulse, ComparisonInstruction)
def isLoadCmp(pulse): return isinstance(pulse, LoadCmp)
def isID(pulse): return (isinstance(pulse, Pulse) and pulse.label == "Id")
def isReturn(pulse): return isinstance(pulse, Return)
def isLoadRepeat(pulse): return isinstance(pulse, LoadRepeat)
def isRepeat(pulse): return isinstance(pulse, Repeat)
def isGoto(pulse): return isinstance(pulse, Goto)
def isCall(pulse): return isinstance(pulse, Call)

def pulseLengths(pulses):
    '''QGL1 function to get the length of a pulse, pulseblock,
    compositepulse, or list or tuple of such things.'''
    lenRes = 0
    if pulses is None:
        logger.debug("pulses was None")
        return lenRes
    if isinstance(pulses, list) or isinstance(pulses, tuple):
        # logger.debug("pulses was list")
        if len(pulses) == 0:
            logger.debug("pulses was list of length 0")
            return lenRes
        for pulse in pulses:
            lenRes += pulseLengths(pulse)
        return lenRes
    if isinstance(pulses, Pulse) or isinstance(pulses, CompositePulse) \
       or isinstance(pulses, PulseBlock) or isinstance(pulses, ControlInstruction) \
       or isinstance(pulses, BlockLabel):
        logger.debug("Pulse %s length: %f", pulses, pulses.length)
        return pulses.length

    # Not a pulse or list of pulses that we know how to handle
    # FIXME! Raise some kind of error?
    # Or are there pulse like things in there that we should ignore?
    logger.warning("Unknown sequence element %s assumed to have length 0", pulses)
    return lenRes

def replaceBarriers(seqs, seqIdxToChannelMap):
    '''Where sequences have lined up Barriers where the time to reach the Barrier
    is deterministic, replace the Barrier with appropriate length Id pulses to 
    keep things lined up. Else replace it with a Sync then Wait'''

    # How many barriers are there
    barrierCnt = 0
    # Which barrier are we handling - marks end of current subblock
    curBarrier = 0
    # 0 based index into the sequence of next element/pulse to look at
    startCursorBySeqInd = dict()
    # List of indexes into sequences of Barriers for each sequence
    barrierIdxesBySeqInd = dict()

    # First loop over each sequence, building up a count of barriers in each and a dict by seqInd with the indices of the barriers.
    for seqInd, seq in enumerate(seqs):
        startCursorBySeqInd[seqInd] = 0
        barrierIdxes = list()
        for ind, elem in enumerate(seq):
            if isBarrier(elem):
                barrierIdxes.append(ind)
        barrierIdxesBySeqInd[seqInd] = barrierIdxes

    # If some sequence has a different number of Barriers, we can't do these replacements
    maxBarrier = max([len(barrierIdxesBySeqInd[i]) for i in barrierIdxesBySeqInd])
    minBarrier = min([len(barrierIdxesBySeqInd[i]) for i in barrierIdxesBySeqInd])
    if maxBarrier != minBarrier:
        # Some sequence has diff # of barriers
        logger.info("Cannot replace any Barriers with pause (Id) pulses; # Barriers ranges from %d to %d", minBarrier, maxBarrier)
        return seqs

    # All sequences have this # of barriers for us to process
    barrierCnt = maxBarrier
    logger.debug("\nSequences have %d barriers", barrierCnt)

    while curBarrier < barrierCnt and all([isBarrier(seq[curBarrier]) for seq in seqs]):
        logger.debug("All sequences had Barrier at %d", curBarrier)
        curBarrier += 1

    # If we skipped some barriers and there is more to do,
    # Then push forward the cursor for each sequence where we'll start in measuring
    # lengths
    # And make the sequences start with a Wait and skip extra Barriers
    if curBarrier > 0 and curBarrier < barrierCnt:
        logger.debug("Skipped some barriers. Now at barrier %d of %d", curBarrier, barrierCnt)
        for seqInd, seq in enumerate(seqs):
            seqs[seqInd] = [Wait()] + seq[curBarrier:]
            startCursorBySeqInd[seqInd] = barrierIdxesBySeqInd[seqInd][curBarrier - 1] + 1

    # Store the length of the current sub-segment for each sequence
    curSeqLengthBySeqInd = dict()

    logger.debug("Ready to loop over %d barrier blocks", barrierCnt - curBarrier)

    # Now loop over each sub-segment
    # That is, the pulses after the last Barrier and up through the next barrier
    # For each, we have to count up the length in each sequence, handling repeats/gotos
    # And if we find something we don't know how to handle, we need to skip to the end of this Barrier block,
    # leaving the Barrier in place
    while curBarrier < barrierCnt:
        logger.debug("Starting barrier block %d", curBarrier)
        # Is this block of indeterminate length
        nonDet = False
        for seqInd, seq in enumerate(seqs):
            logger.debug("Starting sequence %d", seqInd)

            # Clear the length for this sequence
            curSeqLengthBySeqInd[seqInd] = 0
            # Shorthand to use for adding as we go
            curlen = 0

            # How many times is the repeat block (if any) to be repeated
            # - LIFO stack to allow nesting
            rptCount = []
            # How long is this repeat block (if any)
            rptLen = []
            # Index into sequence where the repeat block if any might start (right after LoadRepeat say)
            rptStartInd = []
            # Element in sequence where repeat block starts if known, or best guess
            rptStartElem = []
            # Length of current sub-block before we started the current repeat, if any
            rptStartLen = []

            # LIFO stack of Index where the next return should go back to (set on seeing a Call)
            # - LIFO so you can nest such call/returns
            retInd = []

            # Index into this sequence of the next Barrier command
            nextBarrierInd = barrierIdxesBySeqInd[seqInd][curBarrier]
            # Index into sequence where we are currently looking
            # starts at startCursorBySeqInd
            curInd = startCursorBySeqInd[seqInd]

            # Now look at each seq element from the current spot (curInd) up to nextBarrierInd (index of next Barrier)
            while curInd <= nextBarrierInd:
                elem = seq[curInd]

                # If we reached the end, stop (should be Barrier)
                if isBarrier(elem):
                    if curInd == nextBarrierInd:
                        logger.debug("Got up to next Barrier at index %d", curInd)
                        curlen += pulseLengths(elem)
                        break # out of this while loop
                    else:
                        raise Exception("Sequence %d found unexpected %s at %d. Didn't expect it until %d" % (seqInd, elem, curInd, nextBarrierInd))
                elif curInd == nextBarrierInd:
                    raise Exception("Sequence %d found unexpected %s at %d. Expected Barrier" % (seqInd, elem, curInd))

                # If this is a comparison of some kind,
                # then this block is of indeterminate length,
                # so we can't replace the Barrier with Id - must use Sync then Wait
                if isCMP(elem) or isLoadCmp(elem):
                    logger.info("Indeterminate length block due to sequence %d has %s at %d", seqInd, elem, curInd)
                    nonDet = True
                    break

                # If this is repeat / loadrepeat
                # NOTE: Here I assume that a Barrier in the middle of a repeat block is illegal
                if isLoadRepeat(elem):
                    if elem.value < 1:
                        # FIXME: raise Exception instead?
                        logger.warning("Sequence %d at %d got %s with value %d: Treat as 1", seqInd, curInd, elem, elem.value)
                        elem.value = 1
                    logger.debug("Found %s at index %d. Length so far: %f", elem, curInd, curlen)
                    rptCount.append(elem.value)

                    # Guess that the repeat will want to go to line after LoadRepeat - if not, we'll start looking there
                    # for the proper destination
                    rptStartInd.append(curInd+1)
                    rptStartElem.append(seq[curInd+1])

                    curlen += pulseLengths(elem)
                    rptStartLen.append(curlen)
                    curInd += 1
                    continue

                if isRepeat(elem):
                    curlen += pulseLengths(elem)
                    # When we get here, we've already added to curlen the result of doing this once
                    if not rptCount:
                        # FIXME: Ignore instead? Use NodeError?
                        raise Exception("Sequence %d got %s at %d without a LoadRepeat" % (seqInd, elem, curInd))

                    # Get the # of times left to repeat
                    rc = rptCount[len(rptCount)-1] - 1
                    logger.debug("Found %s at index %d. Remaining repeats %d", elem, curInd, rc)

                    # If there are no more repeats, move on
                    if rc <= 0:
                        # Just finished last time through the loop
                        # Clear all the repeat variables
                        rptCount.pop()
                        while len(rptStartInd) > len(rptCount):
                            rptStartInd.pop()
                        while len(rptStartElem) > len(rptCount):
                            rptStartElem.pop()
                        rptStartLen.pop()
                        # Move on to the next element
                        curInd += 1
                        continue

                    # If we get here, we need to repeat that block at least once
                    # Update the repeats remaining counter
                    rptCount[len(rptCount)-1] = rc

                    # Back when we got the LoadRepeat (or looked back to find target), we guessed where to start from
                    # If the guess is still in place and matches what we want, just use that and move on
                    if len(rptCount) == len(rptStartElem) and rptCount[len(rptCount)-1] and elem.target == rptStartElem[len(rptStartElem)-1]:
                        # We guessed correctly where to start repeat from
                        rs = rptStartLen.pop()
                        rptAdd = (curlen - rs) * rc
                        logger.debug("Stashed startElem matches target. Finish by adding (curlen %f - startLen %f) * repeatsToGo %d = %f", curlen, rs, rc, rptAdd)
                        curlen += rptAdd

                        # Just finished last time through the loop
                        # Clear all the repeat variables
                        rptCount.pop()
                        while len(rptStartInd) > len(rptCount):
                            rptStartInd.pop()
                        while len(rptStartElem) > len(rptCount):
                            rptStartElem.pop()
                        while len(rptStartLen) > len(rptCount):
                            rptStartLen.pop()
                        # Move on to the next element
                        curInd += 1
                        continue
                    else:
                        logger.debug("Go back to look for target (wasn't stashed guess '%s')", rptStartElem[len(rptStartElem)-1])
                        # Go back to find the blocklabel to repeat from
                        # We go back to rptStartInd and loop forward until we find elem.target.
                        # Then set curInd to that ind, set startElem to the elem.target
                        # and set StartLen to curlen
                        rptStartElem[len(rptStartElem)-1] = elem.target
                        rptStartLen[len(rptStartLen)-1] = curlen
                        idx = rptStartInd[len(rptStartInd)-1]
                        while idx < curInd and seq[idx] != elem.target:
                            idx += 1
                        if idx == curInd:
                            logger.warning("Failed to find %s target '%s' in sequence %d from %d to %d - cannot repeat", elem, elem.target, seqInd, rptStartInd[len(rptStartInd)-1], curInd)
                            # FIXME: Keep going?
                            curInd += 1
                            continue
                        logger.debug("Found repeat start at %d - going back there", idx)
                        #else:
                        # Continue this loop from that point
                        curInd = idx
                        continue
                # End of handling Repeat

                if isCall(elem):
                    # A call has a matching Return. We will need to return to the line after this.
                    # Note we assume no intervening Barrier.
                    callTarget = elem.target
                    retInd.append(curInd+1)
                    logger.debug("Got %s at %d pointing at '%s'", elem, curInd, elem.target)
                    curlen += pulseLengths(elem)

                    # Look for the call target from here forward to next Barrier
                    foundTarget = False
                    for ind2, e2 in enumerate(seq[curInd+1:nextBarrierInd-1]):
                        if e2 == callTarget:
                            curInd = ind2
                            foundTarget = True
                            break
                    if foundTarget:
                        # reset pointer so next loop will start where Call pointed
                        logger.debug("Jumping to target at %d", curInd)
                        continue
                    # FIXME: Exception? Log and continue?
                    raise Exception("Sequence %d at %d: Failed to find %s target '%s' from there to next barrier at %d" % (seqInd, curInd, elem, elem.target, nextBarrierInd-1))

                if isReturn(elem):
                    # Should have seen a call that put a return index in our list
                    curlen += pulseLengths(elem)
                    if not retInd:
                        raise Exception("Sequence %d at %d: Have no saved index to go back to for %s" % (seqInd, curInd, elem))
                    ri = retInd.pop()
                    logger.debug("Got %s: Returning to saved index %d", elem, ri)
                    curInd = ri
                    continue

                if isGoto(elem):
                    # Jump to line with given label
                    gotoElem = elem.target
                    curlen += pulseLengths(elem)

                    foundTarget = False
                    logger.debug("Got %s at %d pointing at %s", elem, curInd, gotoElem)
                    for ind2, e2 in enumerate(Seq[curInd+1:nextBarrierInd-1]):
                        if e2 == gotoElem:
                            curInd = ind2
                            foundTarget = True
                            break
                    if foundTarget:
                        logger.debug("Jumping to target at %d", curInd)
                        continue
                    # FIXME: Exception or log and continue?
                    raise Exception("Sequence %d at %d: Failed to find %s target '%s' from there to next barrier at %d" % (seqInd, curInd, elem, elem.target, nextBarrierInd-1))

                # Normal case: Add length of this element and move to next element
                logger.debug("'%s' is a normal element - add its length (%f) and move on", elem, pulseLengths(elem))

                curlen += pulseLengths(elem)
                curInd += 1
            # End of while loop over elements in this block in this sequence

            # If this was nonDet, stop looping over sequences for this block
            if nonDet:
                break

            # Record the length we found
            curSeqLengthBySeqInd[seqInd] = curlen

            # I want us to be pointing at the final barrier now: Make sure
            if not isBarrier(seq[curInd]) or not curInd == nextBarrierInd:
                raise Exception("Sequence %d: Expected when done with walking a barrier block to be pointing at that last barrier but stopped at %d:%s not %d:%s" % (seqInd, curInd, seq[curInd], nextBarrierInd, seq[nextBarrierInd]))

            # Push forward where we'll start for next block in this sequence
            startCursorBySeqInd[seqInd] = curInd
        # End of loop over sequences for this block

        # If we found this block was indeterminate, push to next block without doing anything
        if nonDet:
            logger.info("Barrier block %d was indeterminate length - will replace with SyncWait", curBarrrier)
            # Don't actually do the replacements here, because it screws up the indices (change 1 for 2)
        else:
            # Now replace Barriers
            # In each sequence we should currently be pointing at the last barrier (in startCursorBySeqInd)
            # We now have block lengths for each sequence
            seqs = replaceBarrier(seqs, startCursorBySeqInd, curSeqLengthBySeqInd, seqIdxToChannelMap)
            # When done with sub segments would/should remove empty Id pulses, BUT....
            # * compile_to_hardware already does this, so don't do it again

        # Move all start pointers past the Barrier that ended that block
        for sidx2, s2 in enumerate(seqs):
            startCursorBySeqInd[sidx2] = barrierIdxesBySeqInd[sidx2][curBarrier]+1

        # Move on to next sub segment / barrier block
        curBarrier += 1
    # End of while loop over barrier blocks

    # Any Barriers left over couldn't be replaced - replace with Wait/Sync
    curBarrier = 0
    swapCnt = 0 # Num swaps done so # that indices are off (must be added)
    while curBarrier < barrierCnt:
        # If every seq still has a barrier at the expected location:
        if all(isBarrier(seq[barrierIdxesBySeqInd[sidx][curBarrier]+swapCnt]) for sidx, seq in enumerate(seqs)):
            logger.debug("Barrier %d was left behind (nondeterministic). Replace with Sync/Wait", curBarrier)
            # Make startCursor point at that Barrier to replace
            # Then re-assign the sequence to be
            # Everything up to that barrier plus a sync then wait plus everything after that barrier
            for sidx2, s2 in enumerate(seqs):
                startCursorBySeqInd[sidx2] = barrierIdxesBySeqInd[sidx2][curBarrier]+swapCnt
                seqs[sidx2] = s2[:startCursorBySeqInd[sidx2]] + [Sync(), Wait()] + s2[startCursorBySeqInd[sidx2]+1:]
                logger.debug("Sequence %d replacing index %d", sidx2, startCursorBySeqInd[sidx2])
                swapCnt += 1
        elif any(isBarrier(seq[barrierIdxesBySeqInd[sidx][curBarrier]+swapCnt]) for sidx, seq in enumerate(seqs)):
            for sidx, seq in enumerate(seqs):
                if isBarrier(seq[barrierIdxesBySeqInd[sidx][curBarrier]+swapCnt]):
                    logger.error("Sequence %d still has Barrier %d at index %d!", curBarrier, sidx, barrierIdxesBySeqInd[sidx][curBarrier]+swapCnt)
        curBarrier += 1

    # Now we have replaced Barriers with Id pulses where possible
    logger.debug("Done replacing Barriers with Ids where possible.\n")
    return seqs

def replaceBarrier(seqs, inds, lengths, chanBySeq):
    '''Replace the barrier at the given inds (indexes) in all sequences with the proper Id pulse'''
    maxBlockLen = max(lengths.values())
    logger.debug("For this barrier block: max Len: %f, min len: %f", maxBlockLen, min(lengths.values()))
    for seqInd, seq in enumerate(seqs):
        ind = inds[seqInd] # Index of the Barrier
        idlen = maxBlockLen - lengths[seqInd] # Length of Id pulse to pause till last channel done
        logger.info("Sequence %d: Replacing %s with Id(%s, length=%f)", seqInd, seq[ind],
                    chanBySeq[seqInd], idlen)
        seq[ind] = Id(chanBySeq[seqInd], idlen)
    return seqs

if __name__ == '__main__':
    from QGL.Compiler import find_unique_channels
    from QGL.Channels import Qubit as qgl1Qubit
    import logging

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger()

    def testFunc2():
#with concur
#  for i in 1,2
#    for q in q1, q2
#       X(q)

# Becomes:

#BARRIER - becomes a wait
#LoadRepeat 2
#loopstart
#X(q)
#Repeat(loopstart)
#BARRIER - becomes ID
        from QGL.ChannelLibrary import QubitFactory
        from QGL.BlockLabel import BlockLabel
        from QGL.ControlFlow import Barrier
        from QGL.ControlFlow import Sync
        from QGL.ControlFlow import Wait
        from QGL.PulsePrimitives import Id
        from QGL.PulsePrimitives import MEAS
        from QGL.PulsePrimitives import X
        from QGL.PulsePrimitives import Y

        q1 = QubitFactory('q1')
        QBIT_q1 = q1
        q2 = QubitFactory('q2')
        QBIT_q2 = q2
        q3 = QubitFactory('q3')
        QBIT_q3 = q3

        seqs = list()
        seq = [
            Barrier(),
            LoadRepeat(2),
            BlockLabel('loopstart'),
            X(q1, length=0.5),
            Repeat(BlockLabel('loopstart')),
            Barrier()
            ]
        seqs += [seq]
        seq = [
            Barrier(),
            LoadRepeat(2),
            BlockLabel('loopstart2'),
            X(q2),
            Repeat(BlockLabel('loopstart2')),
            Barrier()
            ]
        seqs += [seq]
        return seqs

    def repeatBarriers():
        '''
for i in 1,2
  with concur
     for q in q1,q2
       X(q)
LoadRepeat 2
loopstart
BARRIER - remove?
X(q)
BARRIER - becomes Id
Repeat(loopstart)
        '''
        from QGL.ChannelLibrary import QubitFactory
        from QGL.BlockLabel import BlockLabel
        from QGL.ControlFlow import Barrier
        from QGL.ControlFlow import Sync
        from QGL.ControlFlow import Wait
        from QGL.PulsePrimitives import Id
        from QGL.PulsePrimitives import MEAS
        from QGL.PulsePrimitives import X
        from QGL.PulsePrimitives import Y

        q1 = QubitFactory('q1')
        QBIT_q1 = q1
        q2 = QubitFactory('q2')
        QBIT_q2 = q2
        q3 = QubitFactory('q3')
        QBIT_q3 = q3

        seqs = list()
        seq = [
            LoadRepeat(2),
            BlockLabel('loopstart1'),
            Barrier(),
            X(q1, length=0.1),
            Barrier(),
            Repeat(BlockLabel('loopstart1')),
            Barrier() # Including this causes error cause we see the Repeat without LoadRepeat
        ]
        seqs += [seq]
        seq = [
            LoadRepeat(2),
            BlockLabel('loopstart2'),
            Barrier(),
            X(q2, length=0.2),
            Barrier(),
            Repeat(BlockLabel('loopstart2')),
            Barrier()
        ]
        seqs += [seq]
        return seqs
 
    def testFunc():
        from QGL.ChannelLibrary import QubitFactory
        from QGL.ControlFlow import Barrier
        from QGL.ControlFlow import Sync
        from QGL.ControlFlow import Wait
        from QGL.PulsePrimitives import Id
        from QGL.PulsePrimitives import MEAS
        from QGL.PulsePrimitives import X
        from QGL.PulsePrimitives import Y

        q1 = QubitFactory('q1')
        QBIT_q1 = q1
        q2 = QubitFactory('q2')
        QBIT_q2 = q2
        q3 = QubitFactory('q3')
        QBIT_q3 = q3

        seqs = list()
        seq = [
            Barrier(),
            Barrier(),
            Barrier(),
            Y(QBIT_q3, length=0.6),
            Barrier()
        ]
        seqs += [seq]
        seq = [
            Barrier(),
            Sync(),
            Wait(),
            Sync(),
            Wait(),
            Barrier()
        ]
        seqs += [seq]
        seq = [
            Barrier(),
            Id(QBIT_q2, length=0.5),
            X(QBIT_q2),
            MEAS(QBIT_q2),
            Barrier(),
            Barrier(),
            Barrier()
        ]
        seqs += [seq]
        seq = [
            Barrier(),
            Id(QBIT_q1),
            X(QBIT_q1, length=0.4),
            MEAS(QBIT_q1),
            Barrier(),
            Barrier(),
            Y(QBIT_q1),
            Barrier()
        ]
        seqs += [seq]
        return seqs

    def printSeqs(seqs):
        from QGL.PulseSequencer import Pulse
        ret = "["
        firstSeq = True
        for sidx, seq in enumerate(seqs):
            if not firstSeq:
                ret += ","
            else:
                firstSeq = False
            ret += "\n"
            ret += "%d:  [" % sidx
            firstElem = True
            for elem in seq:
                if not firstElem:
                    ret += ","
                else:
                    firstElem = False
                ret += "    %s" % str(elem)
                if isinstance(elem, Pulse) and (elem.label == 'Id' or elem.length != 0):
                    ret += "(len: %f)" % elem.length
            ret += "  ]"
        ret += "\n]\n"
        return ret

    seqs = repeatBarriers()

    logger.info("Seqs: \n%s", printSeqs(seqs))

    seqIdxToChannelMap = dict()
    for idx, seq in enumerate(seqs):
        chs = find_unique_channels(seq)
        for ch in chs:
            # FIXME: Or just exclude Measurement channels?
            if isinstance(ch, qgl1Qubit):
                seqIdxToChannelMap[idx] = ch
                logger.debug("Sequence %d is channel %s", idx, ch)
                break

    # Hack: skip the empty sequence(s) now before doing anything else
    useseqs = list()
    decr = 0 # How much to decrement the index
    toDecr = dict() # Map of old index to amount to decrement
    for idx, seq in enumerate(seqs):
        if idx not in seqIdxToChannelMap:
            # Indicates an error - that empty sequence
            logger.debug("Sequence %d has no channel - skip", idx)
            decr = decr+1
            continue
        if decr:
            toDecr[idx] = decr
            logger.debug("Will shift index of sequence %d by %d", idx, decr)
        useseqs.append(seq)
    seqs = useseqs
    if decr:
        newmap = dict()
        for ind in seqIdxToChannelMap:
            if ind in toDecr:
                newmap[ind-decr] = seqIdxToChannelMap[ind]
                logger.debug("Sequence %d (channel %s) is now sequence %d", ind, seqIdxToChannelMap[ind], ind-decr)
            elif ind in seqIdxToChannelMap:
                logger.debug("Sequence %d keeping map to %s", ind, seqIdxToChannelMap[ind])
                newmap[ind] = seqIdxToChannelMap[ind]
            else:
                logger.debug("Dropping (empty) sequence %d", ind)
        seqIdxToChannelMap = newmap

    logger.info("Seqs just before replace:\n%s", printSeqs(seqs))
    seqs = replaceBarriers(seqs, seqIdxToChannelMap)
    logger.info("Seqs after replace: \n%s", printSeqs(seqs))
