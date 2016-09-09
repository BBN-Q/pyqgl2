def main(**kwargs):
    from QGL.ChannelLibrary import QubitFactory
    from QGL.PulsePrimitives import X90

    if 'QBIT_q1' in kwargs:
        QBIT_q1 = kwargs['QBIT_q1']
    else:
        QBIT_q1 = QubitFactory('q1')
    QBIT_q1 = QBIT_q1
    from pyqgl2.eval import EvalTransformer
    _v = EvalTransformer.PRECOMPUTED_VALUES
    seqs = list()
    seq_QBIT_q1 = [
        Barrier('seq_0_1', [QBIT_q1]),
        Barrier('seq_0_3', [QBIT_q1]),
        X90(QBIT_q1),
        Barrier('eseq_1_3', [QBIT_q1]),
        Barrier('seq_0_4', [QBIT_q1]),
        X90(QBIT_q1),
        Barrier('eseq_1_4', [QBIT_q1]),
        Barrier('eseq_1_1', [QBIT_q1])
    ]
    seqs += [seq_QBIT_q1]
    return seqs
