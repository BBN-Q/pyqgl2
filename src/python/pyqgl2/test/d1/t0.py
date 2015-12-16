
from qgl2.qgl2 import concur, seq
from qgl2.qgl2 import qgl2decl, qgl2main
from qgl2.qgl2 import classical, pulse, qbit, qbit_list
from qgl2.qgl2 import Qbit

import t1

from t2 import second_level as fred

@qgl2main
def main():

    a = Qbit(1)
    b = Qbit(2)
    c = Qbit(3)

    with concur:
        t1.t1(a, b)
        t1.t1(b, c)
        t1.t1(c, a)
