# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qreg, qgl2main, pulse, QRegister

from qgl2.qgl1 import X, U, Y90, X90, MEAS, Id

from qgl2.util import init

from itertools import chain
from numpy import pi

@qgl2decl
def spam_seqs(angle, qubit: qreg, maxSpamBlocks=10):
    """ Helper function to create a list of sequences increasing SPAM blocks with a given angle. """
    #SPAMBlock = [X(qubit), U(qubit, phase=pi/2+angle), X(qubit), U(qubit, phase=pi/2+angle)]
    #return [[Y90(qubit)] + SPAMBlock*rep + [X90(qubit)] for rep in range(maxSpamBlocks)]
    for rep in range(maxSpamBlocks):
        init(qubit)
        Y90(qubit)
        for _ in range(rep):
            X(qubit)
            U(qubit, phase=pi/2+angle)
            X(qubit)
            U(qubit, phase=pi/2+angle)
        X90(qubit)
        MEAS(qubit)

@qgl2decl
def SPAM(qubit: qreg, angleSweep, maxSpamBlocks=10):
    """
    X-Y sequence (X-Y-X-Y)**n to determine quadrature angles or mixer correction.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    angleSweep : angle shift to sweep over
    maxSpamBlocks : maximum number of XYXY block to do
    """
    # Original:
    # def spam_seqs(angle):
    #     """ Helper function to create a list of sequences increasing SPAM blocks with a given angle. """
    #     SPAMBlock = [X(qubit), U(qubit, phase=pi/2+angle), X(qubit), U(qubit, phase=pi/2+angle)]
    #     return [[Y90(qubit)] + SPAMBlock*rep + [X90(qubit)] for rep in range(maxSpamBlocks)]

    # # Insert an identity at the start of every set to mark them off
    # seqs = list(chain.from_iterable([[[Id(qubit)]] + spam_seqs(angle) for angle in angleSweep]))

    # # Add a final pi for reference
    # seqs.append([X(qubit)])

    # # Add the measurment block to every sequence
    # measBlock = MEAS(qubit)
    # for seq in seqs:
    #     seq.append(measBlock)

    # fileNames = compile_to_hardware(seqs, 'SPAM/SPAM')
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)

    # Insert an identity at the start of every set to mark them off
    for angle in angleSweep:
        init(qubit)
        Id(qubit)
        MEAS(qubit)
        spam_seqs(angle, qubit, maxSpamBlocks)

    # Add a final pi for reference
    init(qubit)
    X(qubit)
    MEAS(qubit)

#    compileAndPlot('SPAM/SPAM', showPlot)

# QGL1 function to compile the above QGL2
# Uses main.py
# FIXME: Use the same argument parsing as main.py
def main():
    from pyqgl2.qreg import QRegister
    import pyqgl2.test_cl
    from pyqgl2.main import compile_function, qgl2_compile_to_hardware
    import numpy as np

    toHW = True
    plotPulses = True
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

    # Pass in a QRegister NOT the real Qubit
    q = QRegister(1)

    # SPAM(q1, np.linspace(0, pi/2, 11))
    # - test_basic_mins uses np.linspace(0,1,11)

    # Here we know the function is in the current file
    # You could use os.path.dirname(os.path.realpath(__file)) to find files relative to this script,
    # Or os.getcwd() to get files relative to where you ran from. Or always use absolute paths.
    resFunction = compile_function(__file__,
                                               "SPAM",
                                               (q, np.linspace(0, pi/2, 11), 10))
    # Run the QGL2. Note that the generated function takes no arguments itself
    sequences = resFunction()
    if toHW:
        print("Compiling sequences to hardware\n")
        fileNames = qgl2_compile_to_hardware(sequences, 'SPAM/SPAM')
        print(f"Compiled sequences; metafile = {fileNames}")
        if plotPulses:
            from QGL.PulseSequencePlotter import plot_pulse_files
            # FIXME: As called, this returns a graphical object to display
            plot_pulse_files(fileNames)
    else:
        print("\nGenerated sequences:\n")
        from QGL.Scheduler import schedule

        scheduled_seq = schedule(sequences)
        from IPython.lib.pretty import pretty
        print(pretty(scheduled_seq))

if __name__ == "__main__":
    main()
