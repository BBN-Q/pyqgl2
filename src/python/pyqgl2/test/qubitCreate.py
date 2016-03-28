# Tests of how to create Qubits and use them

from qgl2.qgl1 import Qubit, Id
from qgl2.qgl2 import qbit, qgl2main, qgl2decl

LABEL = "mylabel"

@qgl2decl
def makeQ(label) -> qbit:
    m = Qubit("label")
    return m

@qgl2main
def main(myarg):
    # Qubit should take only 2 arguments without a name. More is an error.
    # Qubit also requires a string arg - variables are no good
    # So this fails
#    q = Qubit(myarg)
    # This should fail, but doesn't
    q = Qubit('mylabel', 1, 2)
    Id(q)
    # This next I'd love to support, but it fails
#    Id(makeQ("2"))
    # The Qubit call must be  atop level call, so this next one fails as well
#    Id(Qubit("3"))

    # This one works
    # but ONLY if the variable name is different than above
    r = Qubit('q1')
    Id(r)

    # These should work
    s = Qubit(label="qs")
    Id(s)
    t = Qubit("qt", 1)
    Id(t)
    s2 = Qubit("qs2")
    Id(s2)

    # You can't have a positional arg and a label kw arg
    # So this should fail
#    u = Qubit("qu", label="qu-label")
