
from qgl2.qgl2 import concur, seq
from qgl2.qgl2 import qgl2decl, qgl2main
from qgl2.qgl2 import classical, pulse, qbit, qbit_list
from qgl2.qgl1 import Qubit

# Note that for this next import to work you must run from the directory containing this file
import t1

from t2 import second_level as fred

@qgl2main
def main():

    a = Qubit("1")
    b = Qubit("2")
    c = Qubit("3")

    with concur:
        t1.t1(a, b)
        t1.t1(b, c)
        t1.t1(c, a)

# After exapansion, the with concur becomes 2 with seq blocks using overlapping qbits
# and that gives an error
