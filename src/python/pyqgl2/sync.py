# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
Add synchronization primitives

Mark off the start and end of each concurrent block for each channel
with a Barrier() message. These are points at which all channels should be brought
in sync with each other.
Later (evenblocks.py) we'll calculate the per channel length of the sequence segment up
to the barrier, and insert pauses (Id pulses of proper length) where necessary to keep
all sequences in sync.
Note that we can only do that where we can determine the length.
Where the length is indeterminate (say, the control flow depends on the result of a 
quantum measurement), we must do a Sync (send a message saying this channel is done) and a wait 
(wait for the global return message saying all channels are done). Note that this takes more time,
so we prefer the sleeps.

"""

import ast

from copy import deepcopy

import pyqgl2.ast_util

from pyqgl2.ast_util import NodeError
from pyqgl2.ast_util import ast2str, copy_all_loc, expr2ast

from pyqgl2.concur_unroll import is_concur, is_seq, find_all_channels

# Global ctr of next Barrier() message
BARRIER_CTR = 0

class SynchronizeBlocks(ast.NodeTransformer):
    """
    Add a Barrier to the start and end of each seq block within each concur block

    Note that before processing is done, we add an empty seq block for
    each channel for which there is not a seq block in a given concur
    block, so that we can add Barriers for that channel, to keep that channel lined
    up with the others.

    For example, if we had the following trivial program:

        with concur:
            with seq:
                X90(QBIT_1)
            with seq:
                Y90(QBIT_2)
        with concur:
            with seq:
                X90(QBIT_2)
            with seq:
                Y90(QBIT_3)

    In the first concur block, only QBIT_1 and QBIT_2 are "busy", but
    QBIT_3 will need to wait for the others to complete so it can start
    in sync with QBIT_2 when it is time.
    And if those blocks were of indeterminate length, we'd be using SYNC 
    and WAIT. Currently that WAIT needs all channels to report in, so we
    need QBIT_3 to do the SYNC as well.
    Similarly, in the second concur
    block, only QBIT_2 and QBIT_3 are "busy", but QBIT_1 will need to
    process any SYNC/WAIT as well.  (since the second block is the final
    block in this program, QBIT_1 does not really need to synchronize
    with the other channels, since no other operations follow, but
    if the program continued then this synchronization would be
    important)

    Therefore, this will expand to:

        with concur:
            with seq:
                Barrier()
                X90(QBIT_1)
                Barrier()
            with seq:
                Barrier()
                Y90(QBIT_2)
                Barrier()
            with seq: # for QBIT_3
                Barrier()
                Barrier()
        with concur:
            with seq: # For QBIT_1
                Barrier()
                Barrier()
            with seq:
                Barrier()
                X90(QBIT_2)
                Barrier()
            with seq:
                Barrier()
                Y90(QBIT_3)
                Barrier()

    Later, those Barrier() messages will become Id or Sync and Wait pulses.
    """

    def __init__(self, node):

        # The set all all channels observed in the input AST
        #
        self.all_channels = find_all_channels(node)

        self.blank_barrier_ast = expr2ast('Barrier()')

    def visit_With(self, node):

        if is_concur(node):
            return self.concur_wait(node)
        else:
            return self.generic_visit(node)

    def concur_wait(self, node):
        """
        Synchronize the start of each seq block within a concur block,

        Add seq blocks for any "missing" channels so we can
        add a Barrier instruction for each of them as well
        """
        global BARRIER_CTR

        # This method will be destructive, unless we make a new
        # copy of the AST tree first
        #
        node = deepcopy(node)

        seen_channels = set()

        # Channels in this with_concur
        concur_channels = find_all_channels(node)

        # For creating the Barriers, we want QGL1 scoped variables that will be real channel instances.
        # We basically have that already.
        real_chans = set()
        for chan in concur_channels:
            real_chans.add(chan)

        start_barrier = BARRIER_CTR
        end_barrier = start_barrier + 1
        BARRIER_CTR += 2

        for stmnt in node.body:
            if not is_seq(stmnt):
                NodeError.error_msg(stmnt,
                        'non-seq block inside concur block?')
                return node

            seq_channels = find_all_channels(stmnt)

            if seq_channels.intersection(seen_channels):
                NodeError.error_msg(stmnt,
                        'seq blocks have overlapping channels')
                return node

            seen_channels = seen_channels.union(seq_channels)

            chan_name = ','.join(seq_channels)

            # mark stmnt with chan_name or seq_channels in another way
            if hasattr(stmnt, 'qgl_chan_list'):
                oldChanSet = set(stmnt.qgl_chan_list)
                newChanSet = seq_channels
                oldMissing = newChanSet - oldChanSet
                oldExtra = oldChanSet - newChanSet
                if len(oldMissing) > 0:
                    NodeError.diag_msg(stmnt, 'marked chan list %s was missing %s' % (str(oldChanSet), str(oldMissing)))
                if len(oldExtra) > 0:
                    NodeError.diag_msg(stmnt, 'marked chan list %s had extra %s' % (str(oldChanSet), str(oldExtra)))
            NodeError.diag_msg(stmnt, 'Marking chan list %s' % (str(seq_channels)))
            stmnt.qgl_chan_list = list(seq_channels)

            new_seq_body = list()

            # Helper to ensure the string we feed to AST doesn't put quotes around
            # our Qubit variable names
            def appendChans(bString, chans):
                bString += '['
                first = True
                for chan in chans:
                    if first:
                        bString += str(chan)
                        first = False
                    else:
                        bString += "," + str(chan)
                bString += ']'
                return bString

            # Add global ctr, chanlist=concur_channels
            # FIXME: Hold concur_channels as a string? List?
            bstring = 'Barrier("%s", ' % str(start_barrier)
            bstring = appendChans(bstring, list(real_chans))
            bstring += ')\n'
            barrier_ast = expr2ast(bstring)
            # barrier_ast = expr2ast('Barrier(%s, %s)\n' % (str(start_barrier), list(real_chans)))
            copy_all_loc(barrier_ast, node)
            barrier_ast.channels = concur_channels
            # print("*****Start barrier: %s" % pyqgl2.ast_util.ast2str(barrier_ast))

            new_seq_body.append(barrier_ast)

            new_seq_body += stmnt.body

            bstring = 'Barrier("%s", ' % str(end_barrier)
            bstring = appendChans(bstring, list(real_chans))
            bstring += ')\n'
            end_barrier_ast = expr2ast(bstring)
            #end_barrier_ast = expr2ast('Barrier(%s, %s)\n' % (str(end_barrier), list(real_chans)))
            copy_all_loc(end_barrier_ast, node)
            # Add global ctr, chanlist=concur_channels
            end_barrier_ast.channels = concur_channels

            # print('End AST: %s' % ast2str(end_barrier_ast))

            new_seq_body.append(end_barrier_ast)

            stmnt.body = new_seq_body

        # FIXME: In new thinking, is the proper unseen set the global one,
        # Or only those local to this with concur. I think only local
        for unseen_chan in concur_channels - seen_channels:
            #print('DIAG %s' % ast2str(stmnt))
            NodeError.diag_msg(stmnt,
                    'channels unreferenced in concur: %s' % str(unseen_chan))

            bstring = 'with seq:\n    Barrier("%s", ' % str(start_barrier)
            bstring = appendChans(bstring, list(real_chans))
            bstring += ')\n    Barrier("%s",' % str(end_barrier)
            bstring = appendChans(bstring, list(real_chans))
            bstring += ')\n'
            empty_seq_ast = expr2ast(bstring)
            # print('Empty AST: %s' % ast2str(empty_seq_ast))
            # empty_seq_ast = expr2ast(
            #         'with seq:\n    Barrier(%s, %s)\n    Barrier(%s, %s)' % (str(start_barrier), list(real_chans), str(end_barrier), list(real_chans)))

            # Mark empty_seq_ast with unseen_chan
            empty_seq_ast.qgl_chan_list = [unseen_chan]
            copy_all_loc(empty_seq_ast, node)
            node.body.append(empty_seq_ast)

        return node

if __name__ == '__main__':

    def test_code(code_text):
        tree = ast.parse(code_text, mode='exec')
        sync = SynchronizeBlocks(tree)
        new = sync.visit(deepcopy(tree))
        print('ORIG\n%s\n=>\n%s' % (ast2str(tree), ast2str(new)))

    def t1():
        code = """
with concur:
    with seq:
        X90(QBIT_1)
    with seq:
        Y90(QBIT_2)
with concur:
    with seq:
        X90(QBIT_2)
    with seq:
        Y90(QBIT_3)
with concur:
    with seq:
        X90(QBIT_4)
"""

        test_code(code)

    def main():

        t1()

    main()

