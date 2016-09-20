def main(**kwargs):
    from QGL.BlockLabel import BlockLabel
    from QGL.ChannelLibrary import QubitFactory
    from QGL.ControlFlow import CmpEq
    from QGL.ControlFlow import Goto
    from QGL.PulsePrimitives import Xtheta

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
        Barrier('seq_0_5', [QBIT_q1]),
        CmpEq(1),
        Goto(BlockLabel('if_end_2')),
        Barrier('seq_0_6', [QBIT_q1]),
        Xtheta(QBIT_q1, i=1, j=2, k=0),
        Barrier('eseq_1_6', [QBIT_q1]),
        BlockLabel('if_end_2'),
        Barrier('eseq_1_5', [QBIT_q1]),
        Barrier('seq_0_7', [QBIT_q1]),
        CmpEq(1),
        Goto(BlockLabel('if_end_4')),
        Barrier('seq_0_8', [QBIT_q1]),
        Xtheta(QBIT_q1, i=1, j=2, k=1),
        Barrier('eseq_1_8', [QBIT_q1]),
        BlockLabel('if_end_4'),
        Barrier('eseq_1_7', [QBIT_q1]),
        Barrier('eseq_1_3', [QBIT_q1]),
        Barrier('seq_0_9', [QBIT_q1]),
        Barrier('seq_0_11', [QBIT_q1]),
        CmpEq(1),
        Goto(BlockLabel('if_end_8')),
        Barrier('seq_0_12', [QBIT_q1]),
        Xtheta(QBIT_q1, i=3, j=4, k=0),
        Barrier('eseq_1_12', [QBIT_q1]),
        BlockLabel('if_end_8'),
        Barrier('eseq_1_11', [QBIT_q1]),
        Barrier('seq_0_13', [QBIT_q1]),
        CmpEq(1),
        Goto(BlockLabel('if_end_10')),
        Barrier('seq_0_14', [QBIT_q1]),
        Xtheta(QBIT_q1, i=3, j=4, k=1),
        Barrier('eseq_1_14', [QBIT_q1]),
        BlockLabel('if_end_10'),
        Barrier('eseq_1_13', [QBIT_q1]),
        Barrier('seq_0_15', [QBIT_q1]),
        CmpEq(1),
        Goto(BlockLabel('if_end_12')),
        Barrier('seq_0_16', [QBIT_q1]),
        Xtheta(QBIT_q1, i=3, j=4, k=2),
        Barrier('eseq_1_16', [QBIT_q1]),
        BlockLabel('if_end_12'),
        Barrier('eseq_1_15', [QBIT_q1]),
        Barrier('seq_0_17', [QBIT_q1]),
        CmpEq(1),
        Goto(BlockLabel('if_end_14')),
        Barrier('seq_0_18', [QBIT_q1]),
        Xtheta(QBIT_q1, i=3, j=4, k=3),
        Barrier('eseq_1_18', [QBIT_q1]),
        BlockLabel('if_end_14'),
        Barrier('eseq_1_17', [QBIT_q1]),
        Barrier('eseq_1_9', [QBIT_q1]),
        Barrier('eseq_1_1', [QBIT_q1])
    ]
    seqs += [seq_QBIT_q1]
    return seqs
