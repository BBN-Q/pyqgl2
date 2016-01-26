# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

#from QGL.BasicSequences import AllXY as QGL1AllXY
from qgl2.qgl2 import qgl2decl, qbit

@qgl2decl
def AllXY(q: qbit, showPlot = False):
    #return QGL1AllXY(q, showPlot)
    raise Exception("Not implemented")
