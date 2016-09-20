from qgl2.qgl2 import concur, qgl2decl, qgl2main
from qgl2.qgl2 import classical, pulse, qbit, qbit_list
from qgl2.qgl1 import QubitFactory, MEAS, X90, X

@qgl2decl
def foo(q1:qbit, q2:qbit):

	with concur:
		while True:
			m1 = MEAS(q1)
			if m1:
				break
			else:
				X(q1)

		while True:
			m2 = MEAS(q2)
			if m2:
				break
			else:
				X(q2)

@qgl2decl
def bar():
	q1 = QubitFactory("1")
	q2 = QubitFactory("2")
	with concur:
		while True:
			m1 = MEAS(q1)
			if m1:
				break
			else:
				X(q1)

		while True:
			m2 = MEAS(q2)
			if m2:
				break
			else:
				X(q2)

@qgl2main
def main():
	q1 = QubitFactory("1")
	q2 = QubitFactory("2")
	with concur:
		reset(q1)
		reset(q2)
	with concur:
		X90(q1)
		X90(q2)
	with concur:
		MEAS(q1)
		MEAS(q2)

@qgl2decl
def reset(q:qbit):
	m = MEAS(q)
	while m == 1:
		X(q)
		m = MEAS(q)
