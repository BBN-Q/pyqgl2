from qgl2.qgl2 import concur, qbit, qgl2decl, sequence, pulse, qgl2main
from qgl2.qgl1 import Qubit, X90, Y90


@qgl2decl
def func_c(q: qbit):

	for i in range(0,3):
 		func_b(q)

@qgl2decl
def func_b(q: qbit):

	for i in range(0,3):
 		func_a(q)
 		
@qgl2decl
def func_a(q: qbit) -> pulse:

	for i in range(0,3):
 		X90(q)


@qgl2main
def main():

    q = Qubit("1")
    func_c(q)
    


