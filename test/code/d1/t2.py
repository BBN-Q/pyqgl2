# Run t0.py
from qgl2.qgl2 import classical, pulse, qreg

from t1 import third_level

@qgl2decl
def second_level(a: qreg, b: qreg):
    third_level(a, b)
    third_level(b, a)

