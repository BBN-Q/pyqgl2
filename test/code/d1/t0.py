
from qgl2.qgl2 import concur, seq
from qgl2.qgl2 import qgl2decl, qgl2main
from qgl2.qgl2 import classical, pulse, qreg
from qgl2.qgl1 import QubitFactory

# Note that for this next import to work you must run from the directory containing this file
import t1

from t2 import second_level as fred

@qgl2main
def main():

    a = QubitFactory("1")
    b = QubitFactory("2")
    c = QubitFactory("3")

    with concur:
        t1.t1(a, b)
        t1.t1(b, c)
        t1.t1(c, a)

# After exapansion, the with concur becomes 2 with seq blocks using overlapping qbits
# and that gives an error
