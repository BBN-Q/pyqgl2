# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit, qbit_list

from QGL.PulsePrimitives import Id, X, Y, X90, Y90, MEAS
from QGL.Compiler import compile_to_hardware
from QGL.PulseSequencePlotter import plot_pulse_files

@qgl2decl
def AllXY(q: qbit, showPlot = False):
    # firstPulses: 21 of them
    firstPulses = [
        Id(q),
        X(q),
        Y(q),
        X(q),
        Y(q),
        X90(q),
        Y90(q),
        X90(q),
        Y90(q),
        X90(q),
        Y90(q),
        X(q),
        Y(q),
        X90(q),
        X(q),
        Y90(q),
        Y(q),
        X(q),
        Y(q),
        X90(q),
        Y90(q)]

    # secondPulses: 21 of them
    secondPulses = [
        Id(q),
        X(q),
        Y(q),
        Y(q),
        X(q),
        Id(q),
        Id(q),
        Y90(q),
        X90(q),
        Y(q),
        X(q),
        Y90(q),
        X90(q),
        X(q),
        X90(q),
        Y(q),
        Y90(q),
        Id(q),
        Id(q),
        X90(q),
        Y90(q)]

    # Here we merge the lists together manually first, to be more clear / explicit
    firstAndSecondPulses = [
        # these produce the state |0>
        [ Id(q),  Id(q)], # no pulses
        [ X(q),   X(q)], # pulsing around the same axis
        [ Y(q),   Y(q)],
        [ X(q),   Y(q)], # pulsing around orthogonal axes
        [ Y(q),   X(q)],
        # these next create a |+> or |i> state (equal superposition of |0> + |1>)
        [ X90(q), Id(q)], # single pulses
        [ Y90(q), Id(q)],
        [ X90(q), Y90(q)], # pulse pairs around orthogonal axes with 1e error sensitivity
        [ Y90(q), X90(q)],
        [ X90(q), Y(q)], # pulse pairs with 2e error sensitivity
        [ Y90(q), X(q)],
        [ X(q),   Y90(q)],
        [ Y(q),   X90(q)],
        [ X90(q), X(q)], # pulse pairs around common axis with 3e error sensitivity
        [ X(q),   X90(q)],
        [ Y90(q), Y(q)],
        [ Y(q),   Y90(q)],
        # these next create the |1> state
        [ X(q),   Id(q)], # single pulses
        [ Y(q),   Id(q)],
        [ X90(q), X90(q)], # pulse pairs
        [ Y90(q), Y90(q)]
    ]

    # If the goal were simply all permutations, then we could compute all the permutations of our pulses.
    # However, the order is special to allow eyeballing errors. See comments above.

    # Any of these produces what we want:
    #   [[f0,s0, M], [f0, s0, M], [f1, s1, M], [f1, s1, M], ....., [f20, s20, M], [f20, S20, M]]
    # 1:
    # seqs = [[firstPulses[ind], secondPulses[ind], MEAS(q)] for ind in range(len(firstPulses)) for i in range(2)]

    # 2:
    # seqs = []
    # for ind in range(len(firstPulses)):
    #     seqs += [[firstPulses[ind], secondPulses[ind], MEAS(q)] for i in range(2)]

    # 3: (This one uses the pre interpolated lists)
    seqs = [firstAndSecondPulses[ind] + [MEAS(q)] for ind in range(len(firstAndSecondPulses)) for i in range(2)]

    def addMeasPulse(listOfSequencesOn1Qubit, q: qbit):
        return [listOfSequencesOn1Qubit[ind] + [MEAS(q)] for ind in range(len(listOfSequencesOn1Qubit))]
    # Elsewhere code does this:
    # # Add the measurement to all sequences
    # for seq in seqsBis:
    #     seq.append(functools.reduce(operator.mul, [MEAS(q) for q in qubits]))

    def repeatSequences(listOfSequences, repeat=2):
        return [listOfSequences[ind] for ind in range(len(listOfSequences)) for i in range(repeat)]

    def compileAndPlot(listOfSequences, filePrefix, showPlot=False):
        fileNames = compile_to_hardware(listOfSequences, filePrefix)
        print(fileNames)

        if showPlot:
            plot_pulse_files(fileNames)

    # FIXME: Should that be a tuple or explicitly 1 qbit or 2?
    def addCalibration(listOfSequences, tupleOfQubits: qbit_list, numRepeats=2):
	# Tack on the calibration sequences
        listOfSequences += create_cal_seqs((tupleOfQubits), numRepeats)
        return listOfSequences
                
    # 4: Using helpers
    # FIXME: This seems to give to more unit test failures
    # seqs = repeatSequences(addMeasPulse(firstAndSecondPulses, q))

    # Boilerplate / unmodified
    filenames = compile_to_hardware(seqs, 'AllXY/AllXY')
    print(filenames)
    
    if showPlot:
        plot_pulse_files(filenames)
#    raise NotImplementedError("Not implemented")
