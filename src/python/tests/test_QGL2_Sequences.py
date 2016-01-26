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
        old = tests.test_Sequences.AllXY
        tests.test_Sequences.AllXY = AllXY
        tests.test_Sequences.AllXY(None)
        print("Redefined AllXY from QGL2")
        old = None
    except AssertionError as ae:
        # That function was never compiled - not redefining
        tests.test_Sequences.AllXY = old
        print("Did not redefine AllXY - found it but it isn't compiled yet")
    except NotImplementedError as ne:
        # have no qgl2 implementation yet, so use the qgl1 version
        if old:
            tests.test_Sequences.AllXY = old
        print("Have no QGL2 implementation of AllXY - use QGL1")
    except Exception as e:
        print("Did not redefine AllXY: %s" % e)

    try:
        old = tests.test_Sequences.PiRabi
        tests.test_Sequences.PiRabi = PiRabi
        tests.test_Sequences.PiRabi(None, None, None)
        print("Redefined PiRabi from QGL2")
        old = None
    except AssertionError as ae:
        # That function was never compiled - not redefining
        tests.test_Sequences.PiRabi = old
        print("Did not redefine PiRabi - found it but it isn't compiled yet")
    except NotImplementedError as ne:
        # have no qgl2 implementation yet, so use the qgl1 version
        if old:
            tests.test_Sequences.PiRabi = old
        print("Have no QGL2 implementation of PiRabi - use QGL1")
    except Exception as e:
        print("Did not redefine PiRabi: %s" % e)

    try:
        old = tests.test_Sequences.EchoCRLen
        tests.test_Sequences.EchoCRLen = EchoCRLen
        tests.test_Sequences.EchoCRLen(None, None, None)
        print("Redefined EchoCRLen from QGL2")
        old = None
    except AssertionError as ae:
        # That function was never compiled - not redefining
        tests.test_Sequences.EchoCRLen = old
        print("Did not redefine EchoCRLen - found it but it isn't compiled yet")
    except NotImplementedError as ne:
        # have no qgl2 implementation yet, so use the qgl1 version
        if old:
            tests.test_Sequences.EchoCRLen = old
        print("Have no QGL2 implementation of EchoCRLen - use QGL1")
    except Exception as e:
        print("Did not redefine EchoCRLen: %s" % e)

    try:
        old = tests.test_Sequences.EchoCRPhase
        tests.test_Sequences.EchoCRPhase = EchoCRPhase
        tests.test_Sequences.EchoCRPhase(None, None, None)
        print("Redefined EchoCRPhase from QGL2")
        old = None
    except AssertionError as ae:
        # That function was never compiled - not redefining
        tests.test_Sequences.EchoCRPhase = old
        print("Did not redefine EchoCRPhase - found it but it isn't compiled yet")
    except NotImplementedError as ne:
        # have no qgl2 implementation yet, so use the qgl1 version
        if old:
            tests.test_Sequences.EchoCRPhase = old
        print("Have no QGL2 implementation of EchoCRPhase - use QGL1")
    except Exception as e:
        print("Did not redefine EchoCRPhase: %s" % e)

    try:
        old = tests.test_Sequences.HahnEcho
        tests.test_Sequences.HahnEcho = HahnEcho
        tests.test_Sequences.HahnEcho(None, None)
        print("Redefined HahnEcho from QGL2")
        old = None
    except AssertionError as ae:
        # That function was never compiled - not redefining
        tests.test_Sequences.HahnEcho = old
        print("Did not redefine HahnEcho - found it but it isn't compiled yet")
    except NotImplementedError as ne:
        # have no qgl2 implementation yet, so use the qgl1 version
        if old:
            tests.test_Sequences.HahnEcho = old
        print("Have no QGL2 implementation of HahnEcho - use QGL1")
    except Exception as e:
        print("Did not redefine HahnEcho: %s" % e)

    try:
        old = tests.test_Sequences.CPMG
        tests.test_Sequences.CPMG = CPMG
        tests.test_Sequences.CPMG(None, None, None)
        print("Redefined CPMG from QGL2")
        old = None
    except AssertionError as ae:
        # That function was never compiled - not redefining
        tests.test_Sequences.CPMG = old
        print("Did not redefine CPMG - found it but it isn't compiled yet")
    except NotImplementedError as ne:
        # have no qgl2 implementation yet, so use the qgl1 version
        if old:
            tests.test_Sequences.CPMG = old
        print("Have no QGL2 implementation of CPMG - use QGL1")
    except Exception as e:
        print("Did not redefine CPMG: %s" % e)

    try:
        old = tests.test_Sequences.FlipFlop
        tests.test_Sequences.FlipFlop = FlipFlop
        tests.test_Sequences.FlipFlop(None, None)
        print("Redefined FlipFlop from QGL2")
        old = None
    except AssertionError as ae:
        # That function was never compiled - not redefining
        tests.test_Sequences.FlipFlop = old
        print("Did not redefine FlipFlop - found it but it isn't compiled yet")
    except NotImplementedError as ne:
        # have no qgl2 implementation yet, so use the qgl1 version
        if old:
            tests.test_Sequences.FlipFlop = old
        print("Have no QGL2 implementation of FlipFlop - use QGL1")
    except Exception as e:
        print("Did not redefine FlipFlop: %s" % e)

    try:
        old = tests.test_Sequences.InversionRecovery
        tests.test_Sequences.InversionRecovery = InversionRecovery
        tests.test_Sequences.InversionRecovery(None, None)
        print("Redefined InversionRecovery from QGL2")
        old = None
    except AssertionError as ae:
        # That function was never compiled - not redefining
        tests.test_Sequences.InversionRecovery = old
        print("Did not redefine InversionRecovery - found it but it isn't compiled yet")
    except NotImplementedError as ne:
        # have no qgl2 implementation yet, so use the qgl1 version
        if old:
            tests.test_Sequences.InversionRecovery = old
        print("Have no QGL2 implementation of InversionRecovery - use QGL1")
    except Exception as e:
        print("Did not redefine InversionRecovery: %s" % e)

    try:
        old = tests.test_Sequences.Ramsey
        tests.test_Sequences.Ramsey = Ramsey
        tests.test_Sequences.Ramsey(None, None)
        print("Redefined Ramsey from QGL2")
        old = None
    except AssertionError as ae:
        # That function was never compiled - not redefining
        tests.test_Sequences.Ramsey = old
        print("Did not redefine Ramsey - found it but it isn't compiled yet")
    except NotImplementedError as ne:
        # have no qgl2 implementation yet, so use the qgl1 version
        if old:
            tests.test_Sequences.Ramsey = old
        print("Have no QGL2 implementation of Ramsey - use QGL1")
    except Exception as e:
        print("Did not redefine Ramsey: %s" % e)

    try:
        old = tests.test_Sequences.SPAM
        tests.test_Sequences.SPAM = SPAM
        tests.test_Sequences.SPAM(None, None)
        print("Redefined SPAM from QGL2")
        old = None
    except AssertionError as ae:
        # That function was never compiled - not redefining
        tests.test_Sequences.SPAM = old
        print("Did not redefine SPAM - found it but it isn't compiled yet")
    except NotImplementedError as ne:
        # have no qgl2 implementation yet, so use the qgl1 version
        if old:
            tests.test_Sequences.SPAM = old
        print("Have no QGL2 implementation of SPAM - use QGL1")
    except Exception as e:
        print("Did not redefine SPAM: %s" % e)

    try:
        old = tests.test_Sequences.RabiAmp
        tests.test_Sequences.RabiAmp = RabiAmp
        tests.test_Sequences.RabiAmp(None, None)
        print("Redefined RabiAmp from QGL2")
        old = None
    except AssertionError as ae:
        # That function was never compiled - not redefining
        tests.test_Sequences.RabiAmp = old
        print("Did not redefine RabiAmp - found it but it isn't compiled yet")
    except NotImplementedError as ne:
        # have no qgl2 implementation yet, so use the qgl1 version
        if old:
            tests.test_Sequences.RabiAmp = old
        print("Have no QGL2 implementation of RabiAmp - use QGL1")
    except Exception as e:
        print("Did not redefine RabiAmp: %s" % e)

    try:
        old = tests.test_Sequences.RabiWidth
        tests.test_Sequences.RabiWidth = RabiWidth
        tests.test_Sequences.RabiWidth(None, None)
        print("Redefined RabiWidth from QGL2")
        old = None
    except AssertionError as ae:
        # That function was never compiled - not redefining
        tests.test_Sequences.RabiWidth = old
        print("Did not redefine RabiWidth - found it but it isn't compiled yet")
    except NotImplementedError as ne:
        # have no qgl2 implementation yet, so use the qgl1 version
        if old:
            tests.test_Sequences.RabiWidth = old
        print("Have no QGL2 implementation of RabiWidth - use QGL1")
    except Exception as e:
        print("Did not redefine RabiWidth: %s" % e)

    try:
        old = tests.test_Sequences.RabiAmp_NQubits
        tests.test_Sequences.RabiAmp_NQubits = RabiAmp_NQubits
        tests.test_Sequences.RabiAmp_NQubits(None, None)
        print("Redefined RabiAmp_NQubits from QGL2")
        old = None
    except AssertionError as ae:
        # That function was never compiled - not redefining
        tests.test_Sequences.RabiAmp_NQubits = old
        print("Did not redefine RabiAmp_NQubits - found it but it isn't compiled yet")
    except NotImplementedError as ne:
        # have no qgl2 implementation yet, so use the qgl1 version
        if old:
            tests.test_Sequences.RabiAmp_NQubits = old
        print("Have no QGL2 implementation of RabiAmp_NQubits - use QGL1")
    except Exception as e:
        print("Did not redefine RabiAmp_NQubits: %s" % e)

    try:
        old = tests.test_Sequences.RabiAmpPi
        tests.test_Sequences.RabiAmpPi = RabiAmpPi
        tests.test_Sequences.RabiAmpPi(None, None, None)
        print("Redefined RabiAmpPi from QGL2")
        old = None
    except AssertionError as ae:
        # That function was never compiled - not redefining
        tests.test_Sequences.RabiAmpPi = old
        print("Did not redefine RabiAmpPi - found it but it isn't compiled yet")
    except NotImplementedError as ne:
        # have no qgl2 implementation yet, so use the qgl1 version
        if old:
            tests.test_Sequences.RabiAmpPi = old
        print("Have no QGL2 implementation of RabiAmpPi - use QGL1")
    except Exception as e:
        print("Did not redefine RabiAmpPi: %s" % e)

    try:
        old = tests.test_Sequences.SingleShot
        tests.test_Sequences.SingleShot = SingleShot
        tests.test_Sequences.SingleShot(None)
        print("Redefined SingleShot from QGL2")
        old = None
    except AssertionError as ae:
        # That function was never compiled - not redefining
        tests.test_Sequences.SingleShot = old
        print("Did not redefine SingleShot - found it but it isn't compiled yet")
    except NotImplementedError as ne:
        # have no qgl2 implementation yet, so use the qgl1 version
        if old:
            tests.test_Sequences.SingleShot = old
        print("Have no QGL2 implementation of SingleShot - use QGL1")
    except Exception as e:
        print("Did not redefine SingleShot: %s" % e)

    try:
        old = tests.test_Sequences.PulsedSpec
        tests.test_Sequences.PulsedSpec = PulsedSpec
        tests.test_Sequences.PulsedSpec(None)
        print("Redefined PulsedSpec from QGL2")
        old = None
    except AssertionError as ae:
        # That function was never compiled - not redefining
        tests.test_Sequences.PulsedSpec = old
        print("Did not redefine PulsedSpec - found it but it isn't compiled yet")
    except NotImplementedError as ne:
        # have no qgl2 implementation yet, so use the qgl1 version
        if old:
            tests.test_Sequences.PulsedSpec = old
        print("Have no QGL2 implementation of PulsedSpec - use QGL1")
    except Exception as e:
        print("Did not redefine PulsedSpec: %s" % e)

    try:
        old = tests.test_Sequences.SingleQubitRB
        tests.test_Sequences.SingleQubitRB = SingleQubitRB
        tests.test_Sequences.SingleQubitRB(None, None)
        print("Redefined SingleQubitRB from QGL2")
        old = None
    except AssertionError as ae:
        # That function was never compiled - not redefining
        tests.test_Sequences.SingleQubitRB = old
        print("Did not redefine SingleQubitRB - found it but it isn't compiled yet")
    except NotImplementedError as ne:
        # have no qgl2 implementation yet, so use the qgl1 version
        if old:
            tests.test_Sequences.SingleQubitRB = old
        print("Have no QGL2 implementation of SingleQubitRB - use QGL1")
    except Exception as e:
        print("Did not redefine SingleQubitRB: %s" % e)

    try:
        old = tests.test_Sequences.create_RB_seqs
        tests.test_Sequences.create_RB_seqs = create_RB_seqs
        tests.test_Sequences.create_RB_seqs(None, None)
        print("Redefined create_RB_seqs from QGL2")
        old = None
    except AssertionError as ae:
        # That function was never compiled - not redefining
        tests.test_Sequences.create_RB_seqs = old
        print("Did not redefine create_RB_seqs - found it but it isn't compiled yet")
    except NotImplementedError as ne:
        # have no qgl2 implementation yet, so use the qgl1 version
        if old:
            tests.test_Sequences.create_RB_seqs = old
        print("Have no QGL2 implementation of create_RB_seqs - use QGL1")
    except Exception as e:
        print("Did not redefine create_RB_seqs: %s" % e)

    try:
        old = tests.test_Sequences.TwoQubitRB
        tests.test_Sequences.TwoQubitRB = TwoQubitRB
        tests.test_Sequences.TwoQubitRB(None, None, None)
        print("Redefined TwoQubitRB from QGL2")
        old = None
    except AssertionError as ae:
        # That function was never compiled - not redefining
        tests.test_Sequences.TwoQubitRB = old
        print("Did not redefine TwoQubitRB - found it but it isn't compiled yet")
    except NotImplementedError as ne:
        # have no qgl2 implementation yet, so use the qgl1 version
        if old:
            tests.test_Sequences.TwoQubitRB = old
        print("Have no QGL2 implementation of TwoQubitRB - use QGL1")
    except Exception as e:
        print("Did not redefine TwoQubitRB: %s" % e)

    try:
        old = tests.test_Sequences.SimultaneousRB_AC
        tests.test_Sequences.SimultaneousRB_AC = SimultaneousRB_AC
        tests.test_Sequences.SimultaneousRB_AC(None, None)
        print("Redefined SimultaneousRB_AC from QGL2")
        old = None
    except AssertionError as ae:
        # That function was never compiled - not redefining
        tests.test_Sequences.SimultaneousRB_AC = old
        print("Did not redefine SimultaneousRB_AC - found it but it isn't compiled yet")
    except NotImplementedError as ne:
        # have no qgl2 implementation yet, so use the qgl1 version
        if old:
            tests.test_Sequences.SimultaneousRB_AC = old
        print("Have no QGL2 implementation of SimultaneousRB_AC - use QGL1")
    except Exception as e:
        print("Did not redefine SimultaneousRB_AC: %s" % e)

    # Having re-defined the basic methods, run the basic QGL1 sequence unit tests
    unittest.main(module=tests.test_Sequences, argv=[sys.argv[0]])
