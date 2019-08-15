# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qreg, qgl2main

from qgl2.qgl1 import X, Id, MEAS, X90, U90

from qgl2.basic_sequences.helpers import create_cal_seqs
from qgl2.util import init

from scipy.constants import pi
import numpy as np

@qgl2decl
def InversionRecovery(qubit: qreg, delays, calRepeats=2):
    """
    Inversion recovery experiment to measure qubit T1

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    delays : delays after inversion before measurement (iterable; seconds)
    calRepeats : how many repetitions of calibration pulses (int)
    """

    # Original: 
    # # Create the basic sequences
    # seqs = [[X(qubit), Id(qubit, d), MEAS(qubit)] for d in delays]

    # # Tack on the calibration scalings
    # seqs += create_cal_seqs((qubit,), calRepeats)

    # fileNames = compile_to_hardware(seqs, 'T1'+('_'+qubit.label)*suffix+'/T1'+('_'+qubit.label)*suffix)
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)
    for d in delays:
        init(qubit)
        X(qubit)
        Id(qubit, length=d)
        MEAS(qubit)

    # Tack on calibration
    create_cal_seqs(qubit, calRepeats)

#    metafile = compile_to_hardware(seqs,
#        'T1' + ('_' + qubit.label) * suffix + '/T1' + ('_' + qubit.label) * suffix,
#        axis_descriptor=[
#            delay_descriptor(delays),
#            cal_descriptor((qubit,), calRepeats)
#        ])


# pulse spacings: 100ns to 10us step by 100ns
# TPPIFreq: 1Mhz (arg is in hz)
@qgl2decl
def Ramsey(qubit: qreg, pulseSpacings, TPPIFreq=0, calRepeats=2):
    """
    Variable pulse spacing Ramsey (pi/2 - tau - pi/2) with optional TPPI.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    pulseSpacings : pulse spacings (iterable; seconds)
    TPPIFreq : frequency for TPPI phase updates of second Ramsey pulse (Hz)
    calRepeats : how many repetitions of calibration pulses (int)
    """

    # Original:
    # # Create the phases for the TPPI
    # phases = 2*pi*TPPIFreq*pulseSpacings

    # # Create the basic Ramsey sequence
    # seqs = [[X90(qubit), Id(qubit, d), U90(qubit, phase=phase), MEAS(qubit)] 
    #         for d,phase in zip(pulseSpacings, phases)]

    # # Tack on the calibration scalings
    # seqs += create_cal_seqs((qubit,), calRepeats)

    # fileNames = compile_to_hardware(seqs, 'Ramsey'+('_'+qubit.label)*suffix+'/Ramsey'+('_'+qubit.label)*suffix)
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)

    # Create the phases for the TPPI
    phases = 2*pi*TPPIFreq*pulseSpacings

    # Creating sequences that look like this:
    # [['X90', 'Id', 'U90', 'M'], ['X90', 'Id', 'U90', 'M']]

    # Create the basic Ramsey sequence
    for d,phase in zip(pulseSpacings, phases):
        init(qubit)
        X90(qubit)
        Id(qubit, length=d)
        U90(qubit, phase=phase)
        MEAS(qubit)

    # Tack on calibration
    create_cal_seqs(qubit, calRepeats)

#    metafile = compile_to_hardware(seqs,
#        'Ramsey' + ('_' + qubit.label) * suffix + '/Ramsey' + ('_' + qubit.label) * suffix,
#        axis_descriptor=[
#            delay_descriptor(pulseSpacings),
#            cal_descriptor((qubit,), calRepeats)
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

    # FIXME: See issue #44: Must supply all args to qgl2main for now

    # InversionRecovery(q1,  np.linspace(0, 5e-6, 11))
    # Ramsey(q1, np.linspace(0, 5e-6, 11))

#    for func, args, label in [("InversionRecovery", (q1, np.linspace(0, 5e-6, 11)), "InversionRecovery"),
#                              ("Ramsey", (q1, np.linspace(0, 5e-6, 11)), "Ramsey")
#                          ]:
    for func, args, label in [("InversionRecovery", (q1, np.linspace(0, 5e-6, 11), 2), "InversionRecovery"),
                              ("Ramsey", (q1, np.linspace(0, 5e-6, 11), 0, 2), "Ramsey")
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
