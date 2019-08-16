# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qgl2main, concur, qreg, pulse
from qgl2.qgl1 import Id, MEAS, X
from qgl2.util import init

from qgl2.basic_sequences.helpers import create_cal_seqs

from itertools import product

# FIXME 8/2019: This isn't working yet.
# Reset and BitFlip3 are good examples of trying to use TDM functions
# or measurement values which QGL2 can't quite do yet.

# The following qreset definitions represent a progression in complexity
# This first one is the simplest (the "goal")

# TODO we don't want this method to be inlined by the compiler
# how do we tell QGL2 not to inline it?
@qgl2decl
def qreset(q: qreg):
    m = MEAS(q)
    if m == 1:
        X(q)

# In this next one, we assume that the hardware might disagree on which
# measurement result indicates qubit state = |0>, so we allow an optional
# sign flip. One way to write this seems to imply TDM computation.

@qgl2decl
def qreset_with_sign_inversion(q: qreg, measSign):
    m = MEAS(q)
    if m == measSign:
        X(q)

# In actuallity, the current definition of "MEAS" does not include a
# necessary element to make this work on real hardware. Namely, we need to
# deal with separate clock domains in the measurement and control systems, so
# we add a delay before checking for the existence of a value to make message
# passing delay deterministic.

@qgl2decl
def qreset_with_delay(q: qreg, delay):
    m = MEAS(q)
    # Wait to make branching time deterministic, and to allow residual
    # measurement photons to decay
    Id(q, delay)
    if m == 1:
        X(q)

# Finally, for short consitional sequences like this, we want each branch
# to consume the same amount of time, therefore the "else" branch should be
# populated with an Id. Putting these things all together we have:

@qgl2decl
def qreset_full(q:qreg, delay, measSign):
    m = MEAS(q)
    Id(q, delay)
    if m == measSign:
        X(q)
    else:
        Id(q)

def Reset(qubits: qreg, measDelay = 1e-6, signVec = None,
          doubleRound = True, buf = 20e-9, measChans = None, docals = True,
          calRepeats=2, reg_size=None, TDM_map=None):
    """
    Preparation, simultanoeus reset, and measurement of an arbitrary number of qubits

    Parameters
    ----------
    qubits : tuple of logical channels to implement sequence (LogicalChannel)
    measDelay : delay between end of measuerement and reset pulse / LOADCMP
    signVec : Measurement results that indicate that we should flip Tuple of 0 (flip if signal > threshold or 1 for each qubit. (default == 0 for all qubits)
    doubleRound : if true, double round of feedback
    docals : enable calibration sequences
    calRepeats: number of times to repeat calibration
    reg_size: total number of qubits, including those that are not reset. Default set to len(qubits)
    TDM_map: map each qubit to a TDM digital input. Default: np.array(qN, qN-1, ..., q1) from MSB to LSB.
    """

    if measChans is None:
        measChans = qubits
    if signVec is None:
        signVec = (0,)*len(qubits)

    # FIXME: create_cal_seqs does pulses, doesn't return them
    # So what is old code expecting is returned here, that I can use instead?
    # given numRepeats=1, this is a single [] containing 2*#qubits of the reduce() thing
    # The reduce thing is a bunch of pulses with * between them
    # So here I create the combinations of pulses we want for each prep thing and loop over those combos
    for prep in product([Id,X], repeat=len(qubits)):
        init(qubits)
        prep # FIXME: See below where it did another loop? Look at git history?
        # FIXME: Could I start by making qreset a qgl1 stub?
        # Seems like the old qgl2 pushed into this method some of what new qgl1 qreset does itself
        # so a git diff is key
        qreset(qubits, signVec, measDelay, buf, reg_size=reg_size, TDM_map=TDM_map)
        measConcurrently(qubits)
        if doubleRound:
            qreset(qubits, signVec, measDelay, buf, reg_size=reg_size, TDM_map=TDM_map)
        # Add final measurement
        measConcurrently(qubits)
        Id(qubits[0], length=measDelay)
        qwait(kind='CMP')
    # If we're doing calibration too, add that at the very end
    # - another 2^numQubits * calRepeats sequences
    if docals:
        create_cal_seqs(qubits, calRepeats, measChans=measChans, waitcmp=True)
#    metafile = compile_to_hardware(seqs, 'Reset/Reset')

# old version
    for prep in product([Id,X], repeat=len(qubits)):
        for p,q,measSign in zip(prep, qubits, signVec):
            init(q)
            # prepare the initial state
            p(q)
            qreset_full(q, measDelay, measSign)
            if doubleRound:
                qreset_full(q, measDelay, measSign)
            MEAS(qubits)

    # If we're doing calibration too, add that at the very end
    # - another 2^numQubits * calRepeats sequences
    if docals:
        create_cal_seqs(qubits, calRepeats)

# do not make it a subroutine for now
def BitFlip3(data_qs: qreg, ancilla_qs: qreg, theta=None, phi=None, nrounds=1, meas_delay=1e-6, docals=False, calRepeats=2):
    """

    Encoding on 3-qubit bit-flip code, followed by n rounds of syndrome detection, and final correction using the n results.

    Parameters
    ----------
    data_qs : tuple of logical channels for the 3 code qubits
    ancilla_qs: tuple of logical channels for the 2 syndrome qubits
    theta, phi: longitudinal and azimuthal rotation angles for encoded state (default = no encoding)
    meas_delay : delay between syndrome check rounds
    docals, calRepeats: enable calibration sequences, repeated calRepeats times

    Returns
    -------
    metafile : metafile path
    """
    if len(data_qs) != 3 or len(ancilla_qs) != 2:
        raise Exception("Wrong number of qubits")

    # Call some TDM Instructions
    DecodeSetRounds(1,0,nrounds)
    Invalidate(10, 2*nrounds)
    Invalidate(11, 0x1)

    # encode single-qubit state into 3 qubits
    if theta and phi:
        Utheta(data_qs[1], angle=theta, phase=phi)
        CNOT(data_qs[1], data_qs[0])
        CNOT(data_qs[1], data_qs[2])

    # multiple rounds of syndrome measurements
    for n in range(nrounds):
        Barrier(data_qs[0], ancilla_qs[0], data_qs[1], ancilla_qs[1])
        CNOT(data_qs[0],ancilla_qs[0])
        CNOT(data_qs[1],ancilla_qs[1])
        Barrier(data_qs[1], ancilla_qs[0], data_qs[2], ancilla_qs[1])
        CNOT(data_qs[1], ancilla_qs[0])
        CNOT(data_qs[2],ancilla_qs[1])
        Barrier(ancilla_qs[0], ancilla_qs[1])
        MEASA(ancilla_qs[0], maddr=(10, 2*n))
        MEASA(ancilla_qs[1], maddr=(10, 2*n+1))
        Id(ancilla_qs[0], meas_delay)
        # virtual msmt's just to keep the number of segments uniform across digitizer channels
        Barrier(data_qs)
        MEAS(data_qs[0], amp=0)
        MEAS(data_qs[1], amp=0)
        MEAS(data_qs[2], amp=0)
    Decode(10, 11, 2*nrounds)
    qwait("RAM",11)
    Barrier(data_qs, ancilla_qs)
    # virtual msmt's
    MEAS(data_qs[0])
    MEAS(data_qs[1])
    MEAS(data_qs[2])
    MEAS(ancilla_qs[0], amp=0)
    MEAS(ancilla_qs[1], amp=0)

    # FIXME: What's right way to do this bit
    # apply corrective pulses depending on the decoder result
    FbGates = []
    for q in data_qs:
        FbGates.append([gate(q) for gate in [Id, X]])
    FbSeq = [reduce(operator.mul, x) for x in product(*FbGates)]
    for k in range(8):
        qif(k, [FbSeq[k]])

    if docals:
        create_cal_seqs(qubits, calRepeats)
#    metafile = compile_to_hardware(seqs, 'BitFlip/BitFlip', tdm_seq=True)

# A main for running the sequences here with some typical argument values
# Here it runs all of them; could do a parse_args like main.py
def main():
    from pyqgl2.qreg import QRegister
    import pyqgl2.test_cl
    from pyqgl2.main import compile_function, qgl2_compile_to_hardware
    import numpy as np

    toHW = True
    plotPulses = False
    pyqgl2.test_cl.create_default_channelLibrary(toHW, True)

#    # To turn on verbose logging in compile_function
#    from pyqgl2.ast_util import NodeError
#    from pyqgl2.debugmsg import DebugMsg
#    NodeError.MUTE_ERR_LEVEL = NodeError.NODE_ERROR_NONE
#    DebugMsg.set_level(0)

    # Now compile the QGL2 to produce the function that would generate the expected sequence.
    # Supply the path to the QGL2, the main function in that file, and a list of the args to that function.
    # Can optionally supply saveOutput=True to save the qgl1.py
    # file,
    # and intermediate_output="path-to-output-file" to save
    # intermediate products

    # Pass in QRegister(s) NOT real Qubits
    q1 = QRegister("q1")

    # FIXME: What are reasonable args for this?!

    # FIXME: See issue #44: Must supply all args to qgl2main for now

#    for func, args, label in [("Reset", (q1, np.linspace(0, 5e-6, 11)), "Reset"),
#                              ("BitFlip3", (q1, [0, 2, 4, 5], 500e-9), "BitFlip"),
#                          ]:
    for func, args, label in [("Reset", (q1, np.linspace(0, 5e-6, 11), 0, 2), "Reset"),
                              ("BitFlip3", (q1, [0, 2, 4, 6], 500e-9, 2), "BitFlip"),
                          ]:

        print(f"\nRun {func}...")
        # Here we know the function is in the current file
        # You could use os.path.dirname(os.path.realpath(__file)) to find files relative to this script,
        # Or os.getcwd() to get files relative to where you ran from. Or always use absolute paths.
        resFunc = compile_function(__file__, func, args)
        # Run the QGL2. Note that the generated function takes no arguments itself
        seq = resFunc()
        if toHW:
            print(f"Compiling {func} sequences to hardware\n")
            fileNames = qgl2_compile_to_hardware(seq, f'{label}/{label}')
            print(f"Compiled sequences; metafile = {fileNames}")
            if plotPulses:
                from QGL.PulseSequencePlotter import plot_pulse_files
                # FIXME: As called, this returns a graphical object to display
                plot_pulse_files(fileNames)
        else:
            print(f"\nGenerated {func} sequences:\n")
            from QGL.Scheduler import schedule

            scheduled_seq = schedule(seq)
            from IPython.lib.pretty import pretty
            print(pretty(scheduled_seq))

if __name__ == "__main__":
    main()
