'''
Utilities for creating a basic channel configuration for testing.
'''

from pyqgl2.main import mapQubitsToSequences
from pyqgl2.evenblocks import replaceBarriers
from QGL.PulseSequencer import Pulse

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

def testable_sequence(seqs):
    '''
    Transform a QGL2 result function output into something more easily testable,
    by replacing barriers and discarding zero length Id's.
    '''
    seqIdxToChannelMap, _ = mapQubitsToSequences(seqs)
    seqs = replaceBarriers(seqs, seqIdxToChannelMap)
    discard_zero_Ids(seqs)
    return seqs
