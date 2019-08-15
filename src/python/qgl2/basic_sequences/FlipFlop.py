# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qreg, qgl2main, pulse
from qgl2.qgl1 import X90, X90m, Y90, Id, X, MEAS
from qgl2.util import init

from itertools import chain

@qgl2decl
def flipflop_seqs(dragScaling, maxNumFFs, qubit: qreg):
    """ Helper function to create a list of sequences with a specified drag parameter. """
    # QGL2 qubits are read only.
    # So instead, supply the dragScaling as an explicit kwarg to all pulses
    # qubit.pulse_params['dragScaling'] = dragScaling

    for rep in range(maxNumFFs):
        init(qubit)
        X90(qubit, dragScaling=dragScaling)
        for _ in range(rep):
            X90(qubit, dragScaling=dragScaling)
            X90m(qubit, dragScaling=dragScaling)
        Y90(qubit, dragScaling=dragScaling)
        MEAS(qubit)

@qgl2decl
def FlipFlop(qubit: qreg, dragParamSweep, maxNumFFs=10):
    """
    Flip-flop sequence (X90-X90m)**n to determine off-resonance or DRAG parameter optimization.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    dragParamSweep : drag parameter values to sweep over (iterable)
    maxNumFFs : maximum number of flip-flop pairs to do
    """

    # Original:
    # def flipflop_seqs(dragScaling):
    #     """ Helper function to create a list of sequences with a specified drag parameter. """
    #     qubit.pulse_params['dragScaling'] = dragScaling
    #     return [[X90(qubit)] + [X90(qubit), X90m(qubit)]*rep + [Y90(qubit)] for rep in range(maxNumFFs)]

    # # Insert an identity at the start of every set to mark them off
    # originalScaling = qubit.pulse_params['dragScaling']
    # seqs = list(chain.from_iterable([[[Id(qubit)]] + flipflop_seqs(dragParam) for dragParam in dragParamSweep]))
    # qubit.pulse_params['dragScaling'] = originalScaling

    # # Add a final pi for reference
    # seqs.append([X(qubit)])

    # # Add the measurment block to every sequence
    # measBlock = MEAS(qubit)
    # for seq in seqs:
    #     seq.append(measBlock)

    # fileNames = compile_to_hardware(seqs, 'FlipFlop/FlipFlop')
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)

    # Insert an identity at the start of every set to mark them off
    # Want a result something like:
    # [['Id'], ['X9', 'Y9'], ['X9', 'X9', 'X9m', 'Y9'], ['X9', 'X9', 'X9m', 'X9', 'X9m', 'Y9'], ['Id'], ['X9', 'Y9'], ['X9', 'X9', 'X9m', 'Y9'], ['X9', 'X9', 'X9m', 'X9', 'X9m', 'Y9'], ['Id'], ['X9', 'Y9'], ['X9', 'X9', 'X9m', 'Y9'], ['X9', 'X9', 'X9m', 'X9', 'X9m', 'Y9']]

    # QGL2 qubits are read only, so can't modify qubit.pulse_params[dragScaling],
    # Instead of modifying qubit, we'll just supply the drag param explicitly to each pulse
    # So no need to save this off and reset afterwards
    # originalScaling = qubit.pulse_params['dragScaling']
    for dragParam in dragParamSweep:
        init(qubit)
        Id(qubit)
        MEAS(qubit)

        flipflop_seqs(dragParam, maxNumFFs, qubit)
    # qubit.pulse_params['dragScaling'] = originalScaling

    # Add a final pi for reference
    init(qubit)
    X(qubit)
    MEAS(qubit)

    # Final result is something like this:
    # [['Id', 'M'], ['X9', 'Y9', 'M'], ['X9', 'X9', 'X9m', 'Y9', 'M'],
    # ['X9', 'X9', 'X9m', 'X9', 'X9m', 'Y9', 'M'], ['Id', 'M'], ['X9',
    # 'Y9', 'M'], ['X9', 'X9', 'X9m', 'Y9', 'M'], ['X9', 'X9', 'X9m',
    # 'X9', 'X9m', 'Y9', 'M'], ['Id', 'M'], ['X9', 'Y9', 'M'], ['X9',
    # 'X9', 'X9m', 'Y9', 'M'], ['X9', 'X9', 'X9m', 'X9', 'X9m', 'Y9',
    # 'M'], ['X', 'M']]

#    compileAndPlot('FlipFlop/FlipFlop', showPlot)

# QGL1 function to compile the above QGL2
# Uses main.py
# FIXME: Use the same argument parsing as in main.py
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
    # file, and intermediate_output="path-to-output-file" to save
    # intermediate products

    # Pass in a QRegister NOT the real Qubit
    q = QRegister(1)
    # Here we do FlipFlop(q1, np.linspace(0, 5e-6, 11))
    # - test_basic_mins uses np.linspace(0,1,11)

    # Here we know the function is in the current file
    # You could use os.path.dirname(os.path.realpath(__file)) to find files relative to this script,
    # Or os.getcwd() to get files relative to where you ran from. Or always use absolute paths.
    resFunction = compile_function(__file__,
                                               "FlipFlop",
                                               (q, np.linspace(0, 5e-6, 11), 10))
    # Run the QGL2. Note that the generated function takes no arguments itself
    sequences = resFunction()
    if toHW:
        print("Compiling sequences to hardware\n")
        fileNames = qgl2_compile_to_hardware(sequences, 'FlipFlop/FlipFlop')
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
