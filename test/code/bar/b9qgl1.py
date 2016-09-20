def main(**kwargs):
    from QGL.ChannelLibrary import QubitFactory
    from QGL.ControlFlow import Sync
    from QGL.ControlFlow import Wait
    from QGL.PulsePrimitives import X90
    from qgl2.qgl1 import Barrier as Barrier

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
        Barrier('seq_0_2', [QBIT_q1]),
        Sync(),
        Barrier('seq_1_2', [QBIT_q1]),
        Wait(),
        Barrier('eseq_2_2', [QBIT_q1]),
        Barrier('seq_1_1', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('seq_2_1', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('seq_0_4', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('seq_0_6', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('concur_beg_8', [QBIT_q1]),
        X90(QBIT_q1),
        Barrier('concur_end_8', [QBIT_q1]),
        Barrier('eseq_1_6', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('seq_0_9', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('eseq_1_9', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('seq_0_12', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('eseq_1_12', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('eseq_1_4', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('eseq_3_1', [QBIT_q1, QBIT_q2, QBIT_q3])
    ]
    seqs += [seq_QBIT_q1]
    seq_QBIT_q2 = [
        Barrier('seq_0_1', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('seq_1_1', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('seq_0_3', [QBIT_q2]),
        Sync(),
        Barrier('seq_1_3', [QBIT_q2]),
        Wait(),
        Barrier('eseq_2_3', [QBIT_q2]),
        Barrier('seq_2_1', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('seq_0_4', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('seq_0_6', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('eseq_1_6', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('seq_0_9', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('concur_beg_11', [QBIT_q2]),
        X90(QBIT_q2),
        Barrier('concur_end_11', [QBIT_q2]),
        Barrier('eseq_1_9', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('seq_0_12', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('eseq_1_12', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('eseq_1_4', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('eseq_3_1', [QBIT_q1, QBIT_q2, QBIT_q3])
    ]
    seqs += [seq_QBIT_q2]
    seq_QBIT_q3 = [
        Barrier('seq_0_1', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('seq_1_1', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('seq_2_1', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('seq_0_4', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('seq_0_6', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('eseq_1_6', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('seq_0_9', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('eseq_1_9', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('seq_0_12', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('concur_beg_14', [QBIT_q3]),
        X90(QBIT_q3),
        Barrier('concur_end_14', [QBIT_q3]),
        Barrier('eseq_1_12', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('eseq_1_4', [QBIT_q1, QBIT_q2, QBIT_q3]),
        Barrier('eseq_3_1', [QBIT_q1, QBIT_q2, QBIT_q3])
    ]
    seqs += [seq_QBIT_q3]
    return seqs
