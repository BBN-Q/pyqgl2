# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# Note: This code is QGL not QGL2

# This file contains code to replace Wait instructions with appropriate Id()
# pulses to make channels line up without using a Wait where possible.
# See replaceWaits().

# Some assumptions:
# * All channels have identical # of Waits
# * LoadRepeat comes before label and before the Repeat
# * Currently, cannot be a Wait between the start label and the Repeat
#   * That must change
# * Currently Call must go to something later.
#   * That must change
# * Currently, cannot be a Wait between Call and its Return
#   * That must change
# * When all channels start with a Wait, leave that Wait alone

from QGL.ControlFlow import Goto, Call, Return, LoadRepeat, Repeat, Wait, LoadCmp, Sync, ComparisonInstruction, ControlInstruction
from QGL.PulseSequencer import Pulse, CompositePulse, PulseBlock
from QGL.PulsePrimitives import Id

import logging

logger = logging.getLogger('QGL.Compiler.qgl2')

# Convenience functions to identify pulse/control elements
def isWait(pulse): return isinstance(pulse, Wait)
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
        return lenRes
    if isinstance(pulses, list) or isinstance(pulses, tuple):
        if len(pulses) == 0:
            return lenRes
        for pulse in pulses:
            lenRes += pulseLengths(pulse)
        return lenRes
    if isinstance(pulses, Pulse) or isinstance(pulses, CompositePulse) \
       or isinstance(pulses, PulseBlock) or isinstance(pulses, ControlInstruction):
        return pulses.length

    # Not a pulse or list of pulses that we know how to handle
    # FIXME! Raise some kind of error?
    # Or are there pulse like things in there that we should ignore?
    logger.warning("Unknown sequence element %s assumed to have length 0", pulses)
    return lenRes

def replaceWaits(seqs, seqIdxToChannelMap):
    '''Where sequences have lined up Waits where the time to reach the Wait
    is deterministic, replace the Wait with appropriate length Id pulses to 
    keep things lined up.'''

    # How many waits are there
    waitCnt = 0
    # Which wait are we handling - marks end of current subblock
    curWait = 0
    # 0 based index into the sequence of next element/pulse to look at
    startCursorBySeqInd = dict()
    # List of indexes into sequences of Waits for each sequence
    waitIdxesBySeqInd = dict()

    # First loop over each sequence, building up a count of waits in each and a dict by seqInd with the indices of the waits.
    for seqInd, seq in enumerate(seqs):
        startCursorBySeqInd[seqInd] = 0
        waitIdxes = list()
        for ind, elem in enumerate(seq):
            if isWait(elem):
                waitIdxes.append(ind)
        waitIdxesBySeqInd[seqInd] = waitIdxes

    # If some sequence has a different number of Waits, we can't do these replacements
    maxWait = max([len(waitIdxesBySeqInd[i]) for i in waitIdxesBySeqInd])
    minWait = min([len(waitIdxesBySeqInd[i]) for i in waitIdxesBySeqInd])
    if maxWait != minWait:
        # Some sequence has diff # of waits
        logger.info("Cannot replace any Waits with pause (Id) pulses; # Waits ranges from %d to %d", minWait, maxWait)
        return seqs

    # All sequences have this # of waits for us to process
    waitCnt = maxWait
    logger.debug("\nSequences have %d waits", waitCnt)

    # If all sequences start with a wait, skip it
    if waitCnt > 0 and all([isWait(seq[0]) for seq in seqs]):
        logger.debug("Skipping a wait at spot %d", curWait)
        curWait += 1

    if curWait < waitCnt and all([isWait(seq[curWait]) for seq in seqs]):
        # More than 2 waits at start of every sequence!?
        logger.warning("All sequences start with more than 1 Wait?")

    # If we skipped some waits and there is more to do,
    # Then push forward the cursor for each sequence where we'll start in measuring
    # lengths
    if curWait > 0 and curWait < waitCnt:
        logger.debug("Skipped some waits. Now at wait %d of %d", curWait, waitCnt)
        for seqInd, seq in enumerate(seqs):
            startCursorBySeqInd[seqInd] = waitIdxesBySeqInd[seqInd][curWait - 1] + 1

    # Store the length of the current sub-segment for each sequence
    curSeqLengthBySeqInd = dict()

    logger.debug("Ready to loop over %d wait blocks", waitCnt - curWait)

    # Now loop over each sub-segment
    # That is, the pulses after the last Wait and up through the next wait
    # For each, we have to count up the length in each sequence, handling repeats/gotos
    # And if we find something we don't know how to handle, we need to skip to the end of this Wait block,
    # leaving the Wait in place
    while curWait < waitCnt:
        logger.debug("Starting wait block %d", curWait)
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

            # Index into this sequence of the next Wait command
            nextWaitInd = waitIdxesBySeqInd[seqInd][curWait]
            # Index into sequence where we are currently looking
            # starts at startCursorBySeqInd
            curInd = startCursorBySeqInd[seqInd]

            # Now look at each seq element from the current spot (curInd) up to nextWaitInd (index of next Wait)
            while curInd <= nextWaitInd:
                elem = seq[curInd]

                # If we reached the end, stop (should be Wait)
                if isWait(elem):
                    if curInd == nextWaitInd:
                        logger.debug("Got up to next Wait at index %d", curInd)
                        curlen += pulseLengths(elem)
                        break # out of this while loop
                    else:
                        raise Exception("Sequence %d found unexpected %s at %d. Didn't expect it until %d" % (seqInd, elem, curInd, nextWaitInd))
                elif curInd == nextWaitInd:
                    raise Exception("Sequence %d found unexpected %s at %d. Expected Wait" % (seqInd, elem, curInd))

                # If this is a comparison of some kind,
                # then this block is of indeterminate length,
                # so we can't replace the Wait
                if isCMP(elem) or isLoadCmp(elem):
                    logger.info("Indeterminate length block due to sequence %d has %s at %d", seqInd, elem, curInd)
                    nonDet = True
                    break

                # If this is repeat / loadrepeat
                # NOTE: Here I assume that a Wait in the middle of a repeat block is illegal
                if isLoadRepeat(elem):
                    if elem.value < 1:
                        # FIXME: raise Exception instead?
                        logger.warning("Sequence %d at %d got %s with value %d: Treat as 1", seqInd, curInd, elem, elem.value)
                        elem.value = 1
                    logger.debug("Found %s for %d at %d. Len so far: %d", elem, elem.value, curInd, curlen)
                    rptCnt.append(elem.value)

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
                    # When we get here, we've already added to curLen the result of doing this once
                    if not rptCnt:
                        # FIXME: Ignore instead? Use NodeError?
                        raise Exception("Sequence %d got %s at %d without a LoadRepeat" % (seqInd, elem, curInd))

                    # Get the # of times left to repeat
                    rc = rptCnt[len(rptCnt)-1] - 1
                    logger.debug("Found %s at %d target %s. Remaining repeats %d", elem, curInd, elem.target, rc)

                    # If there are no more repeats, move on
                    if rc <= 0:
                        # Just finished last time through the loop
                        # Clear all the repeat variables
                        rptCnt.pop()
                        while len(rptStartInd) > len(rptCnt):
                            rptStartInd.pop()
                        while len(rptStartElem) > len(rptCnt):
                            rptStartElem.pop()
                        rptStartLen.pop()
                        # Move on to the next element
                        curInd += 1
                        continue

                    # If we get here, we need to repeat that block at least once
                    # Update the repeats remaining counter
                    rptCnt[len(rptCnt)-1] = rc

                    # Back when we got the LoadRepeat (or looked back to find target), we guessed where to start from
                    # If the guess is still in place and matches what we want, just use that and move on
                    if len(rptCnt) == len(rptStartElem) and rptCnt[len(rptCnt)-1] and elem.target == rptStartElem[len(rptStartElem)-1]:
                        # We guessed correctly where to start repeat from
                        rs = rptStartLen.pop()
                        rptAdd = (curLen - rs) * rc
                        logger.debug("Stashed startElem matches target. Finish by adding (curlen %d - startLen %d) * repeatsToGo %d = %d", curlen, rs, rc, rptAdd)
                        curlen += rptAdd

                        # Just finished last time through the loop
                        # Clear all the repeat variables
                        rptCnt.pop()
                        while len(rptStartInd) > len(rptCnt):
                            rptStartInd.pop()
                        while len(rptStartElem) > len(rptCnt):
                            rptStartElem.pop()
                        while len(rptStartLen) > len(rptCnt):
                            rptStartLen.pop()
                        # Move on to the next element
                        curInd += 1
                        continue
                    else:
                        logger.debug("Go back to look for target (wasn't stashed guess %s)", rptStartElem[len(rptStartElem)-1])
                        # Go back to find the blocklabel to repeat from
                        # We go back to rptStartInd and loop forward until we find elem.target.
                        # Then set curInd to that ind, set startElem to the elem.target
                        # and set StartLen to curLen
                        rptStartElem[len(rptStartElem)-1] = elem.target
                        rptStartLen[len(rptStartLen)-1] = curLen
                        idx = rptStartInd[len(rptStartInd)-1]
                        while idx < curInd and seq[idx] != elem.target:
                            idx += 1
                        if idx == curInd:
                            logger.warning("Failed to find %s target %s in sequence %d from %d to %d - cannot repeat", elem, elem.target, seqInd, rptStartInd[len(rptStartInd)-1], curInd)
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
                    # Note we assume no intervening Wait.
                    callTarget = elem.target
                    retInd.append(curInd+1)
                    logger.debug("Got %s at %d pointing at %s", elem, curInd, elem.target)
                    curlen += pulseLengths(elem)

                    # Look for the call target from here forward to next Wait
                    foundTarget = False
                    for ind2, e2 in enumerate(seq[curInd+1:nextWaitInd-1]):
                        if e2 == callTarget:
                            curInd = ind2
                            foundTarget = True
                            break
                    if foundTarget:
                        # reset pointer so next loop will start where Call pointed
                        logger.debug("Jumping to target at %d", curInd)
                        continue
                    # FIXME: Exception? Log and continue?
                    raise Exception("Sequence %d at %d: Failed to find %s target %s from there to next wait at %d" % (seqInd, curInd, elem, elem.target, nextWaitInd-1))

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
                    for ind2, e2 in enumerate(Seq[curInd+1:nextWaitInd-1]):
                        if e2 == gotoElem:
                            curInd = ind2
                            foundTarget = True
                            break
                    if foundTarget:
                        logger.debug("Jumping to target at %d", curInd)
                        continue
                    # FIXME: Exception or log and continue?
                    raise Exception("Sequence %d at %d: Failed to find %s target %s from there to next wait at %d" % (seqInd, curInd, elem, elem.target, nextWaitInd-1))

                # Normal case: Add length of this element and move to next element
                logger.debug("%s is a normal element - add its length and move on", elem)
                curlen += pulseLengths(elem)
                curInd += 1
            # End of while loop over elements in this block in this sequence

            # If this was nonDet, stop looping over sequences for this block
            if nonDet:
                break

            # Record the length we found
            curSeqLengthBySeqInd[seqInd] = curlen

            # I want us to be pointing at the final wait now: Make sure
            if not isWait(seq[curInd]) or not curInd == nextWaitInd:
                raise Exception("Sequence %d: Expected when done with walking a wait block to be pointing at that last wait but stopped at %d:%s not %d:%s" % (seqInd, curInd, seq[curInd], nextWaitInd, seq[nextWaitInd]))

            # Push forward where we'll start for next block in this sequence
            startCursorBySeqInd[seqInd] = curInd
        # End of loop over sequences for this block

        # If we found this block was indeterminate, push to next block without doing anything
        if nonDet:
            logger.debug("That Wait block was indeterminate length - moving on")
        else:
            # Now replace Waits
            # In each sequence we should currently be pointing at the last wait (in startCursorBySeqInd)
            # We now have block lengths for each sequence
            seqs = replaceWait(seqs, startCursorBySeqInd, curSeqLengthBySeqInd, seqIdxToChannelMap)
            # When done with sub segments would/should remove empty Id pulses, BUT....
            # * compile_to_hardware already does this, so don't do it again

        # Move all start pointers past the Wait that ended that block
        for sidx2, s2 in enumerate(seqs):
            startCursorBySeqInd[sidx2] = waitIdxesBySeqInd[sidx2][curWait]+1

        # Move on to next sub segment / wait block
        curWait += 1
    # End of while loop over wait blocks

    # Now we have replaced Waits with Id pulses where possible
    logger.debug("Done replacing Waits with Ids where possible.\n")
    return seqs

def replaceWait(seqs, inds, lengths, chanBySeq):
    '''Replace the wait at the given inds (indexes) in all sequences with the proper Id pulse'''
    maxBlockLen = max(lengths.values())
    for seqInd, seq in enumerate(seqs):
        ind = inds[seqInd] # Index of the Wait
        idlen = maxBlockLen - lengths[seqInd] # Length of Id pulse to pause till last channel done
        logger.info("Sequence %d: Replacing %s with Id(%s, length=%d)", seqInd, seq[ind],
                    chanBySeq[seqInd], idlen)
        seq[ind] = Id(chanBySeq[seqInd], idlen)
    return seqs
