# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit, qgl2main

from QGL.PulsePrimitives import X90, Id, Y, U90, MEAS
from QGL.Compiler import compile_to_hardware
from QGL.PulseSequencePlotter import plot_pulse_files
from qgl2.basic_sequences.helpers import create_cal_seqs
from qgl2.basic_sequences.new_helpers import addCalibration, compileAndPlot
from qgl2.util import init

from math import pi

@qgl2decl
def HahnEcho(qubit: qbit, pulseSpacings, periods = 0, calRepeats=2, showPlot=False):
    """
    A single pulse Hahn echo with variable phase of second pi/2 pulse. 

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    pulseSpacings : pulse spacings to sweep over; the t in 90-t-180-t-180 (iterable)
    periods: number of artificial oscillations
    calRepeats : how many times to repeat calibration scalings (default 2)
    showPlot : whether to plot (boolean)
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

    # FIXME: QGL2 doesn't understand this for loop yet

    for k in range(len(pulseSpacings)):
        init(qubit)
        X90(qubit)
        Id(qubit, pulseSpacings[k])
        Y(qubit)
        Id(qubit, pulseSpacings[k])
        U90(qubit, phase=2*pi*periods/len(pulseSpacings)*k)
        MEAS(qubit)

    create_cal_seqs((qubit,), calRepeats)

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    compileAndPlot('Echo/Echo', showPlot)

def HahnEchoq1(qubit: qbit, pulseSpacings, periods = 0, calRepeats=2, showPlot=False):
    """
    A single pulse Hahn echo with variable phase of second pi/2 pulse. 

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    pulseSpacings : pulse spacings to sweep over; the t in 90-t-180-t-180 (iterable)
    periods: number of artificial oscillations
    calRepeats : how many times to repeat calibration scalings (default 2)
    showPlot : whether to plot (boolean)
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

    seqs = []
    for k in range(len(pulseSpacings)):
        idpulse = Id(qubit, pulseSpacings[k])
        seqs.append([
            X90(qubit),
            idpulse,
            Y(qubit),
            idpulse,
            U90(qubit, phase=2*pi*periods/len(pulseSpacings)*k),
            MEAS(qubit)
        ])
    seqs = addCalibration(seqs, (qubit,), calRepeats)

    # Be sure to un-decorate this function to make it work without the
    # QGL2 compiler
    compileAndPlot(seqs, 'Echo/Echo', showPlot)

@qgl2decl
def CPMG(qubit: qbit, numPulses, pulseSpacing, calRepeats=2, showPlot=False):
    """
    CPMG pulse train with fixed pulse spacing. Note this pulse spacing is centre to centre,
    i.e. it accounts for the pulse width

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    numPulses : number of 180 pulses; should be even (iterable)
    pulseSpacing : spacing between the 180's (seconds)
    calRepeats : how many times to repeat calibration scalings (default 2)
    showPlot : whether to plot (boolean)
    """

    # Original:
    # # First setup the t-180-t block
    # CPMGBlock = [Id(qubit, (pulseSpacing-qubit.pulseParams['length'])/2),
    #              Y(qubit), Id(qubit, (pulseSpacing-qubit.pulseParams['length'])/2)]

    # seqs = [[X90(qubit)] + CPMGBlock*rep + [X90(qubit), MEAS(qubit)] for rep in numPulses]

    # # Tack on the calibration scalings
    # seqs += create_cal_seqs((qubit,), calRepeats)

    # fileNames = compile_to_hardware(seqs, 'CPMG/CPMG')
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)

    @qgl2decl
    def idPulse(qubit: qbit):
        Id(qubit, (pulseSpacing - qubit.pulseParams['length'])/2)

    # FIXME: QGL2 doesn't understand these for loops yet

    # Create numPulses sequences
    for rep in numPulses:
        init(qubit)
        X90(qubit)
        # Repeat the t-180-t block rep times
        for _ in range(rep):
            idPulse(qubit)
            Y(qubit)
            idPulse(qubit)
        X90(qubit)
        MEAS(qubit)

    # Tack on calibration
    create_cal_seqs((qubit,), calRepeats)

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    compileAndPlot('CPMG/CPMG', showPlot)

def CPMGq1(qubit: qbit, numPulses, pulseSpacing, calRepeats=2, showPlot=False):
    """
    CPMG pulse train with fixed pulse spacing. Note this pulse spacing is centre to centre,
    i.e. it accounts for the pulse width

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    numPulses : number of 180 pulses; should be even (iterable)
    pulseSpacing : spacing between the 180's (seconds)
    calRepeats : how many times to repeat calibration scalings (default 2)
    showPlot : whether to plot (boolean)
    """

    # Original:
    # # First setup the t-180-t block
    # CPMGBlock = [Id(qubit, (pulseSpacing-qubit.pulseParams['length'])/2),
    #              Y(qubit), Id(qubit, (pulseSpacing-qubit.pulseParams['length'])/2)]

    # seqs = [[X90(qubit)] + CPMGBlock*rep + [X90(qubit), MEAS(qubit)] for rep in numPulses]

    # # Tack on the calibration scalings
    # seqs += create_cal_seqs((qubit,), calRepeats)

    # fileNames = compile_to_hardware(seqs, 'CPMG/CPMG')
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)

    # First setup the t-180-t block
    idPulse = Id(qubit, (pulseSpacing - qubit.pulseParams['length'])/2)
    CPMGBlock = [
        idPulse,
        Y(qubit),
        idPulse
    ]

    seqs = []
    for rep in numPulses:
        seqs.append(
            [X90(qubit)] +
            CPMGBlock * rep +
            [X90(qubit), MEAS(qubit)]
        )

    # Tack on calibration
    seqs = addCalibration(seqs, (qubit,), calRepeats)

    # Be sure to un-decorate this function to make it work without the
    # QGL2 compiler
    compileAndPlot(seqs, 'CPMG/CPMG', showPlot)

# Imports for testing only
#from QGL.Channels import Qubit, LogicalMarkerChannel
from qgl2.qgl1 import Qubit, QubitFactory
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
    q1 = QubitFactory(label='q1')
#    q1.pulseParams['length'] = 30e-9
#    q1.pulseParams['phase'] = pi/2

    # But the current qgl2 compiler doesn't understand Qubits, only
    # Qbits. So use that instead when running through the QGL2
    # compiler, but comment this out when running directly.
#    q1 = Qbit(1)

    print("Run HahnEcho")
    HahnEcho(q1, np.linspace(0, 5e-6, 11))
    print("Run CPMG")
    CPMG(q1, 2*np.arange(4), 500e-9)

if __name__ == "__main__":
    main()
