def main(**kwargs):
    from QGL.ChannelLibrary import QubitFactory
    from QGL.ControlFlow import Sync
    from QGL.ControlFlow import Wait
    from QGL.PulsePrimitives import X90
    from QGL.PulsePrimitives import Y90

    if 'QBIT_1' in kwargs:
        QBIT_1 = kwargs['QBIT_1']
    else:
        QBIT_1 = QubitFactory('1')
    QBIT_1 = QBIT_1
    from pyqgl2.eval import EvalTransformer
    _v = EvalTransformer.PRECOMPUTED_VALUES
    seqs = list()
    seq = [
        Wait(),
        X90(QBIT_1),
        Y90(QBIT_1),
        X90(QBIT_1),
        Y90(QBIT_1),
        X90(QBIT_1),
        Y90(QBIT_1),
        X90(QBIT_1),
        Y90(QBIT_1),
        X90(QBIT_1),
        Y90(QBIT_1),
        X90(QBIT_1),
        Y90(QBIT_1),
        X90(QBIT_1),
        Y90(QBIT_1),
        X90(QBIT_1),
        Y90(QBIT_1),
        X90(QBIT_1),
        Y90(QBIT_1),
        X90(QBIT_1),
        Y90(QBIT_1),
        X90(QBIT_1),
        Y90(QBIT_1),
        X90(QBIT_1),
        Y90(QBIT_1),
        X90(QBIT_1),
        Y90(QBIT_1),
        X90(QBIT_1),
        Y90(QBIT_1),
        X90(QBIT_1),
        Y90(QBIT_1),
        X90(QBIT_1),
        Y90(QBIT_1),
        X90(QBIT_1),
        Y90(QBIT_1),
        X90(QBIT_1),
        Y90(QBIT_1),
        X90(QBIT_1),
        Y90(QBIT_1),
        X90(QBIT_1),
        Y90(QBIT_1),
        X90(QBIT_1),
        Y90(QBIT_1),
        X90(QBIT_1),
        Y90(QBIT_1),
        X90(QBIT_1),
        Y90(QBIT_1),
        X90(QBIT_1),
        Y90(QBIT_1),
        X90(QBIT_1),
        Y90(QBIT_1),
        X90(QBIT_1),
        Y90(QBIT_1),
        X90(QBIT_1),
        Y90(QBIT_1),
        Sync()
    ]
    seqs += [seq]
    return seqs
