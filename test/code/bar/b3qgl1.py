def main(**kwargs):
    from QGL.ChannelLibrary import QubitFactory
    from QGL.PulsePrimitives import X90
    from QGL.PulsePrimitives import Y90

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
        Barrier('seq_0_1', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('concur_beg_5', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('seq_0_3', [QBIT_q1, QBIT_q2]),
        X90(QBIT_q1),
        Barrier('seq_1_3', [QBIT_q1, QBIT_q2]),
        Barrier('eseq_2_3', [QBIT_q1, QBIT_q2]),
        Barrier('concur_end_5', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('eseq_1_1', [QBIT_q1, QBIT_q2, QBIT_q3])
    ]
    seqs += [seq_QBIT_q1]
    seq_QBIT_q2 = [
        Barrier('seq_0_1', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('concur_beg_5', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('seq_0_3', [QBIT_q1, QBIT_q2]),
        Barrier('seq_1_3', [QBIT_q1, QBIT_q2]),
        Y90(QBIT_q2),
        Barrier('eseq_2_3', [QBIT_q1, QBIT_q2]),
        Barrier('seq_0_4', [QBIT_q2, QBIT_q3]),
        X90(QBIT_q2),
        Barrier('seq_1_4', [QBIT_q2, QBIT_q3]),
        Barrier('eseq_2_4', [QBIT_q2, QBIT_q3]),
        Barrier('concur_end_5', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('eseq_1_1', [QBIT_q1, QBIT_q2, QBIT_q3])
    ]
    seqs += [seq_QBIT_q2]
    seq_QBIT_q3 = [
        Barrier('seq_0_1', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('concur_beg_5', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('seq_0_4', [QBIT_q2, QBIT_q3]),
        Barrier('seq_1_4', [QBIT_q2, QBIT_q3]),
        Y90(QBIT_q3),
        Barrier('eseq_2_4', [QBIT_q2, QBIT_q3]),
        Barrier('concur_end_5', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('eseq_1_1', [QBIT_q1, QBIT_q2, QBIT_q3])
    ]
    seqs += [seq_QBIT_q3]
    return seqs
