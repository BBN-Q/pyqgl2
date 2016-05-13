# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# This file reproduces the QGL1 imports to define BasicSequences.
# To test using the methods defined in this module, put this directory on the PYTHONPATH before the QGL1 versions.

# To implement the QGL2 versions using the QGL versions, do something like:
# from QGL.BasicSequences.Rabi import RabiAmp as QGL1RabiAmp
# and then in the method:
#     return QGL1RabiAmp(qubit, amps, phase, showPlot)

# These are the imports QGL used. Try leaving these out.

#from .Rabi import RabiAmp, RabiWidth, RabiAmpPi, RabiAmp_NQubits, PulsedSpec, SingleShot
#from .T1T2 import Ramsey, InversionRecovery
#from .FlipFlop import FlipFlop
#from .SPAM import SPAM
#from .RB import create_RB_seqs, SingleQubitRB, SingleQubitRB_AC, SingleQubitIRB_AC, SimultaneousRB_AC, SingleQubitRBT, TwoQubitRB
#from .Decoupling import HahnEcho, CPMG
#from .helpers import create_cal_seqs
#from .CR import EchoCRPhase, EchoCRLen, PiRabi
#from .AllXY import AllXY
#from .Feedback import Reset
#from .qgl2_plumbing import init

# These next are not in the original and not used in QGL
#from .Rabi import Swap
#from .BlankingSweeps import sweep_gateDelay
