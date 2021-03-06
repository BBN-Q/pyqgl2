# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.basic_sequences.helpers import create_cal_seqs, measConcurrently, cal_descriptor, delay_descriptor
from qgl2.qgl2 import qgl2decl, qreg, QRegister
from qgl2.qgl1 import Utheta, MEAS, X, Id
from qgl2.util import init

# For tanh shape function
import QGL.PulseShapes

@qgl2decl
def RabiAmp(qubit: qreg, amps, phase=0):
    """
    Variable amplitude Rabi nutation experiment.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel)
    amps : pulse amplitudes to sweep over (iterable)
    phase : phase of the pulse (radians)
    """
    for amp in amps:
        init(qubit)
        Utheta(qubit, amp=amp, phase=phase)
        MEAS(qubit)
#    axis_descriptor = [{
#        'name': 'amplitude',
#        'unit': None,
#        'points': list(amps),
#        'partition': 1
#    }]

#    metafile = compile_to_hardware(seqs, 'Rabi/Rabi', axis_descriptor=axis_descriptor)

# Note that QGL2 gives a warning printing the tanh function; harmless
@qgl2decl
def RabiWidth(qubit: qreg, widths, amp=1, phase=0, shape_fun=QGL.PulseShapes.tanh):
    """
    Variable pulse width Rabi nutation experiment.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel)
    widths : pulse widths to sweep over (iterable)
    phase : phase of the pulse (radians, default = 0)
    shape_fun : shape of pulse (function, default = PulseShapes.tanh)
    """

    # Original created 1 seq per width. This is same pulses, but in 1 sequence
    for l in widths:
        init(qubit)
        Utheta(qubit, length=l, amp=amp, phase=phase, shape_fun=shape_fun)
        MEAS(qubit)
#    metafile = compile_to_hardware(seqs, 'Rabi/Rabi',
#        axis_descriptor=[delay_descriptor(widths)])

@qgl2decl
def RabiAmp_NQubits(qubits: qreg, amps, phase=0,
                      measChans: qreg=None, docals=False, calRepeats=2):
    """
    Variable amplitude Rabi nutation experiment for an arbitrary number of qubits simultaneously

    Parameters
    ----------
    qubits : tuple of logical channels to implement sequence (LogicalChannel)
    amps : pulse amplitudes to sweep over for all qubits (iterable)
    phase : phase of the pulses (radians)
    measChans : tuple of qubits to be measured (use qubits if not specified) (LogicalChannel)
    docals, calRepeats: enable calibration sequences, repeated calRepeats times
    """
    if measChans is None:
        measChans = qubits
    allChans = QRegister(qubits, measChans)
    for amp in amps:
        init(allChans)
        Utheta(qubits, amp=amp, phase=phase)
        measConcurrently(measChans)

    if docals:
        create_cal_seqs(qubits, calRepeats, measChans)

#    axis_descriptor = [
#        {
#            'name': 'amplitude',
#            'unit': None,
#            'points': list(amps),
#            'partition': 1
#        },
#        cal_descriptor(qubits, calRepeats)
#    ]

#    metafile = compile_to_hardware(seqs, 'Rabi/Rabi',
#        axis_descriptor=axis_descriptor)

@qgl2decl
def RabiAmpPi(qubit: qreg, mqubit: qreg, amps, phase=0):
    """
    Variable amplitude Rabi nutation experiment.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel)
    mqubit : logical measurement channel to implement sequence (LogicalChannel)
              If None then use qubit
    amps : pulse amplitudes to sweep over (iterable)
    phase : phase of the pulse (radians)
    """
    if mqubit is None:
        mqubit = qubit
    qNm = QRegister(qubit, mqubit)
    for amp in amps:
        init(qNm)
        X(mqubit)
        Utheta(qubit, amp=amp, phase=phase)
        X(mqubit)
        MEAS(mqubit)
#    axis_descriptor = [{
#        'name': 'amplitude',
#        'unit': None,
#        'points': list(amps),
#        'partition': 1
#    }]

#    metafile = compile_to_hardware(seqs, 'Rabi/Rabi', axis_descriptor=axis_descriptor)

@qgl2decl
def SingleShot(qubit: qreg):
    """
    2-segment sequence with qubit prepared in |0> and |1>, useful for single-shot fidelity measurements and kernel calibration
    """
    init(qubit)
    Id(qubit)
    MEAS(qubit)
    init(qubit)
    X(qubit)
    MEAS(qubit)

#    axis_descriptor = {
#        'name': 'state',
#        'unit': 'state',
#        'points': ["0", "1"],
#        'partition': 1
#    }

#    metafile = compile_to_hardware(seqs, 'SingleShot/SingleShot')

@qgl2decl
def SingleShotNoArg():
    """
    Sample 0-argument 2-segment sequence with qubit prepared in |0> and |1>, useful for single-shot fidelity measurements and kernel calibration
    """
    qubit = QRegister(1)
    init(qubit)
    Id(qubit)
    MEAS(qubit)
    init(qubit)
    X(qubit)
    MEAS(qubit)

@qgl2decl
def PulsedSpec(qubit: qreg, specOn=True):
    """
    Measurement preceded by a X pulse if specOn
    """
    init(qubit)
    if specOn:
        X(qubit)
    else:
        Id(qubit)
    MEAS(qubit)
#    metafile = compile_to_hardware(seqs, 'Spec/Spec')

@qgl2decl
def Swap(qubit: qreg, delays, mqubit: qreg =None):
    # Note: Not a QGL1 basic sequence any more, but preserving this anyhow

    # Original:
    # seqs = [[X(qubit), X(mqubit), Id(mqubit, d), MEAS(mqubit)*MEAS(qubit)] for d in delays] + create_cal_seqs((mqubit,qubit), 2, measChans=(mqubit,qubit))

    # fileNames = compile_to_hardware(seqs, 'Rabi/Rabi')
    # print(fileNames)

    # if showPlot:
    #     plotWin = plot_pulse_files(fileNames)
    #     return plotWin
    if mqubit is None:
        mqubit = qubit
    allChans = QRegister(qubit, mqubit)
    for d in delays:
        init(allChans)
        X(qubit)
        X(mqubit)
        Id(mqubit, length=d)
        measConcurrently(allChans)

    create_cal_seqs(allChans, 2)

# A main for running the sequences here with some typical argument values
# Here it runs all of them; could do a parse_args like main.py
def main():
    from pyqgl2.qreg import QRegister
    import pyqgl2.test_cl
    from pyqgl2.main import compile_function, qgl2_compile_to_hardware
    import numpy as np
    import QGL.PulseShapes

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
    qr = QRegister(q1, q2)

    rAmpAmps = np.linspace(0, 1, 1)
    rWidthWidths = np.linspace(0, 5e-6, 11)
    ranqAmps = np.linspace(0, 5e-6, 11)
    tCalR = 2
    rAmpPiAmps = np.linspace(0, 1, 11)

    def getRAmpAD(amps):
        return [{
            'name': 'amplitude',
            'unit': None,
            'points': list(amps),
            'partition': 1
        }]
    def getRWidthAD(widths):
        return [delay_descriptor(widths)]

    def getRAmpNQAD(qubits, amps, calRepeats):
        return [
            {
                'name': 'amplitude',
                'unit': None,
                'points': list(amps),
                'partition': 1
            },
            cal_descriptor(qubits, calRepeats)
        ]

    def getRAmpPiAD(amps):
        return [{
            'name': 'amplitude',
            'unit': None,
            'points': list(amps),
            'partition': 1
        }]

    # FIXME: See issue #44: Must supply all args to qgl2main for now

#    for func, args, label, axisDec in [("RabiAmp", (q1, rAmpAmps), "Rabi", getRAmpAD(rAmpAmps)),
#                              ("RabiWidth", (q1, rWidthWidths), "Rabi", getRWidthAD(rWidthWidths)),
#                              ("RabiAmpPi", (q1, q2, rAmpPiAmps), "Rabi", getRAmpPiAD(rAmpPiAmps)),
#                              ("SingleShow", (q1,), "SingleShot", None),
#                              ("PulsedSpec", (q1,), "Spec", None),
#                              ("RabiAmp_NQubits", (qr,ranqAmps), "Rabi", getRAmpNQAD(qr, ranqAmps, tCalR)),
#                              ("Swap", (q1, np.linspace(0, 5e-6, 11), "Swap", None),
#                          ]:

    for func, args, label, axisDesc in [("RabiAmp", (q1, rAmpAmps, 0), "Rabi", getRAmpAD(rAmpAmps)),
                              ("RabiWidth", (q1, rWidthWidths, 1, 0, QGL.PulseShapes.tanh), "Rabi", getRWidthAD(rWidthWidths)),
                              ("RabiAmpPi", (q1, q2, rAmpPiAmps, 0), "Rabi", getRAmpPiAD(rAmpPiAmps)),
                              ("SingleShot", (q1,), "SingleShot", None),
                              ("PulsedSpec", (q1,True), "Spec", None),
                              ("RabiAmp_NQubits", (qr,ranqAmps, 0, qr, False, tCalR), "Rabi", getRAmpNQAD(qr, ranqAmps, tCalR)),
                              ("Swap", (q1, np.linspace(0, 5e-6, 11), q2), "Swap", None)
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
            # To get verbose logging including showing the compiled sequences:
            # QGL.Compiler.set_log_level()
            fileNames = qgl2_compile_to_hardware(seq, filename=f'{label}/{label}', axis_descriptor=axisDesc)
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
