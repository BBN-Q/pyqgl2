'''
Utilities for creating a basic channel configuration for testing.
'''

from pyqgl2.main import mapQubitsToSequences
from pyqgl2.evenblocks import replaceBarriers
from QGL.PulseSequencer import Pulse, CompositePulse
from QGL.PatternUtils import flatten
import collections

def discard_zero_Ids(seqs):
    # assume seqs has a structure like [[entry0, entry1, ..., entryN]]
    for seq in seqs:
        ct = 0
        while ct < len(seq):
            entry = seq[ct]
            if isinstance(entry, Pulse) and entry.label == "Id" and entry.length == 0:
                del seq[ct]
            else:
                ct += 1

# Things like echoCR create lists of pulses that need to be flattened
# before calling compile_to_hardware
def flattenSeqs(seqs):
    nseqs = []
    for seq in seqs:
        hasList = False
        for el in seq:
            if isinstance(el, collections.Iterable) and not isinstance(el, (str, Pulse, CompositePulse)) :
                hasList = True
                break
        if hasList:
            newS = []
            for el in flatten(seq):
                newS.append(el)
            nseqs.append(newS)
        else:
            nseqs.append(seq)
    return nseqs

def testable_sequence(seqs):
    '''
    Transform a QGL2 result function output into something more easily testable,
    by replacing barriers and discarding zero length Id's and
    flattening pulse lists.
    '''
    seqIdxToChannelMap, _ = mapQubitsToSequences(seqs)
    seqs = replaceBarriers(seqs, seqIdxToChannelMap)
    discard_zero_Ids(seqs)
    seqs = flattenSeqs(seqs)
    return seqs
