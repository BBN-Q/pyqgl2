# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qreg, QRegister

from qgl2.qgl1 import Id, X, MEAS, X90, flat_top_gaussian_edge, echoCR, Y90m

from qgl2.basic_sequences.helpers import create_cal_seqs, measConcurrently
from qgl2.util import init

from itertools import product
import numpy as np

@qgl2decl
def PiRabi(controlQ: qreg, targetQ: qreg, lengths, riseFall=40e-9, amp=1, phase=0, calRepeats=2):
    """
    Variable length CX experiment.

    Parameters
    ----------
    controlQ : logical channel for the control qubit (LogicalChannel)
    targetQ: logical channel for the target qubit (LogicalChannel)
    lengths : pulse lengths of the CR pulse to sweep over (iterable)
    riseFall : rise/fall time of the CR pulse (s)
    amp : amplitude of the CR pulse
    phase : phase of the CR pulse (rad)
    calRepeats : number repetitions of calibration sequences (int)
    """

    # Rather than do EdgeFactory and regular flat_top_gaussian,
    # define a new QGL2 stub where the QGL1 implementation does that,
    # so QGL2 can avoid dealing with the edge
    # CRchan = EdgeFactory(controlQ, targetQ)

    # flat_top_gaussian is an addition of 3 UTheta pulses

    cNt = QRegister(controlQ, targetQ)

    # Sequence 1: Id(control), gaussian(l), measure both
    for l in lengths:
        init(cNt)
        Id(controlQ)
        flat_top_gaussian_edge(controlQ, targetQ, riseFall, length=l, amp=amp, phase=phase)
        measConcurrently(cNt)

    # Sequence 2: X(control), gaussian(l), X(control), measure both
    for l in lengths:
        init(cNt)
        X(controlQ)
        flat_top_gaussian_edge(controlQ, targetQ, riseFall, length=l, amp=amp, phase=phase)
        X(controlQ)
        measConcurrently(cNt)

    # Then do calRepeats calibration sequences
    create_cal_seqs(cNt, calRepeats)

#    metafile = compile_to_hardware(seqs, 'PiRabi/PiRabi',
#        axis_descriptor=[
#            delay_descriptor(np.concatenate((lengths, lengths))),
#            cal_descriptor((controlQ, targetQ), calRepeats)
#        ])

@qgl2decl
def EchoCRLen(controlQ: qreg, targetQ: qreg, lengths, riseFall=40e-9, amp=1, phase=0, calRepeats=2, canc_amp=0, canc_phase=np.pi/2):
    """
    Variable length CX experiment, with echo pulse sandwiched between two CR opposite-phase pulses.

    Parameters
    ----------
    controlQ : logical channel for the control qubit (LogicalChannel)
    targetQ: logical channel for the target qubit (LogicalChannel)
    lengths : pulse lengths of the CR pulse to sweep over (iterable)
    riseFall : rise/fall time of the CR pulse (s)
    amp : amplitude of the CR pulse
    phase : phase of the CR pulse (rad)
    calRepeats : number of repetitions of readout calibrations for each 2-qubit state
    """
    # Original: 
    # seqs = [[Id(controlQ)] + echoCR(controlQ, targetQ, length=l, phase=phase, riseFall=riseFall) + [Id(controlQ), MEAS(targetQ)*MEAS(controlQ)] \
    #         for l in lengths]+ [[X(controlQ)] + echoCR(controlQ, targetQ, length=l, phase= phase, riseFall=riseFall) + [X(controlQ), MEAS(targetQ)*MEAS(controlQ)] \
    #                             for l in lengths] + create_cal_seqs((targetQ,controlQ), calRepeats, measChans=(targetQ,controlQ))

    cNt = QRegister(controlQ, targetQ)

    # Sequence1:
    for l in lengths:
        init(cNt)
        Id(controlQ)
        echoCR(controlQ, targetQ, length=l, phase=phase, amp=amp,
               riseFall=riseFall, canc_amp=canc_amp, canc_phase=canc_phase)
        Id(controlQ)
        measConcurrently(cNt)

    # Sequence 2
    for l in lengths:
        init(cNt)
        X(controlQ)
        echoCR(controlQ, targetQ, length=l, phase=phase, amp=amp,
               riseFall=riseFall, canc_amp=canc_amp, canc_phase=canc_phase)
        X(controlQ)
        measConcurrently(cNt)

    # Then do calRepeats calibration sequences
    create_cal_seqs(cNt, calRepeats)

#    metafile = compile_to_hardware(seqs, 'EchoCR/EchoCR',
#        axis_descriptor=[
#            delay_descriptor(np.concatenate((lengths, lengths))),
#            cal_descriptor((controlQ, targetQ), calRepeats)
#        ])

@qgl2decl
def EchoCRPhase(controlQ: qreg, targetQ: qreg, phases, riseFall=40e-9, amp=1, length=100e-9, calRepeats=2, canc_amp=0, canc_phase=np.pi/2):
    """
    Variable phase CX experiment, with echo pulse sandwiched between two CR opposite-phase pulses.

    Parameters
    ----------
    controlQ : logical channel for the control qubit (LogicalChannel)
    targetQ : logical channel for the cross-resonance pulse (LogicalChannel)
    phases : pulse phases of the CR pulse to sweep over (iterable)
    riseFall : rise/fall time of the CR pulse (s)
    amp : amplitude of the CR pulse
    length : duration of each of the two flat parts of the CR pulse (s)
    calRepeats : number of repetitions of readout calibrations for each 2-qubit state
    """
    # Original:
    # seqs = [[Id(controlQ)] + echoCR(controlQ, targetQ, length=length, phase=ph, riseFall=riseFall) + [X90(targetQ)*Id(controlQ), MEAS(targetQ)*MEAS(controlQ)] \
    #         for ph in phases]+[[X(controlQ)] + echoCR(controlQ, targetQ, length=length, phase= ph, riseFall = riseFall) + [X90(targetQ)*X(controlQ), MEAS(targetQ)*MEAS(controlQ)] \
    #                            for ph in phases]+create_cal_seqs((targetQ,controlQ), calRepeats, measChans=(targetQ,controlQ))

    cNt = QRegister(controlQ, targetQ)

    # Sequence 1
    for ph in phases:
        init(cNt)
        Id(controlQ)
        echoCR(controlQ, targetQ, length=length, phase=ph,
               riseFall=riseFall, canc_amp=canc_amp, canc_phase=canc_phase)
        Barrier(cNt)
        X90(targetQ)
        Id(controlQ)
        measConcurrently(cNt)

    # Sequence 2
    for ph in phases:
        init(cNt)
        X(controlQ)
        echoCR(controlQ, targetQ, length=length, phase=ph,
               riseFall=riseFall, canc_amp=canc_amp, canc_phase=canc_phase)
        Barrier(cNt)
        X90(targetQ)
        X(controlQ)
        measConcurrently(cNt)

    # Then do calRepeats calibration sequences
    create_cal_seqs(cNt, calRepeats)

#    axis_descriptor = [
#        {
#            'name': 'phase',
#            'unit': 'radians',
#            'points': list(phases)+list(phases),
#            'partition': 1
#        },
#        cal_descriptor((controlQ, targetQ), calRepeats)
#    ]
#
#    metafile = compile_to_hardware(seqs, 'EchoCR/EchoCR',
#        axis_descriptor=axis_descriptor)

@qgl2decl
def EchoCRAmp(controlQ: qreg,
              targetQ: qreg,
              amps,
              riseFall=40e-9,
              length=50e-9,
              phase=0,
              calRepeats=2):
    """
	Variable amplitude CX experiment, with echo pulse sandwiched between two CR opposite-phase pulses.

	Parameters
	----------
	controlQ : logical channel for the control qubit (LogicalChannel)
	targetQ: logical channel for the target qubit (LogicalChannel)
	amps : pulse amplitudes of the CR pulse to sweep over (iterable)
	riseFall : rise/fall time of the CR pulse (s)
	length : duration of each of the two flat parts of the CR pulse (s)
	phase : phase of the CR pulse (rad)
	calRepeats : number of repetitions of readout calibrations for each 2-qubit state
	"""
    cNt = QRegister(controlQ, targetQ)

    # Sequence 1
    for a in amps:
        init(cNt)
        Id(controlQ)
        echoCR(controlQ, targetQ, length=length, phase=phase, riseFall=riseFall,amp=a)
        Id(controlQ)
        measConcurrently(cNt)

    # Sequence 2
    for a in amps:
        init(cNt)
        X(controlQ)
        echoCR(controlQ, targetQ, length=length, phase= phase, riseFall=riseFall,amp=a)
        X(controlQ)
        measConcurrently(cNt)

    # Then do calRepeats calibration sequences
    create_cal_seqs(cNt, calRepeats)

#    axis_descriptor = [
#        {
#            'name': 'amplitude',
#            'unit': None,
#            'points': list(amps)+list(amps),
#            'partition': 1
#        },
#        cal_descriptor((controlQ, targetQ), calRepeats)
#    ]

#    metafile = compile_to_hardware(seqs, 'EchoCR/EchoCR',
#        axis_descriptor=axis_descriptor)

@qgl2decl
def CRtomo_seq(controlQ: qreg, targetQ: qreg, lengths, ph, amp=0.8, riseFall=20e-9):
    """
    Variable length CX experiment, for Hamiltonian tomography.

    Parameters
    ----------
    controlQ : logical channel for the control qubit (LogicalChannel)
    targetQ: logical channel for the target qubit (LogicalChannel)
    lengths : pulse lengths of the CR pulse to sweep over (iterable)
    riseFall : rise/fall time of the CR pulse (s)
    ph : phase of the CR pulse (rad)
    """
    # Rather than do EdgeFactory and regular flat_top_gaussian,
    # define a new QGL2 stub where the QGL1 implementation does that,
    # so QGL2 can avoid dealing with the edge
    # CRchan = EdgeFactory(controlQ, targetQ)

    # flat_top_gaussian is an addition of 3 UTheta pulses
    cNt = QRegister(controlQ, targetQ)
    tomo_pulses = [Y90m, X90, Id]

    # Sequence 1
    for l, tomo_pulse in product(lengths, tomo_pulses):
        init(cNt)
        Id(controlQ)
        flat_top_gaussian_edge(controlQ, targetQ, riseFall=riseFall, length=l, amp=amp, phase=ph, label="CR")
        Barrier(cNt)
        Id(controlQ)
        tomo_pulse(targetQ)
        MEAS(targetQ)

    # Sequence 2
    for l, tomo_pulse in product(lengths, tomo_pulses):
        init(cNt)
        X(controlQ)
        flat_top_gaussian_edge(controlQ, targetQ, riseFall=riseFall, length=l, amp=amp, phase=ph, label="CR")
        Barrier(cNt)
        X(controlQ)
        tomo_pulse(targetQ)
        MEAS(targetQ)

    create_cal_seqs(targetQ, 2)

#    metafile = compile_to_hardware(seqs, 'CR/CR',
#        axis_descriptor=[
#            delay_descriptor(np.concatenate((np.repeat(lengths,3), np.repeat(lengths,3)))),
#            cal_descriptor((targetQ,), 2)
#        ])

# A main for running the sequences here with some typical argument values
# Here it runs all of them; could do a parse_args like main.py
def main():
    from pyqgl2.qreg import QRegister
    import pyqgl2.test_cl
    from pyqgl2.main import compile_function, qgl2_compile_to_hardware

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
    q2 = QRegister("q2")

    # FIXME: See issue #44: Must supply all args to qgl2main for now

#    for func, args, label in [("PiRabi", (q1, q2, np.linspace(0, 4e-6, 11)), "PiRabi"),
#                              ("EchoCRLen", (q1, q2, np.linspace(0, 2e-6, 11)), "EchoCR"),
#                              ("EchoCRPhase", (q1, q2, np.linspace(0, np.pi/2, 11)), "EchoCR"),
#                              ("EchoCRAmp", (q1, q2, np.linspace(0, 5e-6, 11)), "EchoCR"), # FIXME: Right values?
#                              ("CRtomo_seq", (q1, q2, np.linspace(0, 2e-6, 11), 0), "CR") # FIXME: Right values?
#                          ]:
    for func, args, label in [("PiRabi", (q1, q2, np.linspace(0, 4e-6, 11), 40e-9,1,0,2), "PiRabi"),
                              ("EchoCRLen", (q1, q2, np.linspace(0, 2e-6, 11),40e-9,1,0,2,0,np.pi/2), "EchoCR"),
                              ("EchoCRPhase", (q1, q2, np.linspace(0, np.pi/2, 11),40e-9,1,100e-9,2,0,np.pi/2), "EchoCR"),
                              ("EchoCRAmp", (q1, q2, np.linspace(0, 5e-6, 11),40e-9,50e-9,0,2), "EchoCR"), # FIXME: Right values?
                              ("CRtomo_seq", (q1, q2, np.linspace(0, 2e-6, 11), 0, 0.8,20e-9), "CR") # FIXME: Right values?
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
