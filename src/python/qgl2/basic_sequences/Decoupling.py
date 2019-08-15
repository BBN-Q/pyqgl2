# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qreg

from qgl2.qgl1 import X90, Id, Y, U90, MEAS, pulseCentered
from qgl2.basic_sequences.helpers import create_cal_seqs
from qgl2.util import init

from math import pi

@qgl2decl
def HahnEcho(qubit: qreg, pulseSpacings, periods = 0, calRepeats=2):
    """
    A single pulse Hahn echo with variable phase of second pi/2 pulse. 

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    pulseSpacings : pulse spacings to sweep over; the t in 90-t-180-t-180 (iterable)
    periods: number of artificial oscillations
    calRepeats : how many times to repeat calibration scalings (default 2)
    """

    # Original:
    # seqs=[];
    # for k in range(len(pulseSpacings)):
    #     seqs.append([X90(qubit), Id(qubit, pulseSpacings[k]), Y(qubit), Id(qubit,pulseSpacings[k]), \
    #                  U90(qubit,phase=2*pi*periods/len(pulseSpacings)*k), MEAS(qubit)])

    # # Tack on the calibration scalings
    # seqs += create_cal_seqs((qubit,), calRepeats)

    # fileNames = compile_to_hardware(seqs, 'Echo/Echo')
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)

    for k in range(len(pulseSpacings)):
        init(qubit)
        X90(qubit)
        # FIXME 9/28/16: Must name the length arg (issue #45)
        Id(qubit, length=pulseSpacings[k])
        Y(qubit)
        Id(qubit, length=pulseSpacings[k])
        U90(qubit, phase=2*pi*periods/len(pulseSpacings)*k)
        MEAS(qubit)

    create_cal_seqs(qubit, calRepeats)

#    compileAndPlot('Echo/Echo', showPlot)

@qgl2decl
def CPMG(qubit: qreg, numPulses, pulseSpacing, calRepeats=2):
    """
    CPMG pulse train with fixed pulse spacing. Note this pulse spacing is centre to centre,
    i.e. it accounts for the pulse width

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    numPulses : number of 180 pulses; should be even (iterable)
    pulseSpacing : spacing between the 180's (seconds)
    calRepeats : how many times to repeat calibration scalings (default 2)
    """

    # Original:
    # # First setup the t-180-t block
    # CPMGBlock = [Id(qubit, (pulseSpacing-qubit.pulse_params['length'])/2),
    #              Y(qubit), Id(qubit, (pulseSpacing-qubit.pulse_params['length'])/2)]

    # seqs = [[X90(qubit)] + CPMGBlock*rep + [X90(qubit), MEAS(qubit)] for rep in numPulses]

    # # Tack on the calibration scalings
    # seqs += create_cal_seqs((qubit,), calRepeats)

    # fileNames = compile_to_hardware(seqs, 'CPMG/CPMG')
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)

    # Create numPulses sequences
    for rep in numPulses:
        init(qubit)
        X90(qubit)
        # Repeat the t-180-t block rep times
        for _ in range(rep):
            pulseCentered(qubit, Id, pulseSpacing)
            Y(qubit)
            pulseCentered(qubit, Id, pulseSpacing)
        X90(qubit)
        MEAS(qubit)

    # Tack on calibration
    create_cal_seqs(qubit, calRepeats)

#    compileAndPlot('CPMG/CPMG', showPlot)

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

    # FIXME: See issue #44: Must supply all args to qgl2main for now

#    for func, args, label in [("HahnEcho", (q1, np.linspace(0, 5e-6, 11)), "HahnEcho"),
#                              ("CPMG", (q1, [0, 2, 4, 5], 500e-9), "CPMG"),
#                          ]:
    for func, args, label in [("HahnEcho", (q1, np.linspace(0, 5e-6, 11), 0, 2), "HahnEcho"),
                              ("CPMG", (q1, [0, 2, 4, 6], 500e-9, 2), "CPMG"),
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
