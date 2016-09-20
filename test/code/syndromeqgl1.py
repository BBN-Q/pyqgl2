def main(**kwargs):
    from QGL.ChannelLibrary import QubitFactory
    from QGL.PulsePrimitives import X
    from QGL.PulsePrimitives import Y
    from QGL.PulsePrimitives import Z
    from qgl2.qgl1control import Barrier as Barrier

    if 'QBIT_0' in kwargs:
        QBIT_0 = kwargs['QBIT_0']
    else:
        QBIT_0 = QubitFactory('0')
    if 'QBIT_1' in kwargs:
        QBIT_1 = kwargs['QBIT_1']
    else:
        QBIT_1 = QubitFactory('1')
    if 'QBIT_2' in kwargs:
        QBIT_2 = kwargs['QBIT_2']
    else:
        QBIT_2 = QubitFactory('2')
    if 'QBIT_3' in kwargs:
        QBIT_3 = kwargs['QBIT_3']
    else:
        QBIT_3 = QubitFactory('3')
    if 'QBIT_4' in kwargs:
        QBIT_4 = kwargs['QBIT_4']
    else:
        QBIT_4 = QubitFactory('4')
    if 'QBIT_5' in kwargs:
        QBIT_5 = kwargs['QBIT_5']
    else:
        QBIT_5 = QubitFactory('5')
    if 'QBIT_6' in kwargs:
        QBIT_6 = kwargs['QBIT_6']
    else:
        QBIT_6 = QubitFactory('6')
    if 'QBIT_7' in kwargs:
        QBIT_7 = kwargs['QBIT_7']
    else:
        QBIT_7 = QubitFactory('7')
    if 'QBIT_8' in kwargs:
        QBIT_8 = kwargs['QBIT_8']
    else:
        QBIT_8 = QubitFactory('8')
    QBIT_0 = QBIT_0
    QBIT_1 = QBIT_1
    QBIT_2 = QBIT_2
    QBIT_3 = QBIT_3
    QBIT_4 = QBIT_4
    QBIT_5 = QBIT_5
    QBIT_6 = QBIT_6
    QBIT_7 = QBIT_7
    QBIT_8 = QBIT_8
    from pyqgl2.eval import EvalTransformer
    _v = EvalTransformer.PRECOMPUTED_VALUES
    seqs = list()
    seq_QBIT_0 = [
        Barrier('group_marker_82', [QBIT_0]),
        Barrier('seq_0_1', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_1_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_11', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_26', [QBIT_0, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_7]),
        Barrier('seq_0_15', [QBIT_0, QBIT_3]),
        Barrier('concur_beg_17', [QBIT_0, QBIT_3]),
        X(qubit=QBIT_0),
        Barrier('concur_end_17', [QBIT_0, QBIT_3]),
        Barrier('eseq_1_15', [QBIT_0, QBIT_3]),
        Barrier('concur_end_26', [QBIT_0, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_7]),
        Barrier('eseq_1_11', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_27', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_42', [QBIT_0, QBIT_1, QBIT_4, QBIT_5, QBIT_6, QBIT_7]),
        Barrier('seq_0_31', [QBIT_0, QBIT_1]),
        Barrier('concur_beg_33', [QBIT_0, QBIT_1]),
        Y(qubit=QBIT_0),
        Barrier('concur_end_33', [QBIT_0, QBIT_1]),
        Barrier('eseq_1_31', [QBIT_0, QBIT_1]),
        Barrier('concur_end_42', [QBIT_0, QBIT_1, QBIT_4, QBIT_5, QBIT_6, QBIT_7]),
        Barrier('eseq_1_27', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_43', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_1_43', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_59', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_1_59', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_2_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_3_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_1_1', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8])
    ]
    seqs += [seq_QBIT_0]
    seq_QBIT_1 = [
        Barrier('group_marker_83', [QBIT_1]),
        Barrier('seq_0_1', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_9', [QBIT_1, QBIT_7]),
        Barrier('seq_0_6', [QBIT_1]),
        Z(qubit=QBIT_1),
        Barrier('eseq_1_6', [QBIT_1]),
        Barrier('concur_end_9', [QBIT_1, QBIT_7]),
        Barrier('seq_1_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_11', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_1_11', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_27', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_42', [QBIT_0, QBIT_1, QBIT_4, QBIT_5, QBIT_6, QBIT_7]),
        Barrier('seq_0_31', [QBIT_0, QBIT_1]),
        Barrier('concur_beg_33', [QBIT_0, QBIT_1]),
        X(qubit=QBIT_1),
        Barrier('concur_end_33', [QBIT_0, QBIT_1]),
        Barrier('eseq_1_31', [QBIT_0, QBIT_1]),
        Barrier('concur_end_42', [QBIT_0, QBIT_1, QBIT_4, QBIT_5, QBIT_6, QBIT_7]),
        Barrier('eseq_1_27', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_43', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_58', [QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_7, QBIT_8]),
        Barrier('seq_0_47', [QBIT_1, QBIT_2]),
        Barrier('concur_beg_49', [QBIT_1, QBIT_2]),
        X(qubit=QBIT_1),
        Barrier('concur_end_49', [QBIT_1, QBIT_2]),
        Barrier('eseq_1_47', [QBIT_1, QBIT_2]),
        Barrier('concur_end_58', [QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_7, QBIT_8]),
        Barrier('eseq_1_43', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_59', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_74', [QBIT_1, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_8]),
        Barrier('seq_0_63', [QBIT_1, QBIT_4]),
        Barrier('concur_beg_65', [QBIT_1, QBIT_4]),
        X(qubit=QBIT_1),
        Barrier('concur_end_65', [QBIT_1, QBIT_4]),
        Barrier('eseq_1_63', [QBIT_1, QBIT_4]),
        Barrier('concur_end_74', [QBIT_1, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_8]),
        Barrier('eseq_1_59', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_2_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_81', [QBIT_1, QBIT_7]),
        Barrier('seq_0_78', [QBIT_1]),
        Z(qubit=QBIT_1),
        Barrier('eseq_1_78', [QBIT_1]),
        Barrier('concur_end_81', [QBIT_1, QBIT_7]),
        Barrier('eseq_3_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_1_1', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8])
    ]
    seqs += [seq_QBIT_1]
    seq_QBIT_2 = [
        Barrier('group_marker_84', [QBIT_2]),
        Barrier('seq_0_1', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_1_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_11', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_26', [QBIT_0, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_7]),
        Barrier('seq_0_19', [QBIT_2, QBIT_5]),
        Barrier('concur_beg_21', [QBIT_2, QBIT_5]),
        X(qubit=QBIT_2),
        Barrier('concur_end_21', [QBIT_2, QBIT_5]),
        Barrier('eseq_1_19', [QBIT_2, QBIT_5]),
        Barrier('concur_end_26', [QBIT_0, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_7]),
        Barrier('eseq_1_11', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_27', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_1_27', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_43', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_58', [QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_7, QBIT_8]),
        Barrier('seq_0_47', [QBIT_1, QBIT_2]),
        Barrier('concur_beg_49', [QBIT_1, QBIT_2]),
        Y(qubit=QBIT_2),
        Barrier('concur_end_49', [QBIT_1, QBIT_2]),
        Barrier('eseq_1_47', [QBIT_1, QBIT_2]),
        Barrier('concur_end_58', [QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_7, QBIT_8]),
        Barrier('eseq_1_43', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_59', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_1_59', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_2_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_3_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_1_1', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8])
    ]
    seqs += [seq_QBIT_2]
    seq_QBIT_3 = [
        Barrier('group_marker_85', [QBIT_3]),
        Barrier('seq_0_1', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_1_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_11', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_26', [QBIT_0, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_7]),
        Barrier('seq_0_15', [QBIT_0, QBIT_3]),
        Barrier('concur_beg_17', [QBIT_0, QBIT_3]),
        Y(qubit=QBIT_3),
        Barrier('concur_end_17', [QBIT_0, QBIT_3]),
        Barrier('eseq_1_15', [QBIT_0, QBIT_3]),
        Barrier('concur_end_26', [QBIT_0, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_7]),
        Barrier('eseq_1_11', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_27', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_1_27', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_43', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_58', [QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_7, QBIT_8]),
        Barrier('seq_0_51', [QBIT_3, QBIT_4]),
        Barrier('concur_beg_53', [QBIT_3, QBIT_4]),
        Y(qubit=QBIT_3),
        Barrier('concur_end_53', [QBIT_3, QBIT_4]),
        Barrier('eseq_1_51', [QBIT_3, QBIT_4]),
        Barrier('concur_end_58', [QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_7, QBIT_8]),
        Barrier('eseq_1_43', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_59', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_74', [QBIT_1, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_8]),
        Barrier('seq_0_67', [QBIT_3, QBIT_6]),
        Barrier('concur_beg_69', [QBIT_3, QBIT_6]),
        Y(qubit=QBIT_3),
        Barrier('concur_end_69', [QBIT_3, QBIT_6]),
        Barrier('eseq_1_67', [QBIT_3, QBIT_6]),
        Barrier('concur_end_74', [QBIT_1, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_8]),
        Barrier('eseq_1_59', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_2_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_3_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_1_1', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8])
    ]
    seqs += [seq_QBIT_3]
    seq_QBIT_4 = [
        Barrier('group_marker_86', [QBIT_4]),
        Barrier('seq_0_1', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_1_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_11', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_26', [QBIT_0, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_7]),
        Barrier('seq_0_23', [QBIT_4, QBIT_7]),
        Barrier('concur_beg_25', [QBIT_4, QBIT_7]),
        Y(qubit=QBIT_4),
        Barrier('concur_end_25', [QBIT_4, QBIT_7]),
        Barrier('eseq_1_23', [QBIT_4, QBIT_7]),
        Barrier('concur_end_26', [QBIT_0, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_7]),
        Barrier('eseq_1_11', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_27', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_42', [QBIT_0, QBIT_1, QBIT_4, QBIT_5, QBIT_6, QBIT_7]),
        Barrier('seq_0_35', [QBIT_4, QBIT_5]),
        Barrier('concur_beg_37', [QBIT_4, QBIT_5]),
        X(qubit=QBIT_4),
        Barrier('concur_end_37', [QBIT_4, QBIT_5]),
        Barrier('eseq_1_35', [QBIT_4, QBIT_5]),
        Barrier('concur_end_42', [QBIT_0, QBIT_1, QBIT_4, QBIT_5, QBIT_6, QBIT_7]),
        Barrier('eseq_1_27', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_43', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_58', [QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_7, QBIT_8]),
        Barrier('seq_0_51', [QBIT_3, QBIT_4]),
        Barrier('concur_beg_53', [QBIT_3, QBIT_4]),
        X(qubit=QBIT_4),
        Barrier('concur_end_53', [QBIT_3, QBIT_4]),
        Barrier('eseq_1_51', [QBIT_3, QBIT_4]),
        Barrier('concur_end_58', [QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_7, QBIT_8]),
        Barrier('eseq_1_43', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_59', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_74', [QBIT_1, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_8]),
        Barrier('seq_0_63', [QBIT_1, QBIT_4]),
        Barrier('concur_beg_65', [QBIT_1, QBIT_4]),
        Y(qubit=QBIT_4),
        Barrier('concur_end_65', [QBIT_1, QBIT_4]),
        Barrier('eseq_1_63', [QBIT_1, QBIT_4]),
        Barrier('concur_end_74', [QBIT_1, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_8]),
        Barrier('eseq_1_59', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_2_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_3_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_1_1', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8])
    ]
    seqs += [seq_QBIT_4]
    seq_QBIT_5 = [
        Barrier('group_marker_87', [QBIT_5]),
        Barrier('seq_0_1', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_1_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_11', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_26', [QBIT_0, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_7]),
        Barrier('seq_0_19', [QBIT_2, QBIT_5]),
        Barrier('concur_beg_21', [QBIT_2, QBIT_5]),
        Y(qubit=QBIT_5),
        Barrier('concur_end_21', [QBIT_2, QBIT_5]),
        Barrier('eseq_1_19', [QBIT_2, QBIT_5]),
        Barrier('concur_end_26', [QBIT_0, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_7]),
        Barrier('eseq_1_11', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_27', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_42', [QBIT_0, QBIT_1, QBIT_4, QBIT_5, QBIT_6, QBIT_7]),
        Barrier('seq_0_35', [QBIT_4, QBIT_5]),
        Barrier('concur_beg_37', [QBIT_4, QBIT_5]),
        Y(qubit=QBIT_5),
        Barrier('concur_end_37', [QBIT_4, QBIT_5]),
        Barrier('eseq_1_35', [QBIT_4, QBIT_5]),
        Barrier('concur_end_42', [QBIT_0, QBIT_1, QBIT_4, QBIT_5, QBIT_6, QBIT_7]),
        Barrier('eseq_1_27', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_43', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_1_43', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_59', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_74', [QBIT_1, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_8]),
        Barrier('seq_0_71', [QBIT_5, QBIT_8]),
        Barrier('concur_beg_73', [QBIT_5, QBIT_8]),
        Y(qubit=QBIT_5),
        Barrier('concur_end_73', [QBIT_5, QBIT_8]),
        Barrier('eseq_1_71', [QBIT_5, QBIT_8]),
        Barrier('concur_end_74', [QBIT_1, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_8]),
        Barrier('eseq_1_59', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_2_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_3_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_1_1', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8])
    ]
    seqs += [seq_QBIT_5]
    seq_QBIT_6 = [
        Barrier('group_marker_88', [QBIT_6]),
        Barrier('seq_0_1', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_1_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_11', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_1_11', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_27', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_42', [QBIT_0, QBIT_1, QBIT_4, QBIT_5, QBIT_6, QBIT_7]),
        Barrier('seq_0_39', [QBIT_6, QBIT_7]),
        Barrier('concur_beg_41', [QBIT_6, QBIT_7]),
        Y(qubit=QBIT_6),
        Barrier('concur_end_41', [QBIT_6, QBIT_7]),
        Barrier('eseq_1_39', [QBIT_6, QBIT_7]),
        Barrier('concur_end_42', [QBIT_0, QBIT_1, QBIT_4, QBIT_5, QBIT_6, QBIT_7]),
        Barrier('eseq_1_27', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_43', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_1_43', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_59', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_74', [QBIT_1, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_8]),
        Barrier('seq_0_67', [QBIT_3, QBIT_6]),
        Barrier('concur_beg_69', [QBIT_3, QBIT_6]),
        X(qubit=QBIT_6),
        Barrier('concur_end_69', [QBIT_3, QBIT_6]),
        Barrier('eseq_1_67', [QBIT_3, QBIT_6]),
        Barrier('concur_end_74', [QBIT_1, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_8]),
        Barrier('eseq_1_59', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_2_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_3_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_1_1', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8])
    ]
    seqs += [seq_QBIT_6]
    seq_QBIT_7 = [
        Barrier('group_marker_89', [QBIT_7]),
        Barrier('seq_0_1', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_9', [QBIT_1, QBIT_7]),
        Barrier('seq_0_8', [QBIT_7]),
        Z(qubit=QBIT_7),
        Barrier('eseq_1_8', [QBIT_7]),
        Barrier('concur_end_9', [QBIT_1, QBIT_7]),
        Barrier('seq_1_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_11', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_26', [QBIT_0, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_7]),
        Barrier('seq_0_23', [QBIT_4, QBIT_7]),
        Barrier('concur_beg_25', [QBIT_4, QBIT_7]),
        X(qubit=QBIT_7),
        Barrier('concur_end_25', [QBIT_4, QBIT_7]),
        Barrier('eseq_1_23', [QBIT_4, QBIT_7]),
        Barrier('concur_end_26', [QBIT_0, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_7]),
        Barrier('eseq_1_11', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_27', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_42', [QBIT_0, QBIT_1, QBIT_4, QBIT_5, QBIT_6, QBIT_7]),
        Barrier('seq_0_39', [QBIT_6, QBIT_7]),
        Barrier('concur_beg_41', [QBIT_6, QBIT_7]),
        X(qubit=QBIT_7),
        Barrier('concur_end_41', [QBIT_6, QBIT_7]),
        Barrier('eseq_1_39', [QBIT_6, QBIT_7]),
        Barrier('concur_end_42', [QBIT_0, QBIT_1, QBIT_4, QBIT_5, QBIT_6, QBIT_7]),
        Barrier('eseq_1_27', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_43', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_58', [QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_7, QBIT_8]),
        Barrier('seq_0_55', [QBIT_7, QBIT_8]),
        Barrier('concur_beg_57', [QBIT_7, QBIT_8]),
        X(qubit=QBIT_7),
        Barrier('concur_end_57', [QBIT_7, QBIT_8]),
        Barrier('eseq_1_55', [QBIT_7, QBIT_8]),
        Barrier('concur_end_58', [QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_7, QBIT_8]),
        Barrier('eseq_1_43', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_59', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_1_59', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_2_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_81', [QBIT_1, QBIT_7]),
        Barrier('seq_0_80', [QBIT_7]),
        Z(qubit=QBIT_7),
        Barrier('eseq_1_80', [QBIT_7]),
        Barrier('concur_end_81', [QBIT_1, QBIT_7]),
        Barrier('eseq_3_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_1_1', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8])
    ]
    seqs += [seq_QBIT_7]
    seq_QBIT_8 = [
        Barrier('group_marker_90', [QBIT_8]),
        Barrier('seq_0_1', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_1_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_11', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_1_11', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_27', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_1_27', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_43', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_58', [QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_7, QBIT_8]),
        Barrier('seq_0_55', [QBIT_7, QBIT_8]),
        Barrier('concur_beg_57', [QBIT_7, QBIT_8]),
        Y(qubit=QBIT_8),
        Barrier('concur_end_57', [QBIT_7, QBIT_8]),
        Barrier('eseq_1_55', [QBIT_7, QBIT_8]),
        Barrier('concur_end_58', [QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_7, QBIT_8]),
        Barrier('eseq_1_43', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_0_59', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('concur_beg_74', [QBIT_1, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_8]),
        Barrier('seq_0_71', [QBIT_5, QBIT_8]),
        Barrier('concur_beg_73', [QBIT_5, QBIT_8]),
        X(qubit=QBIT_8),
        Barrier('concur_end_73', [QBIT_5, QBIT_8]),
        Barrier('eseq_1_71', [QBIT_5, QBIT_8]),
        Barrier('concur_end_74', [QBIT_1, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_8]),
        Barrier('eseq_1_59', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('seq_2_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_3_2', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8]),
        Barrier('eseq_1_1', [QBIT_0, QBIT_1, QBIT_2, QBIT_3, QBIT_4, QBIT_5, QBIT_6, QBIT_7, QBIT_8])
    ]
    seqs += [seq_QBIT_8]
    return seqs
