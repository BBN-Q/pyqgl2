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

from qgl2.qgl2 import qgl2decl, qgl2main

try:
    from qgl2.basic_sequences import RabiAmp, RabiWidth, RabiAmpPi, RabiAmp_NQubits, PulsedSpec, SingleShot
    from qgl2.basic_sequences import Ramsey, InversionRecovery, FlipFlop, SPAM
    from qgl2.basic_sequences import create_RB_seqs, SingleQubitRB, SingleQubitRB_AC, SingleQubitIRB_AC, SimultaneousRB_AC, SingleQubitRBT, TwoQubitRB
    from qgl2.basic_sequences import HahnEcho, CPMG, create_cal_seqs, AllXY
    from qgl2.basic_sequences import Reset, EchoCRPhase, EchoCRLen, PiRabi
    # These next are never used
    # from qgl2.basic_sequences import Swap, sweep_gateDelay
    # I would do an import *, but this is more explicit to show what we're testing

    print("Re-defining basic sequences from qgl2.basic_sequences")
except Exception as e:
    import traceback
    sys.exit("Failed to redefine sequences from qgl2.basic_sequences: %s. %s" % (e, traceback.format_exc()))

# For testing as vanilla unit test, must comment out next line
@qgl2main
def main():

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
        # Try invoking the function
        # If that raises an AssertionError or NotImplementedError
        # then we know it isn't ready
        # But since we're calling with Nones, we expect certain Attribute Errors
        try:
            tests.test_Sequences.AllXY(None)
        except AttributeError as eN:
            if "'NoneType' object has no attribute" not in str(eN):
                raise
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
        import traceback
        print("Did not redefine AllXY: %s. %s" % (e, traceback.format_exc()))

    try:
        old = tests.test_Sequences.PiRabi
        tests.test_Sequences.PiRabi = PiRabi
        # Try invoking the function
        # If that raises an AssertionError or NotImplementedError
        # then we know it isn't ready
        # But since we're calling with Nones, we expect certain Attribute Errors
        try:
            tests.test_Sequences.PiRabi(None, None, [])
        except ValueError as e2:
            if "Edge (None, None) not found" not in str(e2):
                raise
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
        old = tests.test_Sequences.Reset
        tests.test_Sequences.Reset = Reset
        # Try invoking the function
        # If that raises an AssertionError or NotImplementedError
        # then we know it isn't ready
        # But since we're calling with Nones, we expect certain Attribute Errors
        try:
            tests.test_Sequences.Reset([])
        except ValueError as e2:
            if "Edge (None, None) not found" not in str(e2):
                raise
        print("Redefined Reset from QGL2")
        old = None
    except AssertionError as ae:
        # That function was never compiled - not redefining
        tests.test_Sequences.Reset = old
        print("Did not redefine Reset - found it but it isn't compiled yet")
    except NotImplementedError as ne:
        # have no qgl2 implementation yet, so use the qgl1 version
        if old:
            tests.test_Sequences.Reset = old
        print("Have no QGL2 implementation of Reset - use QGL1")
    except Exception as e:
        print("Did not redefine Reset: %s" % e)

    try:
        old = tests.test_Sequences.EchoCRLen
        tests.test_Sequences.EchoCRLen = EchoCRLen
        # Try invoking the function
        # If that raises an AssertionError or NotImplementedError
        # then we know it isn't ready
        # But since we're calling with Nones, we expect certain Attribute Errors
        try:
            tests.test_Sequences.EchoCRLen(None, None, [])
        except AttributeError as eN:
            if "'NoneType' object has no attribute" not in str(eN):
                raise
        except UnboundLocalError as e3:
            if "'channelName' referenced before " not in str(e3):
                raise
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
        import traceback
        print("Did not redefine EchoCRLen: %s: %s" % (e, traceback.format_exc()))

    try:
        old = tests.test_Sequences.EchoCRPhase
        tests.test_Sequences.EchoCRPhase = EchoCRPhase
        # Try invoking the function
        # If that raises an AssertionError or NotImplementedError
        # then we know it isn't ready
        # But since we're calling with Nones, we expect certain Attribute Errors
        try:
            tests.test_Sequences.EchoCRPhase(None, None, [])
        except UnboundLocalError as e3:
            if "'channelName' referenced before " not in str(e3):
                raise
        except AttributeError as eN:
            if "'NoneType' object has no attribute" not in str(eN):
                raise
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
        import traceback
        print("Did not redefine EchoCRPhase: %s: %s" % (e, traceback.format_exc()))

    try:
        old = tests.test_Sequences.HahnEcho
        tests.test_Sequences.HahnEcho = HahnEcho
        # Try invoking the function
        # If that raises an AssertionError or NotImplementedError
        # then we know it isn't ready
        # But since we're calling with Nones, we expect certain Attribute Errors
        try:
            tests.test_Sequences.HahnEcho(None, [])
        except AttributeError as eN:
            if "'NoneType' object has no attribute" not in str(eN):
                raise
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
        # Try invoking the function
        # If that raises an AssertionError or NotImplementedError
        # then we know it isn't ready
        # But since we're calling with Nones, we expect certain Attribute Errors
        try:
            tests.test_Sequences.CPMG(None, 0, 0)
        except AttributeError as eN:
            if "'NoneType' object has no attribute" not in str(eN):
                raise
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
        old = tests.test_Sequences.create_cal_seqs
        tests.test_Sequences.create_cal_seqs = create_cal_seqs
        # Try invoking the function
        # If that raises an AssertionError or NotImplementedError
        # then we know it isn't ready
        # But since we're calling with Nones, we expect certain Attribute Errors
        try:
            tests.test_Sequences.create_cal_seqs([], 0)
        except AttributeError as eN:
            if "'NoneType' object has no attribute" not in str(eN):
                raise
        print("Redefined create_cal_seqs from QGL2")
        old = None
    except AssertionError as ae:
        # That function was never compiled - not redefining
        tests.test_Sequences.create_cal_seqs = old
        print("Did not redefine create_cal_seqs - found it but it isn't compiled yet")
    except NotImplementedError as ne:
        # have no qgl2 implementation yet, so use the qgl1 version
        if old:
            tests.test_Sequences.create_cal_seqs = old
        print("Have no QGL2 implementation of create_cal_seqs - use QGL1")
    except Exception as e:
        print("Did not redefine create_cal_seqs: %s" % e)

    try:
        old = tests.test_Sequences.FlipFlop
        tests.test_Sequences.FlipFlop = FlipFlop
        # Try invoking the function
        # If that raises an AssertionError or NotImplementedError
        # then we know it isn't ready
        # But since we're calling with Nones, we expect certain Attribute Errors
        try:
            tests.test_Sequences.FlipFlop(None, [])
        except AttributeError as eN:
            if "'NoneType' object has no attribute" not in str(eN):
                raise
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
        # Try invoking the function
        # If that raises an AssertionError or NotImplementedError
        # then we know it isn't ready
        # But since we're calling with Nones, we expect certain Attribute Errors
        try:
            tests.test_Sequences.InversionRecovery(None, [])
        except AttributeError as eN:
            if "'NoneType' object has no attribute" not in str(eN):
                raise
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
        # Try invoking the function
        # If that raises an AssertionError or NotImplementedError
        # then we know it isn't ready
        # But since we're calling with Nones, we expect certain Attribute Errors
        try:
            tests.test_Sequences.Ramsey(None, [])
        except TypeError as e3:
            if "can't multiply sequence by non-int of type 'float'" not in str(e3):
                raise
        except AttributeError as eN:
            if "'NoneType' object has no attribute" not in str(eN):
                raise
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
        import traceback
        print("Did not redefine Ramsey: %s: %s" % (e, traceback.format_exc()))

    try:
        old = tests.test_Sequences.SPAM
        tests.test_Sequences.SPAM = SPAM
        # Try invoking the function
        # If that raises an AssertionError or NotImplementedError
        # then we know it isn't ready
        # But since we're calling with Nones, we expect certain Attribute Errors
        try:
            tests.test_Sequences.SPAM(None, [])
        except AttributeError as eN:
            if "'NoneType' object has no attribute" not in str(eN):
                raise
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
        # Try invoking the function
        # If that raises an AssertionError or NotImplementedError
        # then we know it isn't ready
        # But since we're calling with Nones, we expect certain Attribute Errors
        try:
            tests.test_Sequences.RabiAmp(None, [])
        except AttributeError as eN:
            if "'NoneType' object has no attribute" not in str(eN):
                raise
        except KeyError as ke:
            if "'slaveTrig'" not in str(ke):
                raise
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
        import traceback
        print("Did not redefine RabiAmp: %s: %s" % (e, traceback.format_exc()))

    try:
        old = tests.test_Sequences.RabiWidth
        tests.test_Sequences.RabiWidth = RabiWidth
        # Try invoking the function
        # If that raises an AssertionError or NotImplementedError
        # then we know it isn't ready
        # But since we're calling with Nones, we expect certain Attribute Errors
        try:
            tests.test_Sequences.RabiWidth(None, [])
        except KeyError as ke:
            if "'slaveTrig'" not in str(ke):
                raise
        except AttributeError as eN:
            if "'NoneType' object has no attribute" not in str(eN):
                raise
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
        # Try invoking the function
        # If that raises an AssertionError or NotImplementedError
        # then we know it isn't ready
        # But since we're calling with Nones, we expect certain Attribute Errors
        try:
            tests.test_Sequences.RabiAmp_NQubits([], [])
        except KeyError as ke:
            if "'slaveTrig'" not in str(ke):
                raise
        except AttributeError as eN:
            if "'NoneType' object has no attribute" not in str(eN):
                raise
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
        # Try invoking the function
        # If that raises an AssertionError or NotImplementedError
        # then we know it isn't ready
        # But since we're calling with Nones, we expect certain Attribute Errors
        try:
            tests.test_Sequences.RabiAmpPi(None, None, [])
        except KeyError as ke:
            if "'slaveTrig'" not in str(ke):
                raise
        except AttributeError as eN:
            if "'NoneType' object has no attribute" not in str(eN):
                raise
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
        # Try invoking the function
        # If that raises an AssertionError or NotImplementedError
        # then we know it isn't ready
        # But since we're calling with Nones, we expect certain Attribute Errors
        try:
            tests.test_Sequences.SingleShot(None)
        except AttributeError as eN:
            if "'NoneType' object has no attribute" not in str(eN):
                raise
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
        # Try invoking the function
        # If that raises an AssertionError or NotImplementedError
        # then we know it isn't ready
        # But since we're calling with Nones, we expect certain Attribute Errors
        try:
            tests.test_Sequences.PulsedSpec(None)
        except AttributeError as eN:
            if "'NoneType' object has no attribute" not in str(eN):
                raise
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
        # Try invoking the function
        # If that raises an AssertionError or NotImplementedError
        # then we know it isn't ready
        # But since we're calling with Nones, we expect certain Attribute Errors
        try:
            tests.test_Sequences.SingleQubitRB(None, [])
        except AttributeError as eN:
            if "'NoneType' object has no attribute" not in str(eN):
                raise
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
        old = tests.test_Sequences.SingleQubitRB_AC
        tests.test_Sequences.SingleQubitRB_AC = SingleQubitRB_AC
        # Try invoking the function
        # If that raises an AssertionError or NotImplementedError
        # then we know it isn't ready
        # But since we're calling with Nones, we expect certain Attribute Errors
        try:
            tests.test_Sequences.SingleQubitRB_AC(None, [])
        except AttributeError as eN:
            if "'NoneType' object has no attribute" not in str(eN):
                raise
        print("Redefined SingleQubitRB_AC from QGL2")
        old = None
    except AssertionError as ae:
        # That function was never compiled - not redefining
        tests.test_Sequences.SingleQubitRB_AC = old
        print("Did not redefine SingleQubitRB_AC - found it but it isn't compiled yet")
    except NotImplementedError as ne:
        # have no qgl2 implementation yet, so use the qgl1 version
        if old:
            tests.test_Sequences.SingleQubitRB_AC = old
        print("Have no QGL2 implementation of SingleQubitRB_AC - use QGL1")
    except Exception as e:
        print("Did not redefine SingleQubitRB_AC: %s" % e)

    try:
        old = tests.test_Sequences.SingleQubitIRB_AC
        tests.test_Sequences.SingleQubitIRB_AC = SingleQubitIRB_AC
        # Try invoking the function
        # If that raises an AssertionError or NotImplementedError
        # then we know it isn't ready
        # But since we're calling with Nones, we expect certain Attribute Errors
        try:
            tests.test_Sequences.SingleQubitIRB_AC(None, None)
        except AttributeError as eN:
            if "'NoneType' object has no attribute" not in str(eN):
                raise
        print("Redefined SingleQubitIRB_AC from QGL2")
        old = None
    except AssertionError as ae:
        # That function was never compiled - not redefining
        tests.test_Sequences.SingleQubitIRB_AC = old
        print("Did not redefine SingleQubitIRB_AC - found it but it isn't compiled yet")
    except NotImplementedError as ne:
        # have no qgl2 implementation yet, so use the qgl1 version
        if old:
            tests.test_Sequences.SingleQubitIRB_AC = old
        print("Have no QGL2 implementation of SingleQubitIRB_AC - use QGL1")
    except Exception as e:
        print("Did not redefine SingleQubitIRB_AC: %s" % e)

    try:
        old = tests.test_Sequences.SingleQubitRBT
        tests.test_Sequences.SingleQubitRBT = SingleQubitRBT
        # Try invoking the function
        # If that raises an AssertionError or NotImplementedError
        # then we know it isn't ready
        # But since we're calling with Nones, we expect certain Attribute Errors
        try:
            tests.test_Sequences.SingleQubitRBT(None, None, None)
        except AttributeError as eN:
            if "'NoneType' object has no attribute" not in str(eN):
                raise
        print("Redefined SingleQubitRBT from QGL2")
        old = None
    except AssertionError as ae:
        # That function was never compiled - not redefining
        tests.test_Sequences.SingleQubitRBT = old
        print("Did not redefine SingleQubitRBT - found it but it isn't compiled yet")
    except NotImplementedError as ne:
        # have no qgl2 implementation yet, so use the qgl1 version
        if old:
            tests.test_Sequences.SingleQubitRBT = old
        print("Have no QGL2 implementation of SingleQubitRBT - use QGL1")
    except Exception as e:
        print("Did not redefine SingleQubitRBT: %s" % e)

    try:
        old = tests.test_Sequences.create_RB_seqs
        tests.test_Sequences.create_RB_seqs = create_RB_seqs
        # Try invoking the function
        # If that raises an AssertionError or NotImplementedError
        # then we know it isn't ready
        # But since we're calling with Nones, we expect certain Attribute Errors
        try:
            tests.test_Sequences.create_RB_seqs(1, [])
        except AttributeError as eN:
            if "'NoneType' object has no attribute" not in str(eN):
                raise
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
        # Try invoking the function
        # If that raises an AssertionError or NotImplementedError
        # then we know it isn't ready
        # But since we're calling with Nones, we expect certain Attribute Errors
        try:
            tests.test_Sequences.TwoQubitRB(None, None, [])
        except AttributeError as eN:
            if "'NoneType' object has no attribute" not in str(eN):
                raise
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
        # Try invoking the function
        # If that raises an AssertionError or NotImplementedError
        # then we know it isn't ready
        # But since we're calling with Nones, we expect certain Attribute Errors
        try:
            tests.test_Sequences.SimultaneousRB_AC([], [])
        except TypeError as e3:
            if "reduce() of empty sequence with no initial value" not in str(e3):
                raise
        except AttributeError as eN:
            if "'NoneType' object has no attribute" not in str(eN):
                raise
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
        import traceback
        print("Did not redefine SimultaneousRB_AC: %s: %s" % (e, traceback.format_exc()))

    # Having re-defined the basic methods, run the basic QGL1 sequence unit tests
    unittest.main(module=tests.test_Sequences, argv=[sys.argv[0]])

if __name__ == "__main__":
    main()

