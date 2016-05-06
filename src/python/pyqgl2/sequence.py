# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import ast
import os
import sys

from copy import deepcopy

from pyqgl2.ast_util import ast2str, NodeError
from pyqgl2.concur_unroll import is_concur, is_seq, find_all_channels
from pyqgl2.importer import collapse_name
from pyqgl2.lang import QGL2

# Dead code
# Produces per channel strings/sequences
# Only use is in an 'if False' in main.py

class SequenceCreator(ast.NodeVisitor):
    """
    Create a list of sequence lists for a given AST

    Note: this assumes that the AST is for one function
    definition that has already been inlined and successfully
    flattened and grouped already (which assumes that all the
    previous steps prior to flattening/grouping have been
    successful).  This does not work, and will probably crash,
    if given general AST.
    """

    def __init__(self):

        self.qbit2sequence = dict()

    def visit_With(self, node):
        """
        If the node is a "with concur", then add a sequence
        for each "with seq" block in its body, with a WAIT
        preamble and SYNC(?) postamble.

        All other kinds of "with" blocks cause an error.
        """

        if is_concur(node):
            self.do_concur(node.body)

            # TODO: if there's an orelse, or anything like
            # that, then gripe here.  We can't handle that yet.

        else:
            # TODO: this error message is not helpful
            NodeError.fatal_msg(node, 'Unexpected with block')

    def do_concur(self, body):

        for stmnt in body:
            if not is_seq(stmnt):
                # TODO: this error message is not helpful
                NodeError.fatal_msg(stmnt, 'expected a "with seq" block')
                return
            else:
                # TODO: The grouper should annotate the seq statement
                # so we don't have to find the qbits again.
                #
                qbits = find_all_channels(stmnt)
                if not qbits:
                    print('XXN body\n%s' % ast2str(stmnt))
                self.do_seq(qbits, stmnt.body)

    def do_seq(self, qbits, body):
        chan_name = '/'.join(qbits)

        if chan_name not in self.qbit2sequence:
            self.qbit2sequence[chan_name] = list()

        for stmnt in body:
            txt = ast2str(stmnt).strip()

            self.qbit2sequence[chan_name].append(txt)

