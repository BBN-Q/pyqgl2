# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
Add synchronization primitives

The long-term goal is to replace waits (which involve global
synchronization) with sleeps (which just pause the local engine
by holding the identity signal for a given length of time)
wherever possible, to avoid the overhead of the global sync.

In the short run, however, we're just going to use waits.

The beginning of each program, and the start of each concur
block after the start of the program, are synchronized.
"""

import ast

from copy import deepcopy

import pyqgl2.ast_util

from pyqgl2.ast_util import NodeError
from pyqgl2.ast_util import ast2str

from pyqgl2.concur_unroll import is_concur, is_seq, find_all_channels


class SynchronizeBlocks(ast.NodeTransformer):
    """
    Add a WAIT to the start of each seq block within each concur block

    Note that before processing is done, we add an empty seq block for
    each channel for which there is not a seq block in a given concur
    block, so that we can add a WAIT for that channel.  This is necessary
    because in the current architecture, each WAIT is broadcast, and
    therefore each channel has to absorb the WAIT message, even if
    has nothing else to do at a given moment.

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
    QBIT_3 will receive and need to process any WAIT message sent to
    synchornize QBIT_1 and QBIT_2.  Similarly, in the second concur
    block, only QBIT_2 and QBIT_3 are "busy", but QBIT_1 will need to
    process the WAIT as well.  (since the second block is the final
    block in this program, QBIT_1 does really need to synchronize
    with the other channels, since no other operations follow, but
    if the program continued then this synchronization would be
    important)

    Therefore, this will expand to:

        with concur:
            with seq:
                WAIT(QBIT_1)
                X90(QBIT_1)
                SYNC()
            with seq:
                WAIT(QBIT_2)
                Y90(QBIT_2)
                SYNC()
            with seq:
                WAIT(QBIT_3)
        with concur:
            with seq:
                WAIT(QBIT_1)
            with seq:
                WAIT(QBIT_2)
                X90(QBIT_2)
                SYNC()
            with seq:
                WAIT(QBIT_3)
                Y90(QBIT_3)
                SYNC()

    Note that the channel operand of WAIT is only used to assign
    the operation to a channel, and is not part of the actual
    instruction.
    """

    def __init__(self, node):

        # The set all all channels observed in the input AST
        #
        self.all_channels = find_all_channels(node)

    def visit_With(self, node):

        if is_concur(node):
            if self.concur_needs_wait(node):
                return self.concur_wait(node)
            else:
                NodeError.error_msg(stmnt,
                        'unimplemented support for non-WAIT concur')
                return node
        else:
            return self.generic_visit(node)

    def concur_needs_wait(self, node):
        """
        Return True if the concur requires a WAIT for synchronization
        (instead of using a delay-based sync)

        Currently we don't do delay-based sync, so this always
        returns True
        """

        return True

    def concur_wait(self, node):
        """
        Synchronize the start of each seq block within a concur block,

        Add seq blocks for any "missing" channels so we can
        add a WAIT instruction for each of them as well
        """

        # This method will be descructive, unless we make a new
        # copy of the AST tree first
        #
        node = deepcopy(node)

        seen_channels = set()

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

            new_seq_body = list()
            wait_ast = ast.parse('WAIT(%s)' % chan_name, mode='exec')
            pyqgl2.ast_util.copy_all_loc(wait_ast, stmnt)
            new_seq_body.append(wait_ast)

            new_seq_body += stmnt.body

            # We don't really need to sync unless we've started
            # playing a waveform.  Is it an error if we do this
            # unnecessarily?  (or is it just slow?)  TODO: review
            #
            # It might not be worth worrying about this because
            # ordinarily there will be at least one waveform
            # per seq block (I think)
            #
            sync_ast = ast.parse('SYNC()', mode='exec')
            pyqgl2.ast_util.copy_all_loc(sync_ast, new_seq_body[-1])

            new_seq_body.append(sync_ast)

            stmnt.body = new_seq_body

        for unseen_chan in self.all_channels - seen_channels:
            NodeError.diag_msg(stmnt,
                    'channels unreferenced in concur: %s' % str(unseen_chan))

            empty_seq_ast = ast.parse(
                    'with seq:\n    WAIT(%s)' % str(unseen_chan),
                    mode='exec')
            pyqgl2.ast_util.copy_all_loc(empty_seq_ast, node)
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
"""

        test_code(code)

    def main():

        t1()

    main()

