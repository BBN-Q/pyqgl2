# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# Note: This code is QGL not QGL2

# This file contains code to replace Barrier instructions with appropriate Id()
# pulses to make channels line up without using a Wait where possible.
# Where not possible, it replaces the Barrier with Sync then WaitSome.
# See replaceBarriers().

'''
Assumptions
* A given function invocation / program has an even # (possibly 0) of Barriers on
  each channel
 * Given barriers at both start/end of with concur or with inlined,
   and no manual additions, this is guaranteed. If the statements in a
   function are not in a with-concur then they are treated as
   sequential, and barriers will be inserted between sequential statements.
* QGL2 programmers may not manually insert Goto, Call, Return,
  BlockLabel, Repeat, LoadRepeat, or Barrier
 * Open question: We could relax this if other things hold true, but why? Perhaps you
 can write a QGL1 function because QGL2 is not expressive enough?
 * Open question: Perhaps you can add Barriers in a sort of export mode?
* LoadRepeat is immediately followed by the BlockLabel we'll repeat to
 * That is, this is what QGL2 will do
 * We could relax this, but why?
* LoadRepeat value will be integer of at least 2
 * That is, this is what QGL2 will do
* The statement block to be repeated (between BlockLabel target of
  Repeat & Repeat) does not include a Goto without also including the
  BlockLabel target of the Goto
 * Note that there may be unused BlockLabels.
* Block to be repeated (between BlockLabel & Repeat) does not include a
  Call without including the target BlockLabel and the matching Return
* Call and Goto and Repeat target BlockLabels exist on each relevant
  channel's program & are unique (per program)
* Code 'between' Call and Return includes an even # (possibly 0) of
  Barriers
 * where 'between' follows execution order not order in the sequence
 * Note there may be some number of Goto and CMP statements in the middle.
* Code 'between' 2 'paired' Barriers does not include a Call without [its
  BlockLabel target, obviously, and] Return
 * where 'paired' refers to the indentation level in the source and is
   not immediately apparent once 'compiled'; e.g. matching
 * there may be other nested barriers in the middle
* A valid QGL2 program calls init() (as currently defined) on all channels that will be used in the program concurrently
 * because it includes a global Wait that requires a Sync from all channels before the program can proceed
* Call and Repeat blocks may be nested

Some things you cannot assume:
* The BlockLabel target of a Goto is often numerically BEFORE the
  Goto; make no assumption about its relative placement
* The BlockLabel target of a Call may be numerically before or after
  the Call; make no assumption about its relative placement
* The Return is numerically before or after the BlockLabel target of a
  Call; make no assumption about its relative placement
* The Repeat is numerically before or after the LoadRepeat /
  BlockLabel target; make no assumption about its relative placement
'''

# Other points
# * There may be diff # of Barriers on diff channels
# * Each barrier has a globally unique Id and list of channels that include this barrier,
# meaning that all those barriers wait on this barrier
# * Wait is like a barrier on all channels.

# * When all channels start with a Barrier, make it a Wait

from QGL.ControlFlow import Goto, Call, Return, LoadRepeat, Repeat, Wait, LoadCmp, Sync, ComparisonInstruction, ControlInstruction, Barrier, WaitSome
from QGL.PulseSequencer import Pulse, CompositePulse, PulseBlock
from QGL.BlockLabel import BlockLabel
from QGL.PulsePrimitives import Id

import logging

logger = logging.getLogger('QGL.Compiler.qgl2')

# Convenience functions to identify pulse/control elements
def isWait(pulse): return isinstance(pulse, Wait)
def isWaitSome(pulse): return isinstance(pulse, WaitSome)
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
def isBlockLabel(pulse): return isinstance(pulse, BlockLabel)

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

def replaceBarriersOld(seqs, seqIdxToChannelMap):
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
            # This is an actual Pulse/BlockLabel
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

def replaceBarrierOld(seqs, inds, lengths, chanBySeq):
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

# =================================================
# Reworked logic to support different channels having different numbers of barriers

def markBarrierLengthCalculated(barrierCtr, seqIdx, newLen=float('nan')):
    '''Update the barrier object in our 3 data structures 
    for the given counter, sequence with the given length.'''
    # To be called for each sequence that this barrier is on
    global barriersByCtr, barriersBySeqByPos, barriersBySeqByCtr
    barrier = barriersByCtr.get(barrierCtr, None)
    if barrier is not None:
        barrier['lengthSince'] = newLen
        barrier['lengthCalculated'] = True
        barriersByCtr[barrierCtr] = barrier
    else:
        logger.warning("Barrier %s not in barriersByCtr", barrierCtr)
    if seqIdx in barriersBySeqByPos:
        for pos in barriersBySeqByPos[seqIdx]:
            if barrierCtr == barriersBySeqByPos[seqIdx][pos]['counter']:
                barrier = barriersBySeqByPos[seqIdx][pos]
                barrier['lengthSince'] = newLen
                barrier['lengthCalculated'] = True
                barriersBySeqByPos[seqIdx][pos] = barrier
                break
    if seqIdx in barriersBySeqByCtr:
        if barrierCtr in barriersBySeqByCtr[seqInd]:
            barrier = barriersBySeqByCtr[seqIdx][barrierCtr]
            barrier['lengthSince'] = newLen
            barrier['lengthCalculated'] = True
            barriersBySeqByCtr[seqInd][barrierCtr] = barrier

def getBarrierForSeqCtr(seqInd, currCtr):
    '''Get the barrier object for the currCtr Barrier
    ID for the sequence seqInd, or -1 if not found.'''
    global barriersBySeqByCtr
    if currCtr is None:
        logger.debug("getBarrierForSeq got None currCtr")
        return -1
    if not seqInd in barriersBySeqByCtr:
        # FIXME: Error?
        logger.warning("getBarrierForSeqCtr got seqInd %s not in barriersBySeqByCtr", seqInd)
        return -1

    # For a wait, could look it up by the index
    # But the wait should be on the ByCtr list too
#    if str(currCtr).startswith('with-'):
#        # It was a with, so this has the index in it
#        return barriersBySeqByPos[seqInd].get(int(currCtr[5:]), -1)

#    elif currCtr == -1:
#        # start - should really be -1, but if the sequence has something, why not?
    return barriersBySeqByCtr[seqInd].get(currCtr, -1)

def getLengthBetweenBarriers(seqInd, currCtr, prevCtr='-1'):
    '''For the given sequence, find the length between the given 2 barriers.
    Return float('NaN') if indeterminate.
    Recurses up the list of barriers adding up the lengths we previously
    calculated for each pair of Barriers.
    So if the length between any 2 barriers within that chain are indeterminate, 
    the whole thing is indeterminate.
    '''
    # ctr of '-1' means start
    # ctr of 'wait-%d' means a Wait at that index in the sequence
    # seqInd is the index of the sequence
    import math
    if currCtr == prevCtr:
        logger.debug("getLengthBetween asked for length to self %s", currCtr)
        return 0
    # find the barrier lengths for this channel
    # follow the previous pointers, adding lengths
    currBarrier = getBarrierForSeqCtr(seqInd, currCtr)
    if currBarrier == -1:
        logger.debug("getLengthBetween from current -1 (start or error), use length 0")
        # from start
        return 0

    # Basic case: the previous barrier is the one we're looking for
    prevBarrierCtr = currBarrier['prevBarrierCtr']
    prevLen = currBarrier['lengthSince']
    # FIXME: Guard against barrier not having these fields?
    if prevBarrierCtr == prevCtr:
        return prevLen

    # Old code stored firstPrev and prevPrev to handle repeat with barrier inside
    # But now realize that doesn't make sense; any barrier inside a repeat (if allowed at all)
    # must be treated as indetermine / a Wait
    
    # If the length so far is indeterminate, no use in recursing -
    # the whole thing will be indeterminate
    if math.isnan(prevLen):
        return prevLen

    # If this barrier doesn't store the desired length, then recurse
    return prevLen + getLengthBetweenBarriers(seqInd, prevBarrierCtr, prevCtr)

def isReplaceableBarrier(barrier, seqs):
    '''Is the given barrier object replacable on its sequence?
    Start, Wait, WaitSome, and barriers that are no longer in
    their sequence are not replacable. So only a Barrier() of the correct id (counter).
    '''
    # Is the given barrier something we can replace?
    # Not a Wait or WaitSome, and still in its sequence
    # return boolean
    ind = barrier['seqPos']
    nextCtr = barrier['counter']
    nextType = barrier['type']
    seqInd = barrier['seqIndex']
    if ind < 0:
        logger.debug("Barrier %s is start, not replacable", nextCtr)
        return False
    if nextType in ('wait', 'waitsome'):
        logger.debug("Barrier %s is a wait, not replacable", nextCtr)
        return False
    if seqs:
        if seqInd not in seqs:
            logger.debug("Barrier %s claims to be on sequence %d which doesn't exist", nextCtr, seqInd)
            return False
        if len(seqs[seqInd]) <= ind:
            logger.debug("Barrier %s claims to be at position %d on sequence %d; the sequence has only %d items", nextCtr, ind, seqInd, len(seqs[seqInd]))
            return False
        if seqs[seqInd][ind].has_attribute('value') and seqs[seqInd][ind].value == nextCtr:
            return True
        if isID(seqs[seqInd][ind]):
            # Expected when we've already done a replacement
            logger.debug("Barrier %s actual element is (now) %s on sequence %d", nextCtr, seqs[seqInd][ind], seqInd)
            return False
        if not isBarrier(seqs[seqInd][ind]):
            # We don't think we've replaced any barriers with waits, so this is unexpected
            logger.debug("Barrier %s claims type %s but actual element is (now) %s on sequence %d", nextCtr, nextType, seqs[seqInd][ind], seqInd)
            return False
        else:
            # It's a barrier but the wrong barrier ID?
            logger.warning("Barrier %s should be at %d on sequence %d, but instead found %s", nextCtr, ind, seqInd, seqs[seqInd][ind])
            return False
    return False

def getNextBarrierCtr(seqs, seqInd, currCtr):
    ''' Find the id (counter) of the next Barrier after currCtr on the given sequence
    that we could (still) replace. So skip barriers no longer in the sequence, or that
    are a Wait or WaitSome.
    Return '-1' if there is none.
    '''
    # Walk to the next barrier past currCtr on sequence seqInd and return the counter of that barrier
    # Return '-1' if no more
    # This is just iterating over barriers on this channel
    # This is for following execution path of a sequence to find
    # all the barriers and swap them all
    # seqInd is the sequence index
    global barriersBySeqByPos, barriersBySeqByCtr
    # If this sequence has no barriers, done
    if not seqInd in barriersBySeqByPos or len(barriersBySeqByPos[seqInd]) == 0:
        logger.debug("getNextBarrierCtr found none for sequence %d", seqInd)
        return '-1'
    if str(currCtr) != '-1' and currCtr not in barriersBySeqByCtr[seqInd].keys():
        # Failed to find desired barrier on this channel
        # FIXME: Raise exception?
        logger.warning("getNextBarrierCtr failed to find barrier %s for sequence %d", currCtr, seqInd)
        return '-1'

    # Handle case where there's no current - we're looking for the first
    if str(currCtr) == '-1':
        if seqInd in barriersBySeqByPos and len(barriersBySeqByPos) > 0:
            for i in range(len(barriersBySeqByPos[seqInd])):
                barrier = barriersBySeqByPos[seqInd][i]
                # Make sure that barrier is actually still in the sequence it claims to be in;
                # we might have already removed it
                if isReplaceableBarrier(barrier, seqs):
                    # return this ctr
                    if str(barrier) == '-1':
                        return '-1'
                    else:
                        return barrier['counter']
                else:
                    # keep looping
                    continue
        else:
            logger.info("Channel %d has no barriers", seqInd)
            return '-1'

    # Find this barrier object
    currBarrier == getBarrierForSeqCtr(seqInd, currCtr)
    found = False
    for barrier in barriersBySeqByPos[seqInd]:
        if not found and barrier == currBarrier:
            # If we hadn't yet found the desired barrier but did now, say so
            found = True
            continue
        if found:
            # But if we had found it, then the next one we found is next
            # NOW....
            # Before blindly returning this barrier, see if it is actually still in the sequence

            # Make sure that barrier is actually still in the sequence it claims to be in;
            # we might have already removed it
            if isReplaceableBarrier(barrier, seqs):
                # return this ctr
                if str(barrier) == '-1':
                    return '-1'
                else:
                    return barrier['counter']
            else:
                # keep looping
                continue

    # We didn't find the desired barrier, or else didn't find a next
    logger.debug("getNextBarrierCtr failed to find a next for sequence %d, barrier %s", seqInd, currCtr)
    return '-1'
# End getNextBarrierCtr

def getBarrierChannels(barrierCtr):
    '''Return a list of Channel objects whose sequences have this barrier,
    and which this Barrier claims it blocks.
    For a Wait this will be allChannels.
    On error this will be an empty list.
    '''
    # What channels is this a barrier on?
    # Return allChannels or empty list or a list of the channel objects on this barrier
    global barriersByCtr, allChannels
    if str(barrierCtr) == '-1':# or str(barrierCtr).startswith('wait-'):
        # Start will wait on all channels
        logger.debug("%s waits on all channels", barrierCtr)
        return allChannels
    if not barrierCtr in barriersByCtr:
        logger.warning("Barrier %s unknown; assume it waits on no channels", barrierCtr)
        # FIXME: Could extract the channel that is the seq for the seqInd of this barrier and assume that
        return []
    return barriersByCtr[barrierCtr]['channels']

def getBarrierIdx(seqInd, barrierCtr):
    '''Get the int position index of the given barrier on the given sequence,
    or -1 if it is not found.'''
    # Get the position index in the sequence with index seqInd for the barrier
    # with ID barrierCtr, or -1 if not found
    global barriersBySeqByCtr
    if not seqInd in barriersBySeqByCtr:
        logger.warning("getBarrierIDx: Unknown sequence %d", seqInd)
        # Error - unknown channel
        return -1
    barriers = barriersBySeqByCtr[seqInd]
    if barrierCtr in barriers:
        return barriers[barrierCtr]['seqPos']
    else:
        # Error - this channel's sequence doesn't have this barrier
        logger.info("Sequence %d doesn't have barrier %s", seqInd, barrierCtr)
        return -1
    # Note one could also loop thru entries in barriersBySeqByPos and return
    # the relevant key when/if we find this barrierCtr

def getLastSharedBarrierCtr(channels, barrierCtr):
    '''Find the last Barrier id (counter) before barrierCtr with at least the same set
    of channels as barrierCtr. Return '-1' if there is none.'''
    # Find the last (before given barrier) barrier shared by the channels on this barrier
    # Return its ID (ctr)
    # Return '-1' if none (start)
    # each barrier has a prevBarrier
    # I'm looking for a barrier whose 'channels' is a superset of the given 'channels'
    global barriersBySeqByCtr, barriersByCtr
    if str(barrierCtr) == '-1' or barrierCtr is None:
        # This is the start - all channels have this and there's nothing prior
        return '-1'

    if not barrierCtr in barriersByCtr:
        logger.warning("Barrier %s unknown", barrierCtr)
        return '-1'
    barrier = barriersByCtr[barrierCtr]

    # Try to set channels if not given
    if not channels:
        if not barrier or barrier == -1 or not "channels" in barrier:
            logger.warning("Couldn't find channels on barrier %s", barrierCtr)
            return '-1'
        channels = barrier["channels"]
        
    if not channels:
        logger.debug("getLastShared couldn't find channels for Barrier %s", barrierCtr)
        return '-1'

    startBarrier = barrier
    if not startBarrier:
        raise Exception("Couldn't find Barrier %s in getLastSharedBarrierCtr" % barrierCtr)

    # Pick one of the sequences that has this Barrier, basically arbitrarily
    seqInd = startBarrier.get('seqIndex', -1)
    if seqInd == -1:
        for seqI in barriersBySeqByCtr.keys():
            if barrierCtr in barriersBySeqByCtr[seqI]:
                seqInd = seqI
                break
        if seqInd == -1:
            raise Exception("Couldn't find Barrier %s in list by sequence" % barrierCtr)

    seqBs = barriersBySeqByCtr[seqInd]
    channelsSet = set(channels)
    prevChannelSet = set()
    currBarrier = startBarrier
    prevBarrierCtr = barrierCtr
    prevBarrier = startBarrier

    # Loop up the barrier's previous pointers, looking to see if its channel set contains all the channels
    # for this Barrier. We're looking for the first previous barrier that is a supert of the channels
    # for this Barrier.
    while not channelsSet <= prevChannelSet:
        currBarrier = prevBarrier
        prevBarrierCtr = currBarrier['prevBarrierCtr']
        prevBarrier = seqBs.get(prevBarrierCtr, None)
        if not prevBarrier or prevBarrier == -1:
            logger.warning("Failed to find prev Barrier %s on sequence %d in getLastSharedBarrierCtr", prevBarrierCtr, seq)
            # This would happen if the last shared barrier is the start
            return '-1'
        prevChannelSet = set(prevBarrier.get('channels', []))
    if channelsSet <= prevChannelSet:
        logger.debug("Found previous barrier %s whose channels %s include at least the channels on Barrier %s: %s", prevBarrierCtr, prevChannelSet, barrierCtr, channelsSet)
        return prevBarrierCtr
    logger.info("Failed to find a common previous barrier to barrier %s on channels %s. Use start.", barrierCtr, channels)
    return '-1'
    
def replaceBarrier(seqs, currCtr, prevForLengthCtr, channelIdxs, chanBySeq):
    '''Replace Barrier currCtr on sequences with indices channelIdxs into seqs
    with the proper Id pulse, or mark this barrier as indeterminate and leave it.
    The Id pulse length is the time needed so all channels in channelIdxs take the same
    time to get from Barrier prevForLengthCtr to currCtr.
    Note the Id() pulse may have 0 length. Later compile_to_hardware drops such empty pulses.
    Return the edited sequences.
    chanBySeq is a dictionary by sequence ID to the channel object
    '''
    # Replace the barrier with ID currCtr across all channels
    # Note that this function modifies seqs in place
    # Note it takes a dict by sequence index to the channel object
    # It also takes a list of the sequence indices that are involved in this barrier

    import math
    # Calculate the length of this segment on each sequence
    # Use helper to do the actual calculation
    lengths = dict()
    for seqInd in channelIdxs:
        seq = seqs[seqInd]
        length[seqInd] = getLengthBetweenBarriers(seqInd, currCtr, prevForLengthCtr)

    # Find the max (at least 0)
    maxBlockLen = max(lengths.values() + [0])

    # If the block is of indeterminate length then later code
    # will replace these Barriers,
    # but mark the Barrier objects as having this indeterminate length
    # so we don't try to recalculate this length.
    indet = False
    if math.isnan(maxBlockLen):
       # This block is indeterminate
       indet = True
       logger.info("Wait at Barrier %s is indeterminate - later make it a sync/wait", currCtr)
       for seqInd in channelIdxs:
           markBarrierLengthCalculated(currCtr, seqInd, maxBlockLen)
       return seqs

    # For each channel that has this Barrier
    # replace the Barrier in the sequence with an Id pulse
    # on the proper channel of the length (max-localLength).
    # Then record on the Barrier object that we used an Id pulse
    # of that length. That way later code to figure out the length
    # for an enclosing pair of barriers gets the right answer.
    # The Id pulse may be of 0 length.
    for seqInd in channelIdxs:
        seq = seqs[seqInd]
        ind = getBarrierIdx(seqInd, currCtr)
        if ind < 0:
            raise Exception("Sequence %d doesn't appear to have Barrier %s!" % (seqInd, currCtr))
        channel = chanBySeq[seqInd]
        idlen = maxBlockLen - lengths[seqInd] # Length of Id pulse to pause till last channel done
        logger.info("Sequence %d: Replacing %s with Id(%s, length=%f)", seqInd, seq[ind],
                    channel, idlen)
        seq[ind] = Id(channel, idlen)
        markBarrierLengthCalculated(currCtr, ind, idlen)
    return seqs

def getPreviousUndoneBarrier(currCtr, prevCtr, seqIdx):
    '''Find the previous barrier from currCtr on sequence seqIdx
    which is not marked as lengthCalculated.
    Return None if none found.
    '''
    # For the given channel, loop up previous barriers,
    # if lengthCalculated==False, return it
    # FIXME: We're ignoring prevCtr here
    # Nominally prevCtr should have lengthCalculated=True,
    # But if it didn't, we'd want to do it
    global barriersBySeqByCtr
    barrier = barriersBySeqByCtr[seqIdx][currCtr]
    while barrier is not None and barrier != -1 and barrier['lengthCalculated']:
        barrierCtr = barrier['prevBarrierCtr']
        barrier = barriersBySeqByCtr[seqIdx].get(barrierCtr, None)
    if barrier is None or barrier == -1:
        return None
    return barrier

def getLastUnMeasuredBarrier(currCtr, prevCtr, seqIdxes):
    '''Return the last Barrier on the list of sequences
    not already marked as measured (will be WaitSome or know
    the Id pulse length)
    Return None if all are measured.
    '''
    # Across all sequences in seqIdxes
    # Start at currCtr, work back to prevCtr
    # return first barrier not marked as measured
    # FIXME: This is a depth first search. So it does not give the latest or earliest
    # such barrier, just the first we encounter. Is that OK?
    for seqIdx in seqIdxes:
        undoneBarrier = getPreviousUndoneBarrier(currCtr, prevCtr, seqIdx)
        if undoneBarrier is not None:
            return undoneBarrier
    return None

def replaceOneBarrier(currCtr, seqIdxToChannelMap, seqInd = None):
    '''Replace the barrier with id currCtr on all sequences.
    Use the version of the barrier on the given sequence seqInd if given.
    Skip barriers that are Wait or WaitSome instances.
    Recursively find intervening Barriers on any related channel that is not
    marked as 'measured' (turned into an Id or will be a WaitSome),
    and replace those first, so that we can correctly calculate
    the length for this Barrier.
    Then use the helper replaceBarrier to do the actual replacement.
    '''
    # Set seqInd and get the Barrier object for the right sequence
    if seqInd is None:
        barrier = barriersByCtr[currCtr]
        if barrier != -1:
            seqInd = barrier['seqIndex']
        else:
            seqInd = -1
    else:
        barrier = getBarrierForSeqCtr(seqInd, currCtr)

    # Get the set of channels this barrier is on
    waitChans = getBarrierChannels(currCtr)
    if waitChans == []:
        logger.warn("Barrier on no channels? Pretend %s is on current sequence %d (channel %s) where we found it", currCtr, seqInd, seqIdxToChannelMap[seqInd].label)
        waitChans = [channel]
    # Turn those Channel objects into sequence indices
    waitSeqIdxes = [ind for ind in seqIdxToChannelMap for chan in waitChans if seqIdxToChannelMap[ind] == chan]
    logger.debug("Replacing Barrier %s on channels %s, sequences %s", currCtr, waitChans, waitSeqIdxes)

    # Skip barriers that are Wait or WaitSome instances.
    if barrier != -1 and barrier.get('type', 'barrier') in ('wait', 'waitsome'):
        # do this later
        logger.info("Found wait barrier %s; handle it later", currCtr)
        # It should be true that lengthCalculated==True on this barrier
        # - across all relevant channels. Make sure.
        for idx in waitSeqIdxes:
            markBarrierLengthCalculated(currCtr, idx)
        return seqs
    
    prevForLengthCtr = getLastSharedBarrierCtr(waitChans, currCtr)
    logger.debug("Using length since barrier %s", prevForLengthCtr)

    # If there are any intervening Barriers not marked as measured on any channel
    # (not turned into an Id or identifies as indeterminate)
    # then replace them, by recursively calling this function.
    # This will recurse to get to the first such barrier when considered
    # sequentially, and then pop out until they're all handled.
    # Looping here handles the case where there are multiple channels involved.
    # We have to replace those earlier barriers, so that we can add things up
    # to get the length for this Barrier.
    undoneBarrierCtr = getLastUnMeasuredBarrier(currCtr, prevForLengthCtr, waitSeqIdxes)
    while undoneBarrierCtr:
        logger.debug("Found undone barrier %s to replace first", undoneBarrierCtr)
        seqs = replaceOneBarrier(undoneBarrierCtr, seqIdxToChannelMap)
        undoneBarrierCtr = getLastUnMeasuredBarrier(currCtr, prevForLengthCtr, waitSeqIdxes)

    # Now want all the lengths between curr and prev, and figure out min, replace as appropriate
    seqs = replaceBarrier(seqs, currCtr, prevForLengthCtr,
                          waitSeqIdxes)
    return seqs
# End of replaceOneBarrier

# TODO
# * Check for logic gaps
# * Improve documentation
# * Raise exceptions don't just log for bad things
# * How do we check that all channels start with sync/wait? Should we?
#  * Or related, do we do anything special if all channels start with a shared barrier?
# * What if we discover multiple sequential Waits or WaitSomes on same chnnels?
#  * Can we or should we remove duplicates?
# * Consider passing around data structures instead of making them globals
# * Testing, including
#  * 3+ qubits
#  * explicit WaitSomes and Waits
#  * Barrier that becomes WaitSome inside a call or a repeat or both
#  * call or goto that goes backwards or forwards (4 cases)
#  * Nested Calls
#  * Nested Repeats
#  * Nested Barriers
#  * Sequences that dont start with a barrier
def replaceBarriers(seqs, seqIdxToChannelMap):
    '''
    Replace all Barrier() instructions with Sync() and WaitSome() or Id() pulses.
    Use WaitSome() if there's some intervening indeterminate length operation,
    like a CMP() or LoadCmp().
    Otherwise pause using Id on the less busy channels.
    This modifies the sequences and returns the updated sequences.
    Assumes Barriers list the channels they are on,
    and have an ID.
    Each Barrier is used exactly once per channel during operation
    (or else has guaranteed same length since prior Barrier,
    effectively meaning it is a WaitSome).
    '''
    # Approach:
    # Walk through each sequence building up barrier objects
    # that record each barrier including length in execution time
    # since the last barrier.
    # Then walk through barriers replacing them with Id pulses
    # where possible.
    # Then replace the remaining barriers with WaitSomes
    # Barrier objects are kept in 3 dictionaries: by sequence
    # by position in the sequence (where each sequence has different
    # instance of the object), by sequence by counter (id), and
    # independent of sequence by counter (in which case this is
    # just one instance of this barrier)
    # Each barrier has its sequence, position, channels,
    # ID, previous barrier, length since previous barrier
    # (float, may be 'nan' meaning it becomes a WaitSome)
    # A barrier object that is -1 means the start
    # A barrier ID of '-1' means the start
    # A wait has a barrier ID of 'wait-<IndexInSequence>'
    # barrier position of -1 is the start

    global barriersBySeqByPos, barriersBySeqByCtr, barriersByCtr, allChannels
    logger.debug("In new replaceBarriers")
    barriersBySeqByPos = dict() # by sequence Index in seqs, by Pos index of element in sequence
    barriersBySeqByCtr = dict() # by sequence Index in seqs, by Counter ID of barrier
    barriersByCtr = dict() # by Counter ID of barrier
    allChannels = [ch for ch in seqIdxToChannelMap.values()] # actual Channel objects

    startBarrier = dict()
    startBarrier['type'] = 'start'
    startBarrier['counter'] = '-1' # notional 'start' barrier has counter '-1', pos -1
    startBarrier['seqPos'] = -1 # index in sequence
    # Have we determined the length of the Id pulse or if this is a WaitSome?
    startBarrier['lengthCalculated'] = False
    # Walking thru running of this sequence, the length since the last Barrier on this sequence,
    # including this element.
    # Note that due to other elements on other sequences, this is not the same as the length
    # of the resulting Id pulse
    startBarrier['lengthSince'] = 0
    barriersByCtr['-1'] = startBarrier

    # Loop over all sequences
    # Walk through each sequence in execution order
    # (following Call/Goto/Repeat/Return)
    # As we encounter barriers, add them to our data structures
    # We'll uses those data structures later to replace the Barriers in the sequences.
    # We track BlockLabels as we go, and of course Call and LoadRepeat
    for seqInd, seq in enumerate(seqs):
        logger.debug("Looking for barriers on sequence %d", seqInd)
        barriersBySeqByPos[seqInd] = dict()
        barriersBySeqByCtr[seqInd] = dict()

        # Put a startBarrier in the front for this channel
        startBarrier['seqIndex'] = seqInd
        barriersBySeqByPos[seqInd][-1] = startBarrier
        barriersBySeqByCtr[seqInd]['-1'] = startBarrier

        # Dict of BlockLabel's label (string) to index in sequence
        # Used to find the target of Call/Goto/Repeat calls
        # This is filled in lazily, as we find the labels.
        blockLabels = dict()

        # Times the repeat block if any is to be repeated (LIFO stack)
        rptCount = []
        # Length of sub-block before starting current repeat, if any
        rptStartLen = []
        # Index into sequence where repeat block starts
        rptStartInd = []

        # LIFO stack of index where Return (from Call) returns to (point to next thing to run)
        retInd = []

        # The previous barrier that this barrier will point to
        prevBarrierPos = -1
        prevBarrier = startBarrier
        prevBarrierCtr = '-1'

        # The total length through this element, which we'll
        # reset at each barrier
        curLen = 0
        # Is this block between 2 barriers of indeterminate length
        nonDet = False

        # default barrier type
        barrierType = 'barrier'

        # The current barrier
        curBarrier = dict()
        curBarrier['type'] = 'barrier'
        curBarrier['prevBarrierPos'] = prevBarrierPos
        curBarrier['prevBarrierCtr'] = prevBarrierCtr
        curBarrier['seqIndex'] = seqInd
        # index into the sequence of the current element
        seqPos = 0

        # Now loop over elements in the sequence
        # Note that some code blocks will reset seqPos to other points
        # to follow Call/Return/Repeat/Goto commands
        while seqPos < len(seq):
            elem = seq[seqPos]
            logger.debug("Examining %s", elem)

            # if the element is a barrier, we save the length since the last barrier and a pointer to that previous barrier
            # If it is a CMP, then this block is indeterminate length. Next barrier must say so

            # Handle all kinds of barriers by putting them in our data structures
            if isBarrier(elem) or isWaitSome(elem) or isWait(elem):
                if isBarrier(elem):
                    logger.debug("Next barrier at %d: %s", seqPos, elem)
                    curBarrier['type'] = 'barrier'
                    curBarrier['channels'] = elem.chanlist
                    curBarrier['counter'] = elem.value
                elif isWaitSome(elem):
                    # This shouldn't really happen
                    # But if previous is a Sync then treat this as a Barrier on its listed channels?
                    logger.warning("Got WaitSome %s at %d?!", elem, seqPos)
                    curBarrier['type'] = 'waitsome'
                    curBarrier['channels'] = elem.chanlist
                    curBarrier['counter'] = 'wait-%d' % seqPos
                    if not isSync(seq[seqPos-1]):
                        logger.warning("Previous element was not a sync but %s", seq[seqPos-1])
                elif isWait(elem):
                    logger.info("Got Wait %s at %d?!", elem, seqPos)
                    curBarrier['type'] = 'wait'
                    curBarrier['channels'] = allChannels
                    curBarrier['counter'] = 'wait-%d' % seqPos
                    if not isSync(seq[seqPos-1]):
                        logger.warning("Previous element was not a sync but %s", seq[seqPos-1])
                curBarrier['seqPos'] = seqPos
                curBarrier['prevBarrierPos'] = prevBarrierPos
                curBarrier['prevBarrierCtr'] = prevBarrierCtr
                curBarrier['seqIndex'] = seqInd
                if nonDet:
                    curBarrier['lengthSince'] = float('nan')
                    # For these barriers, we consider we know the length
                    # So later it's safe to skip over this barrier on other channels;
                    # getLengthBetweenBarriers will get the nan lengthSince and that's accurate
                    curBarrier['lengthCalculated'] = True

                    # Note that for nested blocks the outer barrier will become
                    # nonDet for the whole block because this one is,
                    # but the range to the next barrier may not be
                    nonDet = False # Reset for next block
                elif rptCount:
                    # We're in a Repeat block. The only way that's legal is to treat this as a Wait of some kind
                    logger.debug("%s is inside a Repeat block; treat as a Wait", elem)
                    curBarrier['lengthSince'] = float('nan')
                    # For these barriers, we consider we know the length
                    # So later it's safe to skip over this barrier on other channels;
                    # getLengthBetweenBarriers will get the nan lengthSince and that's accurate
                    curBarrier['lengthCalculated'] = True
                else:
                    curBarrier['lengthSince'] = curLen + pulseLengths(elem)
                logger.debug("Channels: %s, length: %s, counter: %s, prevBarrier: %s at %d", curBarrier['channels'], curBarrier['lengthSince'], curBarrier['counter'], curBarrier['prevBarrierCtr'], curBarrier['prevBarrierPos'])
                logger.debug(curBarrier)

                # Store this barrier
                barriersByCtr[curBarrier['counter']] = curBarrier
                barriersBySeqByPos[seqInd][seqPos] = curBarrier
                barriersBySeqByCtr[seqInd][curBarrier['counter']] = curBarrier

                # Reset vars for next barrier block
                prevBarrier = curBarrier
                prevBarrierCtr = curBarrier['counter']
                prevBarrierPos = seqPos
                # the length counter starts at 0 for the next block
                curLen = 0
                # Move to the next element in the sequence
                seqPos += 1
                continue

            # CMP
            # Note this is a nonDeterminate block
            if isCMP(elem) or isLoadCmp(elem):
                logger.info("Indeterminate length block on sequence %d; has %s at %d", seqInd, elem, seqPos)
                nonDet = True
                seqPos += 1
                curLen += pulseLengths(elem)
                continue

            # LoadRepeat
            # Goes with a later Repeat(<label>) call
            # That <label> could nominally be anywhere, but QGL2 puts it on the line after the LoadRepeat
            # Note that you can nominally nest Repeat blocks, so we keep a LIFO stack of rptCounts.
            # Inside the block of code to be repeated, you can't in general have a Barrier; the elements
            # to that barrier are different between the first and later times through the loop, so the Barrier
            # is 2 different Id blocks so it isn't a repeat.
            # Exceptions: If the element right before the block is a barrier, and the last element in the block
            # is a Barrier, or you otherwise construct things carefully, then the block is the same length.
            # Or else if the Barrier is a WaitSome (on both 1st and later times through the loop), then it is an identical
            # Pulse.
            # Put another way: you can only use a given Barrier in a single way in any channel.
            # However there's another issue with a Barrier in a Repeat block: each channel for that Barrier must use the barrier
            # the same # of times, and in the same way, such that it makes sense to line up the barrier.
            if isLoadRepeat(elem):
                if elem.value < 1:
                    logger.warning("Sequence %d at %d got %s with value %d: Treat as 1", seqInd, seqPos, elem, elem.value)
                    elem.value = 1
                logger.debug("Found %s at index %d. Length so far: %f", elem, seqPos, curLen)
                rptCount.append(elem.value)

                # Guess that the repeat will want to go to line after LoadRepeat - if not, we'll start looking there
                # for the proper destination
                rptStartInd.append(seqPos+1)

                curLen += pulseLengths(elem)

                # Store the length of this block up through this element.
                # That way when we hit the Repeat block, we can potentially calculate the length of the block being repeated,
                # and just add it, without having to re-walk
                # Here we assume that the repeat block in fact starts at the next element after this LoadRepeat
                rptStartLen.append(curLen)

                seqPos += 1
                continue

            # See note above on Repeat blocks.
            # This code allows target of repeat to be anywhere.
            # It guesses that the Repeat goes to the line after LoadRepeat (as guessed above).
            # It does nothing special about intervening Barriers; elsewhere we ensure they are Waits not Ids
            # When we get here, we've already added to curlen the result of doing this repeat block once
            if isRepeat(elem):
                curLen += pulseLengths(elem)
                if not rptCount:
                    # FIXME: Ignore instead? Use NodeError?
                    raise Exception("Sequence %d got %s at %d without a LoadRepeat" % (seqInd, elem, seqPos))

                # Get the # of times left to repeat
                rc = rptCount[-1] - 1
                logger.debug("Found %s at index %d. Remaining repeats: %d", elem, seqPos, rc)

                # If there are no more repeats, move on
                if rc <= 0:
                    # Just finished last time through the loop
                    # Clear all the repeat variables
                    rptCount.pop()
                    while len(rptStartInd) > len(rptCount):
                        rptStartInd.pop()
                    while len(rptStartLen) > len(rptCount):
                        rptStartLen.pop()
                    # Move on to the next element
                    seqPos += 1
                    continue

                # If we get here, we need to repeat that block at least once
                # Update the repeats remaining counter
                rptCount[-1] = rc

                # Do blockLabels comparison by label
                target = elem.target
                if isBlockLabel(target):
                    target = target.label

                # Find proper start index
                realRptStartInd = -1
                if target in blockLabels:
                    realRptStartInd = blockLabels[target]
                    logger.debug("Found Repeat target in cache at %d", realRptStartInd)
                else:
                    # Loop thru rest of seq to find the target. Then loop thru start of seq to here
                    found = False
                    for posNext in range(seqPos, len(seq)):
                        if isBlockLabel(seq[posNext]) and seq[posNext].label == target:
                            blockLabels[target] = posNext
                            realRptStartInd = posNext
                            found = True
                            logger.debug("Found Repeat target in rest of sequence at %d", realRptStartInd)
                            break
                    if not found:
                        for posNext in range(0, seqPos):
                            if isBlockLabel(seq[posNext]) and seq[posNext].label == target:
                                blockLabels[target] = posNext
                                realRptStartInd = posNext
                                found = True
                                logger.debug("Found target in first part of sequence at %d", realRptStartInd)
                                break
                    if not found:
                        raise Exception("Sequence %d at %d: Failed to find %s target '%s'" % (seqInd, seqPos, elem, elem.target))

                # If the start of the repeat block is same as that in rptStartInd,
                # then use curlen-rptStartLen as length of block to repeat.
                # Mutiply that by rc and add to curlen
                # Then clear the rpt LIFOs and move on
                if rptStartInd[-1] == realRptStartInd:
                    # We guessed correctly where to start repeat from
                    rs = rptStartLen.pop()
                    rptAdd = (curLen - rs) * rc
                    logger.debug("Stashed startElemInd matches target. Finish by adding (curlen %f - startLen %f) * repeatsToGo %d = %f", curLen, rs, rc, rptAdd)
                    curLen += rptAdd

                    # Just finished last time through the loop
                    # Clear all the repeat variables
                    rptCount.pop()
                    while len(rptStartInd) > len(rptCount):
                        rptStartInd.pop()
                    while len(rptStartLen) > len(rptCount):
                        rptStartLen.pop()
                    # Move on to the next element
                    seqPos += 1
                    continue
                else:
                    # If the 2 are different, then reset rptStartInd to what we found, reset repeatStartLen to curlen, set seqPos to rptStartInd
                    logger.debug("Repeat started at %d for target %s, not guessed %d; going back", realRptStartInd, elem.target, rptStartElem[-1])
                    # We already reset the repeat counter properly
                    # Reset the startInd to be the proper one
                    # And reset the length for before the repeat to the length to this point
                    rptStartLen[-1] = curLen
                    rptStartInd[-1] = realRptStartInd
                    # Then continue from that starting point
                    seqPos = realRptStartInd
                    continue
            # End of handling Repeat

            # Handle Return
            # This jumps back to the last Call
            # Note that Call/Return blocks could be nested,
            # and due to a Goto, the 'Return' may go to something later in the sequence.
            # Note that if there is a Barrier inside a Call block, what does it mean to hit that Barrier
            # twice? As in the comment above for Repeat, unless things are identical across channels,
            # how do you line up the Barriers?
            # So in general, a Barrier, including one inside a Call block, should only be called once
            if isReturn(elem):
                # Should have seen a previous call
                # NOTE: If there was a barrier inside that block, we better only have called this block once
                curLen += pulseLengths(elem)
                if not retInd:
                    raise Exception("Sequence %d at %d: Have no saved index to go back to for %s" % (seqInd, seqPos, elem))
                ri = retInd.pop()
                logger.debug("Got %s: Returning to saved index %d", elem, ri)
                seqPos = ri
                continue

            # Handle Call() or Goto()
            # Both take a BlockLabel to jump to.
            # Call() requires stashing the index after it to return to.
            if isCall(elem) or isGoto(elem):
                logger.debug("Got %s at %d - will jump to %s", elem, seqPos, elem.target)
                # Call is slightly special
                if isCall(elem):
                    if seqPos+1 == len(seq):
                        # The return would try to go to something off the end. That won't work.
                        raise Exception("Call() is last element in sequence %d: %s" % (seqInd, elem))
                    logger.debug("Next Return will go to %d", seqPos+1)
                    # stash away seqPos+1 as the next place to return
                    retInd.append(seqPos+1)

                # Do BlockLabels comparison by label
                target = elem.target
                if isBlockLabel(target):
                    target = target.label
                curLen += pulseLengths(elem)
                if target in blockLabels:
                    seqPos = blockLabels[target]
                    logger.debug("Found target in cache at %d", seqPos)
                    continue

                # Didn't find the target yet. Look.
                # Loop thru rest of seq. Then loop thru start of seq to here
                found = False
                for posNext in range(seqPos, len(seq)):
                    if isBlockLabel(seq[posNext]) and seq[posNext].label == target:
                        blockLabels[target] = posNext
                        seqPos = posNext
                        found = True
                        logger.debug("Found target in rest of sequence at %d", seqPos)
                        break
                if found:
                    continue
                for posNext in range(0, seqPos):
                    if isBlockLabel(seq[posNext]) and seq[posNext].label == target:
                        blockLabels[target] = posNext
                        seqPos = posNext
                        found = True
                        logger.debug("Found target in first part of sequence at %d", seqPos)
                        break
                if found:
                    continue
                else:
                    raise Exception("Sequence %d at %d: Failed to find %s target '%s'" % (seqInd, seqPos, elem, elem.target))

            # BlockLabel
            # Save where this was in case it's a target for a Call/Goto/Repeat,
            # otherwise it's a normal element.
            if isBlockLabel(elem):
                curLen += pulseLengths(elem)
                # Stash away that label in case some Call/Goto/Repeat needs it
                blockLabels[elem.label] = seqPos
                seqPos += 1
                continue

            # Default
            logger.debug("'%s' is a normal element - add its length (%f) and move on", elem, pulseLengths(elem))
            curLen += pulseLengths(elem)
            seqPos += 1
            continue
        # Done looking at elements in this sequence
        
        logger.debug("Done looking for Barriers on sequence %d", seqInd)
        # Now we'll move to the next channel
    # End of loop over channels
    logger.debug("Done looking for Barriers on all sequences")
    # At this point we've looked at every element in every sequence, adding up the lengths.
    # This data is saved away in barrier objects for use to use next.
    
    # And here is the main code to use the above functions and replace all barriers.

    # First we replace Barriers that turn into Id pulses
    # - because thats a 1 for 1 replacement (doesn't screw up saved indices)
    # For each sequence, start at the 'start' barrier and go to 'next'
    # where the next is a Barrier that is still in the sequence
    # and not marked as already calculated (if still there but marked
    # calculated it is turning into a WaitSome)
    # When we have such a barrier, replace it.
    # Note however that replacing a Barrier potentially requires
    # first replacing some other barriers on other channels.
    # EG if for q1 B3 links up with q3 and the last common is B0, but B1 and B2 are only on
    # the q3 program, then for q3 to get the length up to B3,
    # it needs to do B1 and B2 first.
    # so replaceOneBarrier hides that recursion.
    for seqInd in seqIdxToChannelMap.keys():
        currCtr = '-1'
        logger.debug("Handling Barriers on sequence %d", seqInd)
        currCtr = getNextBarrierCtr(seqs, seqInd, currCtr)
        while (currCtr != '-1'): # While there's another barrier
            logger.info("Replacing Barrier %s found on sequence %d", currCtr, seqInd)
            # replace that barrier, plus any other barriers (on other channels)
            # necessary to calculate the length of the Id pulse here
            seqs = replaceOneBarrier(currCtr, seqIdxToChannelMap, seqInd)
            # Move on to the next barrier
            currCtr = getNextBarrierCtr(seqs, seqInd, currCtr)
    # When we get here, we ran out of barriers that turn into Id pulses to replace
    logger.debug("Done swapping non Wait Barriers")
  
    # Now change any remaining barriers into Sync/WaitSome pairs
    for seqInd in barriersBySeqByPos:
        if seqInd not in seqs:
            logger.warn("No such channel %d?", seqInd)
            continue
        logger.debug("Swapping remaining Barriers on sequence %d with Sync/WaitSome", seqInd)
        seq = seqs[seqInd]
        # Count how many of these swaps we've done
        # Because that's the # of extra elements we're inserting, so it is the
        # amount that our saved indices are off
        swapCnt = 0
        # loop over our previous stash of barriers on this sequence
        for barrierInd in barriersBySeqByPos[seqInd].keys():
            # The new actual index of this element in the sequence
            bInd = barrierInd + swapCnt
            barrier = barriersBySeqByPos[seqInd][barrierInd]
            bType = barrier.get('type', 'barrier')
            bChannels = getBarrierChannels(barrier['counter'])
            if bInd >= len(seq):
                raise Exception("Calculated index of barrier %s (%d, was originally %d) is past end of sequence %d" % (barrier['counter'], bInd, barrierInd, seqInd))

            # Make sure it's a barrier still
            if isinstance(seq[bInd], QGL.ControlFlow.Barrier):
                if bType == 'wait' or bChannels == allChannels:                    
                    logger.info("Replacing sequence %d index %d (%s) with Sync();Wait()", seqInd, bInd, seq[bInd])
                    # Replace
                    seqs[seqInd] = seq[:bInd] + [Sync(), Wait()] + seq[bInd+1:]
                else:
                    logger.info("Replacing sequence %d index %d (%s) with Sync(); WaitSome(%s)", seqInd, bInd, seq[bInd], bChannels)
                    seqs[seqInd] = seq[:bInd] + [Sync(), WaitSome(bChannels)] + seq[bInd+1:]
            else:
                logger.debug("Spot %d in sequence %d (channel %s) not (no longer) a barrier, but: %s", barrierInd, seqInd, seqIdxToChannelMap[seqInd], seq[barrierInd])
                continue
        logger.debug("Swapped %d barriers on sequence %d", swapCnt, seqInd)
        # Now to next sequence
    # Done swapping remaining barriers for Sync/Waits

    # Now all Barriers should be gone.
    for sidx, seq in enumerate(seqs):
        for idx in range(len(seq)):
            if isBarrier(seq[idx]):
                logger.warn("Sequence %d still has %s at %d!", sidx, seq[idx], idx)
    logger.debug("Done replacing Barriers")
    return seqs
# End of replaceBarriers

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
