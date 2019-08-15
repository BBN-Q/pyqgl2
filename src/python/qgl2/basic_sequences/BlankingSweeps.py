# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
Sequences for optimizing gating timing.
OBE: This assumes you modify the gateDelay on a generator. That is no longer a thing.
"""

from qgl2.qgl2 import qgl2decl, qreg
from qgl2.qgl1 import Id, X90, MEAS
from qgl2.util import init

@qgl2decl
def sweep_gateDelaySeqs(qubit: qreg):
    # QGL2 function to generate the sequence used in sweep_gateDelay
    # a simple Id, Id, X90, X90 sequence
    init(qubit)
    Id(qubit, length=120e-9)
    Id(qubit)
    MEAS(qubit)
    Id(qubit, length=120e-9)
    MEAS(qubit)
    Id(qubit, length=120e-9)
    X90(qubit)
    MEAS(qubit)
    Id(qubit, length=120e-9)
    X90(qubit)
    MEAS(qubit)

def sweep_gateDelay(qubit, sweepPts, qgl2func, plotPulses=False):
    """
    OBE: Sweep the gate delay associated with a qubit channel using a simple Id, Id, X90, X90
    sequence. But the gateDelay on a generator is no longer a thing

    Parameters
    ---------
    qubit : logical qubit to create sequences for
    sweepPts : iterable to sweep the gate delay over.
    qgl2func : compiled QGL2 function that generates sequences when run
    """
    # Original:
#    generator = qubit.phys_chan.generator
#    oldDelay = generator.gateDelay

#    for ct, delay in enumerate(sweepPts):
#        seqs = [[Id(qubit, length=120e-9), Id(qubit), MEAS(qubit)],
#                [Id(qubit, length=120e-9), MEAS(qubit)],
#                [Id(qubit, length=120e-9), X90(qubit), MEAS(qubit)],
#                [Id(qubit, length=120e-9), X90(qubit), MEAS(qubit)]]

#        generator.gateDelay = delay

#        compile_to_hardware(seqs, 'BlankingSweeps/GateDelay', suffix='_{}'.format(ct+1))

#    generator.gateDelay = oldDelay

    # Problem in doing in QGL2: Need params of the real qubit, which we don't have.
    # SO, use a combo: QGL1 (looping and doing compile) and QGL2 (generating sequences)
    from pyqgl2.main import qgl2_compile_to_hardware

    # WONTFIX: Generators no longer have a gateDelay
    # But this shows the kind of thing you could do when mixing QGL1 and QGL2
    # generator = qubit.phys_chan.generator
    # oldDelay = generator.gateDelay

    for ct, delay in enumerate(sweepPts):
        seqs = qgl2func()
        # generator.gateDelay = delay
        metafile=qgl2_compile_to_hardware(seqs, 'BlankingSweeps/GateDelay', suffix='_{}'.format(ct+1))
        print(f"Compiled sequences; metafile = {metafile}")
        if plotPulses:
            from QGL.PulseSequencePlotter import plot_pulse_files
            # FIXME: As called, this returns a graphical object to display
            plot_pulse_files(metafile)

    # generator.gateDelay = oldDelay


# QGL1 function to compile the above QGL2
# Uses main.py functions
# FIXME: Use the same argument parsing as main.py
# NOTE: This does not wark, as generator no longer has a gateDelay
def main():
    from pyqgl2.qreg import QRegister
    import pyqgl2.test_cl
    from pyqgl2.main import compile_function

    toHW = True
    plotPulses = True
    pyqgl2.test_cl.create_default_channelLibrary(toHW, True)
    # Note: That doesn't put a generator on the phys_chan, which we would need to really run this

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
    # Here we know the function is in the current file
    # You could use os.path.dirname(os.path.realpath(__file)) to find files relative to this script,
    # Or os.getcwd() to get files relative to where you ran from. Or always use absolute paths.
    resFunction = compile_function(__file__,
                                               "sweep_gateDelaySeqs",
                                               (q,))
    # Run the QGL2. Note that the generated function takes no arguments itself
    if toHW:
        from QGL.ChannelLibraries import QubitFactory
        import numpy as np
        print("Compiling sequences to hardware\n")
        qubit = QubitFactory('q1')
        if qubit.phys_chan is None:
            print(f"Qubit {qubit} missing phys_chan")
            return
#        elif qubit.phys_chan.generator is None:
#            print(f"Qubit {qubit} on phys_chan {qubit.phys_chan} missing phys_chan.generator")
#            return

        # FIXME: What's a reasonable value here?
        sweepPts = np.linspace(0, 5e-6, 11)

        # Here we call a special QGL1 function that uses the compiled QGL2 function to generate sequences
        # We redo the sequence generation to avoid the compiler modifying the sequence causing problems
        # This function will handle compile_to_hardware and plot_pulse_files
        sweep_gateDelay(qubit, sweepPts, resFunction, plotPulses)
    else:
        sequences = resFunction()
        print("\nGenerated sequences:\n")
        from QGL.Scheduler import schedule

        scheduled_seq = schedule(sequences)
        from IPython.lib.pretty import pretty
        print(pretty(scheduled_seq))

if __name__ == "__main__":
    main()
