from qgl2.qgl2 import concur, qgl2decl, qgl2main
from qgl2.qgl1 import QubitFactory
from qgl2.qgl1 import X, Y

@qgl2main
def main():

    x = QubitFactory('1')
    y = QubitFactory('2')
    z = QubitFactory('3')

    for q in [x, y, z]:
        with concur:
            X(q)
            Y(q)



