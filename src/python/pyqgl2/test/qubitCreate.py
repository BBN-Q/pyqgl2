# Tests of how to create Qubits and use them

from qgl2.qgl1 import QubitFactory, Id
from qgl2.qgl2 import qbit, qgl2main, qgl2decl

LABEL = "mylabel"

@qgl2decl
def makeQ(label) -> qbit:
    m = QubitFactory("label")
    return m

@qgl2main
def main(myarg):
    # Qubit should take only 2 arguments without a name. More is an error.
    # Qubit also requires a string arg - variables are no good
    # So this fails
#    q = QubitFactory(myarg)
    # This should fail, but doesn't
    q = QubitFactory('mylabel', 1, 2)
    Id(q)
    # This next I'd love to support, but it fails
#    Id(makeQ("2"))
    # The Qubit call must be a top level call, so this next one fails as well
#    Id(QubitFactory("3"))

    # This one works
    # but ONLY if the variable name is different than above
    r = QubitFactory('q1')
    Id(r)

    # These should work
    s = QubitFactory(label="qs")
    Id(s)
    t = QubitFactory("qt", 1)
    Id(t)
    s2 = QubitFactory("qs2")
    Id(s2)
    s3 = Qubit(label="qs3")
    Id(s3)

    # You can't have a positional arg and a label kw arg
    # So this should fail
#    u = QubitFactory("qu", label="qu-label")
