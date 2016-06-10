from pyqgl2.main import compileFunction, qgl2_compile_to_hardware
from pyqgl2.ast_util import NodeError
from pyqgl2.debugmsg import DebugMsg
import QGL


code = """
from qgl2.qgl2 import qgl2decl, sequence, concur
from qgl2.util import init
from qgl2.qgl1 import Y, QubitFactory, Id, X, MEAS, Y
@qgl2main
def myTest() -> sequence:
    q1 = QubitFactory('q1')
    q2 = QubitFactory('q2')
    q3 = QubitFactory('q3')
    with concur:
        for q in [q1, q2]:
            init(q)
            Id(q)
            X(q)
            MEAS(q)
    with concur:
        for q in [q1, q3]:
            Y(q)
"""
if __name__ == '__main__':
    NodeError.MUTE_ERR_LEVEL = NodeError.NODE_ERROR_NONE

    DebugMsg.set_level(0)
    resFunction = compileFunction(code, None, saveOutput=True,
                                  intermediate_output="myinter")
    if resFunction:
        # Now import the QGL1 things we need 
        from QGL.PulseSequencePlotter import plot_pulse_files
        from QGL.ChannelLibrary import QubitFactory
        import os

        # Create a directory for saving the results
        QGL.config.AWGDir = os.path.abspath(QGL.config.AWGDir + os.path.sep + "qgl2main")
        if not os.path.isdir(QGL.config.AWGDir):
            os.makedirs(QGL.config.AWGDir)

        # Now execute the returned function, which should produce a list of sequences
        sequences = resFunction(q=QubitFactory('q1'))

#        # Get length
#        from pyqgl2.pulselength import pulseLengths
#        length = pulseLengths(sequences)
#        print("Sequence length: %s" % length)

        # In verbose mode, turn on DEBUG python logging for the QGL Compiler
        if False:
            import logging
            from QGL.Compiler import set_log_level
            # Note this acts on QGL.Compiler at DEBUG by default
            # Could specify other levels, loggers
            set_log_level()

        # Now we have a QGL1 list of sequences we can act on
        fileNames = qgl2_compile_to_hardware(sequences, 'test/test',
                                             '')
        print(fileNames)
        if False:
            plot_pulse_files(fileNames)
    else:
        # Didn't produce a function
        pass
    
