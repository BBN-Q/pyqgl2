from qgl2.qgl2 import concur, qreg, qgl2decl, sequence, pulse, qgl2main
from qgl2.qgl1 import QubitFactory, X90, Y90


@qgl2decl
def func_c(q: qreg):

	for i in range(0,3):
 		func_b(q)

@qgl2decl
def func_b(q: qreg):

	for i in range(0,3):
 		func_a(q)
 		
@qgl2decl
def func_a(q: qreg) -> pulse:

	for i in range(0,3):
 		X90(q)


@qgl2main
def main():

    q = QubitFactory("1")
    func_c(q)
    


