# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
Unroll for loops (and possibly other conditional/iterative statements)
within a "with concur" block.
"""

import ast

import pyqgl2.ast_util

from pyqgl2.ast_util import ast2str
from pyqgl2.debugmsg import DebugMsg
from pyqgl2.inline import QubitPlaceholder

import QGL.Channels


def find_all_channels(node, local_vars=None):
    """
    Wrapper for find_all_channels_worker, which checks that the result
    returned matches the value of node.qgl2_referenced_qbits,
    which is what we want to use in the future.

    Use of find_all_channels* is deprecated.
    """

    channels = find_all_channels_worker(node, local_vars=local_vars)

    # for debugging/testing only

    if hasattr(node, 'qgl2_referenced_qbits'):
        if channels != node.qgl2_referenced_qbits:
            DebugMsg.log(
                    "channels != node.qgl2_referenced_qbits",
                    level=DebugMsg.HIGH)
    else:
        DebugMsg.log(
                "node lacks a qgl2_referenced_qbits", level=DebugMsg.HIGH)

    return channels


def find_all_channels_worker(node, local_vars=None):
    """
    Reinitialze the set of all_channels to be the set of
    all channels referenced in the AST rooted at the given
    node.

    This is a hack, because we assume we can identify all
    channels lexically.  FIXME
    """

    print('SSSS')

    if not local_vars:
        print('NO LOCAL VARS')
        local_vars = dict()

    all_channels = set()

    for subnode in ast.walk(node):
        if isinstance(subnode, ast.Name):

            # Ugly hard-coded assumption about channel names: FIXME
            #
            # Also look for bindings to QubitPlaceholders
            #
            if subnode.id.startswith('QBIT_'):
                all_channels.add(subnode.id)
            elif subnode.id.startswith('EDGE_'):
                all_channels.add(subnode.id)
            elif subnode.id in local_vars:
                print('SYM IN LOCAL_VARS %s' % subnode.id)
                if isinstance(local_vars[subnode.id], QubitPlaceholder):
                    all_channels.add(local_vars[subnode.id].use_name)
                elif isinstance(local_vars[subnode.id], QGL.Channels.Qubit):
                    print('ITS A QUBIT %s' % local_vars[subnode.id])
                    all_channels.add(local_vars[subnode.id].use_name)

        # Look for references to inlined calls; dig out any
        # channels that might be hiding there despite being
        # optimized away later.
        #
        if hasattr(subnode, 'qgl2_orig_call'):
            orig_chan = find_all_channels_worker(
                    subnode.qgl2_orig_call, local_vars)
            # print('FAC %s -> %s' %
            #         (ast2str(subnode.qgl2_orig_call).strip(),
            #             str(orig_chan)))
            all_channels.update(orig_chan)

    return all_channels
