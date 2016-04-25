# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit, qgl2main

from QGL.PulsePrimitives import X, Id, MEAS, X90, U90
from QGL.Compiler import compile_to_hardware
from QGL.PulseSequencePlotter import plot_pulse_files

from .helpers import create_cal_seqs
from .new_helpers import addCalibration, compileAndPlot
from .qgl2_plumbing import init
from qgl2.qgl1 import X90, Id, U90, MEAS, X, QubitFactory
from qgl2.qgl1 import Sync, Wait

from scipy.constants import pi
import numpy as np

def InversionRecoveryq1(qubit: qbit, delays, showPlot=False, calRepeats=2, suffix=False):
    """
    Inversion recovery experiment to measure qubit T1

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    delays : delays after inversion before measurement (iterable; seconds)
    showPlot : whether to plot (boolean)
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
    seqs = []
    for d in delays:
        seq = []
        seq.append(X(qubit))
        seq.append(Id(qubit, d))
        seq.append(MEAS(qubit))
        seqs.append(seq)

    # Tack on calibration
    seqs = addCalibration(seqs, (qubit,), calRepeats)

    # Calculate label
    label = 'T1'+('_'+qubit.label)*suffix
    fullLabel = label + '/' + label

    # Be sure to un-decorate this function to make it work without the
    # QGL2 compiler
    compileAndPlot(seqs, fullLabel, showPlot)

@qgl2decl
def InversionRecovery(qubit: qbit, delays, showPlot=False, calRepeats=2, suffix=False):
    """
    Inversion recovery experiment to measure qubit T1

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    delays : delays after inversion before measurement (iterable; seconds)
    showPlot : whether to plot (boolean)
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
        Id(qubit, d)
        MEAS(qubit)

    # Tack on calibration
    create_cal_seqs((qubit,), calRepeats)

    # Calculate label
    label = 'T1'+('_'+qubit.label)*suffix
    fullLabel = label + '/' + label

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    compileAndPlot(fullLabel, showPlot)

def Ramseyq1(qubit: qbit, pulseSpacings, TPPIFreq=0, showPlot=False, calRepeats=2, suffix=False):
    """
    Variable pulse spacing Ramsey (pi/2 - tau - pi/2) with optional TPPI.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    pulseSpacings : pulse spacings (iterable; seconds)
    TPPIFreq : frequency for TPPI phase updates of second Ramsey pulse (Hz)
    showPlot : whether to plot (boolean)
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
    seqs = []
    for d,phase in zip(pulseSpacings, phases):
        seq = []
        seq.append(X90(qubit))
        seq.append(Id(qubit, d))
        seq.append(U90(qubit, phase=phase))
        seq.append(MEAS(qubit))
        seqs.append(seq)

    # Tack on calibration
    seqs = addCalibration(seqs, (qubit,), calRepeats)

    # Calculate label
    label = 'Ramsey'+('_'+qubit.label)*suffix
    fullLabel = label + '/' + label

    # Be sure to un-decorate this function to make it work without the
    # QGL2 compiler
    compileAndPlot(seqs, fullLabel, showPlot)

# produce a Ramsey sequence on qbit named q
# pulse spacings: 100ns to 10us step by 100ns
# TPPIFreq: 1Mhz (arg is in hz)
@qgl2decl
def doRamsey() -> sequence:
    q = QubitFactory('q1')
    TPPIFreq=1e6
    # FIXME: QGL2 doesn't deal well with the call to np.arange
    pulseS = [  1.00000000e-07,   2.00000000e-07,   3.00000000e-07,
         4.00000000e-07,   5.00000000e-07,   6.00000000e-07,
         7.00000000e-07,   8.00000000e-07,   9.00000000e-07,
         1.00000000e-06,   1.10000000e-06,   1.20000000e-06,
         1.30000000e-06,   1.40000000e-06,   1.50000000e-06,
         1.60000000e-06,   1.70000000e-06,   1.80000000e-06,
         1.90000000e-06,   2.00000000e-06,   2.10000000e-06,
         2.20000000e-06,   2.30000000e-06,   2.40000000e-06,
         2.50000000e-06,   2.60000000e-06,   2.70000000e-06,
         2.80000000e-06,   2.90000000e-06,   3.00000000e-06,
         3.10000000e-06,   3.20000000e-06,   3.30000000e-06,
         3.40000000e-06,   3.50000000e-06,   3.60000000e-06,
         3.70000000e-06,   3.80000000e-06,   3.90000000e-06,
         4.00000000e-06,   4.10000000e-06,   4.20000000e-06,
         4.30000000e-06,   4.40000000e-06,   4.50000000e-06,
         4.60000000e-06,   4.70000000e-06,   4.80000000e-06,
         4.90000000e-06,   5.00000000e-06,   5.10000000e-06,
         5.20000000e-06,   5.30000000e-06,   5.40000000e-06,
         5.50000000e-06,   5.60000000e-06,   5.70000000e-06,
         5.80000000e-06,   5.90000000e-06,   6.00000000e-06,
         6.10000000e-06,   6.20000000e-06,   6.30000000e-06,
         6.40000000e-06,   6.50000000e-06,   6.60000000e-06,
         6.70000000e-06,   6.80000000e-06,   6.90000000e-06,
         7.00000000e-06,   7.10000000e-06,   7.20000000e-06,
         7.30000000e-06,   7.40000000e-06,   7.50000000e-06,
         7.60000000e-06,   7.70000000e-06,   7.80000000e-06,
         7.90000000e-06,   8.00000000e-06,   8.10000000e-06,
         8.20000000e-06,   8.30000000e-06,   8.40000000e-06,
         8.50000000e-06,   8.60000000e-06,   8.70000000e-06,
         8.80000000e-06,   8.90000000e-06,   9.00000000e-06,
         9.10000000e-06,   9.20000000e-06,   9.30000000e-06,
         9.40000000e-06,   9.50000000e-06,   9.60000000e-06,
         9.70000000e-06,   9.80000000e-06,   9.90000000e-06]
    #pulseSpacings=np.arange(100e-9, 10e-6, 100e-9)
    # Create the phases for the TPPI
    phases = 2*pi*TPPIFreq*pulseS
    # Create the basic Ramsey sequence
    # FIXME: QGL2 doesn't deal well with this call to zip
    for d,phase in zip(pulseS, phases):
        init(q)
        X90(q)
        Id(q, d)
        U90(q, phase=phase)
        MEAS(q)

    # Tack on calibration
    create_cal_seqs((q,), calRepeats)

@qgl2decl
def Ramsey(qubit: qbit, pulseSpacings, TPPIFreq=0, showPlot=False, calRepeats=2, suffix=False):
    """
    Variable pulse spacing Ramsey (pi/2 - tau - pi/2) with optional TPPI.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    pulseSpacings : pulse spacings (iterable; seconds)
    TPPIFreq : frequency for TPPI phase updates of second Ramsey pulse (Hz)
    showPlot : whether to plot (boolean)
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
        Id(qubit, d)
        U90(qubit, phase=phase)
        MEAS(qubit)

    # Tack on calibration
    create_cal_seqs((qubit,), calRepeats)

    # Calculate label
    label = 'Ramsey'+('_'+qubit.label)*suffix
    fullLabel = label + '/' + label

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    compileAndPlot(fullLabel, showPlot)

# Imports for testing only
from QGL.Channels import Qubit, LogicalMarkerChannel, Measurement
import QGL.ChannelLibrary as ChannelLibrary
from qgl2.qgl1 import QubitFactory
import numpy as np
from math import pi

@qgl2main
def main():
    # Set up 2 qbits, following model in QGL/test/test_Sequences

    # FIXME: Cannot use these in current QGL2 compiler, because
    # a: QGL2 doesn't understand creating class instances, and 
    # b: QGL2 currently only understands the fake Qbits
#    qg1 = LogicalMarkerChannel(label="q1-gate")
#    q1 = Qubit(label='q1', gateChan=qg1)
#    q1.pulseParams['length'] = 30e-9
#    q1.pulseParams['phase'] = pi/2
#    sTrig = LogicalMarkerChannel(label='slaveTrig')
#    dTrig = LogicalMarkerChannel(label='digitizerTrig')
#    Mq1 = '';
#    Mq1gate = LogicalMarkerChannel(label='M-q1-gate')
#    m = Measurement(label='M-q1', gateChan = Mq1gate, trigChan = dTrig)

#    ChannelLibrary.channelLib = ChannelLibrary.ChannelLibrary()
#    ChannelLibrary.channelLib.channelDict = {
#        'q1-gate': qg1,
#        'q1': q1,
#        'slaveTrig': sTrig,
#        'digitizerTrig': dTrig,
#        'M-q1': m,
#        'M-q1-gate': Mq1gate
#    }
#    ChannelLibrary.channelLib.build_connectivity_graph()

    # Use stub Qubits, but comment this out when running directly.
    q1 = QubitFactory("q1")

    print("Run InversionRecovery")
    InversionRecovery(q1,  np.linspace(0, 5e-6, 11))
    print("Run Ramsey")
    Ramsey(q1, np.linspace(0, 5e-6, 11))

if __name__ == "__main__":
    main()
