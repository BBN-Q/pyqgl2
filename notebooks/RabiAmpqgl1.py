def RabiAmp():
    from QGL import QubitFactory
    from QGL.PulsePrimitives import MEAS
    from QGL.PulsePrimitives import Utheta
    from qgl2.qgl1_util import init_real as init

    QBIT_1 = QubitFactory('q1')
    from pyqgl2.eval import EvalTransformer
    _v = EvalTransformer.PRECOMPUTED_VALUES
    seq = [
        init(QBIT_1),
        Utheta(QBIT_1, amp=0.0, phase=0),
        MEAS(QBIT_1)
    ]
    return seq
