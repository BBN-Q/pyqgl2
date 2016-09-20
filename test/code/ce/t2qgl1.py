def main(**kwargs):
    from QGL.BlockLabel import BlockLabel
    from QGL.ChannelLibrary import QubitFactory
    from QGL.ControlFlow import CmpEq
    from QGL.ControlFlow import Goto
    from QGL.PulsePrimitives import X

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
        Barrier('concur_beg_5', [QBIT_q1, QBIT_q2]),
        BlockLabel('while_start_0'),
        CmpEq(1),
        Goto(BlockLabel('while_end_0')),
        X(QBIT_q1),
        Goto(BlockLabel('while_start_0')),
        BlockLabel('while_end_0'),
        Barrier('concur_end_5', [QBIT_q1, QBIT_q2]),
        Barrier('eseq_1_1', [QBIT_q1, QBIT_q2])
    ]
    seqs += [seq_QBIT_q1]
    seq_QBIT_q2 = [
        Barrier('seq_0_1', [QBIT_q1, QBIT_q2]),
        Barrier('concur_beg_5', [QBIT_q1, QBIT_q2]),
        BlockLabel('while_start_1'),
        CmpEq(1),
        Goto(BlockLabel('while_end_1')),
        X(QBIT_q2),
        Goto(BlockLabel('while_start_1')),
        BlockLabel('while_end_1'),
        Barrier('concur_end_5', [QBIT_q1, QBIT_q2]),
        Barrier('eseq_1_1', [QBIT_q1, QBIT_q2])
    ]
    seqs += [seq_QBIT_q2]
    return seqs
