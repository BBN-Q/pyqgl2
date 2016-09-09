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
    QBIT_q1 = QBIT_q1
    QBIT_q2 = QBIT_q2
    from pyqgl2.eval import EvalTransformer
    _v = EvalTransformer.PRECOMPUTED_VALUES
    seqs = list()
    seq_QBIT_q1 = [
        Barrier('seq_0_1', [QBIT_q1, QBIT_q2]),
        X90(QBIT_q1),
        Barrier('seq_1_1', [QBIT_q1, QBIT_q2]),
        Barrier('eseq_2_1', [QBIT_q1, QBIT_q2])
    ]
    seqs += [seq_QBIT_q1]
    seq_QBIT_q2 = [
        Barrier('seq_0_1', [QBIT_q1, QBIT_q2]),
        Barrier('seq_1_1', [QBIT_q1, QBIT_q2]),
        Y90(QBIT_q2),
        Barrier('eseq_2_1', [QBIT_q1, QBIT_q2])
    ]
    seqs += [seq_QBIT_q2]
    return seqs
