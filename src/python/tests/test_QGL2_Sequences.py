# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.
'''
Variant of test_Sequences.py that uses the QGL2 compiled versions of the basic sequences, instead of the 
built-in versions.

Requires python3 anaconda, cppy, atom 1.0.0, latest QGL repo, and the latest
JSONLibraryUtils repo cloned as a sub-dir to QGL (if use the
--recurse-submodules arg when cloning QGL, you get it for free).
E.G.
pip install cppy; pip install
git+https://github.com/nucleic/atom.git@1.0.0-dev
git clone <QGL>
cd QGL
git submodule update, or git clone <JSONLibraryUtils>

You MUST write the QGL2 versions of your classes into a QGL2 module on the pythonpath, such that

   from qgl2.basic_sequences import *

re-defines all the QGL1 functions that you are trying to replace.

You will need both QGL1 and QGL2 on your pythonpath. Put QGL2 first.

The functions to replace are those that are used in test_Sequences, which are not primitives. Mostly this is therefore
the functions in BasicSequences.

These are the functions that I think we do want to redefine

funcs = ["AllXY", "PiRabi", "EchoCRLen", "EchoCRPhase", "HahnEcho", "CPMG", "FlipFlop", "InversionRecovery", "Ramsey", "SPAM", "RabiAmp", "RabiWidth", "RabiAmp_NQubits", "RabiAmpPi", "SingleShot", "PulsedSpec", "SingleQubitRB", "create_RB_seqs", "TwoQubitRB", "SimultaneousRB_AC"]
'''

import tests.test_Sequences

import sys
import unittest

# NOTE: Assuming anything defined in PulsePrimitives we do not need to redo / separately test
# Note that CNOT_CR is potentially multiple pulses so might want to do that one in QGL2

#import QGL2AC as AC
#import QGL2ZX90_CR as ZX90_CR
#import QGL2CNOT_CR as CNOT_CR


#from qgl2.qgl2 import *
from qgl2.qgl2 import concur, qgl2decl, qgl2main
from qgl2.qgl2 import classical, pulse, qbit, qbit_list
from qgl2.qgl2 import Qbit

if __name__ == "__main__":
    try:
        from qgl2.basic_sequences import *
        print("Re-defined basic sequences from qgl2.basic_sequences")
    except Exception as e:
        import traceback
        sys.exit("Failed to redefine sequences from qgl2.basic_sequences: %s. %s" % (e, traceback.format_exc()))

    # Now must redefine all the methods here.
    # I'd like to do something like this:
#    import QGL2
#    for symbol in dir(QGL2):
#        if symbol[0] == "_" or "QGL1" == symbol[:4]:
#            continue
#        tests.test_Sequences.symbol = symbol

    # But that doesn't quite work. So instead, this uglier version

    try:
        tests.test_Sequences.AllXY = AllXY
        print("Redefined AllXY from QGL2")
    except:
        print("Did not redefine AllXY")

    try:
        tests.test_Sequences.PiRabi = PiRabi
        print("Redefined PiRabi from QGL2")
    except:
        print("Did not redefine PiRabi")

    try:
        tests.test_Sequences.EchoCRLen = EchoCRLen
        print("Redefined EchoCRLen from QGL2")
    except:
        print("Did not redefine EchoCRLen")

    try:
        tests.test_Sequences.EchoCRPhase = EchoCRPhase
        print("Redefined EchoCRPhase from QGL2")
    except:
        print("Did not redefine EchoCRPhase")

    try:
        tests.test_Sequences.HahnEcho = HahnEcho
        print("Redefined HahnEcho from QGL2")
    except:
        print("Did not redefine HahnEcho")

    try:
        tests.test_Sequences.CPMG = CPMG
        print("Redefined CPMG from QGL2")
    except:
        print("Did not redefine CPMG")

    try:
        tests.test_Sequences.FlipFlop = FlipFlop
        print("Redefined FlipFlop from QGL2")
    except:
        print("Did not redefine FlipFlop")

    try:
        tests.test_Sequences.InversionRecovery = InversionRecovery
        print("Redefined InversionRecovery from QGL2")
    except:
        print("Did not redefine InversionRecovery")

    try:
        tests.test_Sequences.Ramsey = Ramsey
        print("Redefined Ramsey from QGL2")
    except:
        print("Did not redefine Ramsey")

    try:
        tests.test_Sequences.SPAM = SPAM
        print("Redefined SPAM from QGL2")
    except:
        print("Did not redefine SPAM")

    try:
        tests.test_Sequences.RabiAmp = RabiAmp
        print("Redefined RabiAmp from QGL2")
    except:
        print("Did not redefine RabiAmp")

    try:
        tests.test_Sequences.RabiWidth = RabiWidth
        print("Redefined RabiWidth from QGL2")
    except:
        print("Did not redefine RabiWidth")

    try:
        tests.test_Sequences.RabiAmp_NQubits = RabiAmp_NQubits
        print("Redefined RabiAmp_NQubits from QGL2")
    except:
        print("Did not redefine RabiAmp_NQubits")

    try:
        tests.test_Sequences.RabiAmpPi = RabiAmpPi
        print("Redefined RabiAmpPi from QGL2")
    except:
        print("Did not redefine RabiAmpPi")

    try:
        tests.test_Sequences.SingleShot = SingleShot
        print("Redefined SingleShot from QGL2")
    except:
        print("Did not redefine SingleShot")

    try:
        tests.test_Sequences.PulsedSpec = PulsedSpec
        print("Redefined PulsedSpec from QGL2")
    except:
        print("Did not redefine PulsedSpec")

    try:
        tests.test_Sequences.SingleQubitRB = SingleQubitRB
        print("Redefined SingleQubitRB from QGL2")
    except:
        print("Did not redefine SingleQubitRB")

    try:
        tests.test_Sequences.create_RB_seqs = create_RB_seqs
        print("Redefined create_RB_seqs from QGL2")
    except:
        print("Did not redefine create_RB_seqs")

    try:
        tests.test_Sequences.TwoQubitRB = TwoQubitRB
        print("Redefined TwoQubitRB from QGL2")
    except:
        print("Did not redefine TwoQubitRB")

    try:
        tests.test_Sequences.SimultaneousRB_AC = SimultaneousRB_AC
        print("Redefined SimultaneousRB_AC from QGL2")
    except:
        print("Did not redefine SimultaneousRB_AC")

    # Having re-defined the basic methods, run the basic QGL1 sequence unit tests
    unittest.main(module=tests.test_Sequences, argv=[sys.argv[0]])
