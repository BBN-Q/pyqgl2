
import qconcur

def test_loops(a:qbit, b:qbit):

    x = Qbit(1)
    x = r
    v1 = MEAS(d)

    with concur:
        while True:
            v1 = MEAS(d)
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



