def anotherMulti2(**kwargs):
    from QGL.ChannelLibrary import QubitFactory
    from QGL.PulsePrimitives import Id
    from QGL.PulsePrimitives import MEAS
    from QGL.PulsePrimitives import X
    from QGL.PulsePrimitives import Y
    from qgl2.qgl1control import Barrier as Barrier

    if 'QBIT_q1' in kwargs:
        QBIT_q1 = kwargs['QBIT_q1']
    else:
        QBIT_q1 = QubitFactory('q1')
    if 'QBIT_q2' in kwargs:
        QBIT_q2 = kwargs['QBIT_q2']
    else:
        QBIT_q2 = QubitFactory('q2')
    if 'QBIT_q3' in kwargs:
        QBIT_q3 = kwargs['QBIT_q3']
    else:
        QBIT_q3 = QubitFactory('q3')
    QBIT_q1 = QBIT_q1
    QBIT_q2 = QBIT_q2
    QBIT_q3 = QBIT_q3
    from pyqgl2.eval import EvalTransformer
    _v = EvalTransformer.PRECOMPUTED_VALUES
    seqs = list()
    seq_QBIT_q1 = [
        Barrier('group_marker_12', [QBIT_q1]),
        Barrier('seq_0_1', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('concur_beg_6', [QBIT_q1, QBIT_q2]),
        Id(channel=QBIT_q1),
        X(qubit=QBIT_q1),
        MEAS(q=QBIT_q1),
        Barrier('concur_end_6', [QBIT_q1, QBIT_q2]),
        Barrier('seq_1_1', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('concur_beg_11', [QBIT_q1, QBIT_q3]),
        Y(qubit=QBIT_q1),
        Barrier('concur_end_11', [QBIT_q1, QBIT_q3]),
        Barrier('eseq_2_1', [QBIT_q1, QBIT_q2, QBIT_q3])
    ]
    seqs += [seq_QBIT_q1]
    seq_QBIT_q2 = [
        Barrier('group_marker_13', [QBIT_q2]),
        Barrier('seq_0_1', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('concur_beg_6', [QBIT_q1, QBIT_q2]),
        Id(channel=QBIT_q2),
        X(qubit=QBIT_q2),
        MEAS(q=QBIT_q2),
        Barrier('concur_end_6', [QBIT_q1, QBIT_q2]),
        Barrier('seq_1_1', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('eseq_2_1', [QBIT_q1, QBIT_q2, QBIT_q3])
    ]
    seqs += [seq_QBIT_q2]
    seq_QBIT_q3 = [
        Barrier('group_marker_14', [QBIT_q3]),
        Barrier('seq_0_1', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('seq_1_1', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('concur_beg_11', [QBIT_q1, QBIT_q3]),
        Y(qubit=QBIT_q3),
        Barrier('concur_end_11', [QBIT_q1, QBIT_q3]),
        Barrier('eseq_2_1', [QBIT_q1, QBIT_q2, QBIT_q3])
    ]
    seqs += [seq_QBIT_q3]
    return seqs
