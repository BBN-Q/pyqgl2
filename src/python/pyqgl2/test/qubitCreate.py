# Unit Tests of how to create Qubits and use them

from qgl2.qgl1 import QubitFactory, Id, Qubit
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

    try:
        q = QubitFactory('mylabel', 1, 2)
        raise Exception("QubitFactory with 3 args should fail")
        Id(q)
    except:
        pass
    # This next I'd love to support, but it fails - QGL2 seems to silently ignore it
#    Id(makeQ("2"))

    # The Qubit call must be a top level call, so this next one fails as well
    # - QGL2 seems to silently ignore it
#    Id(QubitFactory("3"))

    # This one works
    # but ONLY if the variable name is different than above
    r = QubitFactory('q1')
    Id(r)

    # These should work, until QGL1 compiler notices the Qubit is unknown
    s = QubitFactory(label="qs")
    Id(s)
    try:
        t = QubitFactory("qt", 1)
        raise Exception("QubitFactory with 2 positional args should fail")
        Id(t)
    except:
        pass

    s2 = QubitFactory("qs2")
    Id(s2)

    s3 = Qubit(label="qs3")
    Id(s3)

    # You can't have a positional arg and a label kw arg
    # So this should fail
    # Expect error like:
# DEBUG-0: .../src/python/pyqgl2/find_labels.py:63 (getChanLabel) QubitFactory had a positional arg used as label='qu'. Cannot also have keyword argument label='qulabel'
# Traceback (most recent call last):
#   File "pyqgl2/main.py", line 661, in <module>
#     sequences = resFunction(q=QubitFactory('q1'))
#   File "<none>", line 26, in main
# TypeError: QubitFactory() got multiple values for argument 'label'
#    u = QubitFactory("qu", label="qulabel")

# Note also that a label with a hyphen in it as in labe="qu-label" can cause issues:
   # QGL2 creates barriers that look like:
#        Barrier('seq_0_1', [QBIT_q1, QBIT_qs, QBIT_qs2, QBIT_qs3, (QBIT_qu - label)]),
    # And the error message says: "SyntaxError: can't assign to operator"
