# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import ast

from pyqgl2.debugmsg import DebugMsg


def getChanLabel(node):
    '''Given an Call to Qubit() or QubitFactory() or an Assign
    containing such, find the label of the qbit.
    Return None if can't find it.'''
    theNode = node
    if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
        theNode = node.value
    if not isinstance(theNode, ast.Call):
        DebugMsg.log("Was not a call")
        return None

    funcName = None
    if isinstance(theNode.func, ast.Name):
        funcName = theNode.func.id
    else:
        # Assume an Attribute
        temp2 = theNode.func.attr
        temp1 = theNode.func.value
        if isinstance(temp1, ast.Name):
            funcName = temp1.id + '.' + temp2
        else:
            funcName = temp2

    # First ensure there's a label.
    # If there are positional args, assume it is first
    # Otherwise, look for it among keyword args
    chanLabel = None
    if len(theNode.args) > 0:
        arg0 = theNode.args[0]
        # FIXME:
        # This code requires that the label arg be an explicit string
        # Not a variable, function call, etc.
        # We need this to (a) error check the arg value is a string, and
        # (b) extract the value for labeling in the QBIT map
        # This is a sad, ugly restriction
        if not isinstance(arg0, ast.Str):
            DebugMsg.log(
                    '1st param to %s() must be a string - got %s' %
                        (funcName, arg0))
            return None

        if not isinstance(arg0.s, str):
            DebugMsg.log(
                    '1st param to %s() must be a str - got %s' %
                        (funcName, arg0.s))
            return None

        chanLabel = arg0.s
    if len(theNode.keywords) > 0:
        for kwarg in theNode.keywords:
            if kwarg.arg == 'label':
                if chanLabel is not None:
                    kwp = str(kwarg.value)
                    if isinstance(kwarg.value, ast.Str):
                        kwp = kwarg.value.s
                    DebugMsg.log("%s had a positional arg used as label='%s'. Cannot also have keyword argument label='%s'" % (funcName, chanLabel, kwp))
                labelArg = kwarg.value
                if not isinstance(labelArg, ast.Str):
                    DebugMsg.log('label param to %s() must be a string - got %s' % (funcName, labelArg))
                    return None

                if not isinstance(labelArg.s, str):
                    DebugMsg.log('label param to %s() must be a str - got %s' % (funcName, labelArg.s))
                    return None
                chanLabel = labelArg.s
                break
        if chanLabel is None:
            DebugMsg.log("%s() missing required label (string) argument: found no label kwarg and had no positional args" % funcName)
            return None
    elif chanLabel is None:
        DebugMsg.log('%s() missing required label (string) argument: call had 0 parameters' % funcName)
        return None
    return chanLabel
