# Run t0.py
from qgl2.qgl2 import classical, pulse, qbit, qbit_list

from t1 import third_level

@qgl2decl
def second_level(a: qbit, b: qbit):
    third_level(a, b)
    third_level(b, a)

