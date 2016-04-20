# Pull in the symbols that QGL2 uses to embellish the
# Python3 syntax.  This must be done in every Python
# file that uses any of these symbols.
#
from qgl2.qgl2 import concur, qgl2decl, qgl2main
from qgl2.qgl2 import classical, pulse, qbit, qbit_list
from qgl2.qgl1 import QubitFactory, X90, Y90, MEAS

@qgl2decl
def test_loops(a:qbit, b:qbit):

    x = QubitFactory("1")
    # Next line causes an error - qbit reassignment
    x = r
    # Next line is also an error - no d defined
    v1 = MEAS(d)

    with concur:
        while True:
            v1 = MEAS(d)
            # There's no qbit1 - another error
            X90(qbit1)
            if v1:
                break

        while True:
            v2 = MEAS(b)
            Y90(qbit2)
            if v2:
                break

    with concur:
        print('fred')



