
from qgl2 import qtypes, concur

@qtypes('a', ('b', 2))
def test_loops(a, b):

    with concur():
        while True:
            v1 = MEAS(a)
            if v1:
                break
            X90(a, 1.0, 2.0)
            X90(a, 1.0, 2.0)

        while True:
            v2 = MEAS(b)
            if v2:
                break
            Y90(b)



