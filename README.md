# QGL2 Compiler

[![Build Status](https://travis-ci.org/BBN-Q/pyqgl2.svg?branch=master)](https://travis-ci.org/BBN-Q/pyqgl2) [![Coverage Status](https://coveralls.io/repos/BBN-Q/pyqgl2/badge.svg?branch=master)](https://coveralls.io/r/BBN-Q/pyqgl2)

This is the QGL2 language compiler. QGL2 is a python-like language for
programming quantum computers. It is a "low-level language" in the sense that
programs directly specify gates at the physical layer, but with many of the
niceties of a high-level programming language provided by the python host
language.

## Examples

QGL2 directly parses the Python syntax to give natural looking binding of qubit
measurement results to variables and control flow statements.

```python
# single qubit reset
from qgl2.qgl2 import QRegister
from qgl2.qgl1 import Id, X, MEAS
q = QRegister(1)
m = MEAS(q)
if m:
  X(q)
else:
  Id(q)
```

With decorators and type annotations, function calls that execute pulses on
qubits make it possible to write tidy compact code using natural pythonic
iteration tools.

```python
# multi-qubit QFT
from qgl2.qgl2 import qgl2decl, qreg, QRegister
from qgl2.qgl1 import Id, X90, Y90, X, Y, Ztheta, MEAS, CNOT

from math import pi

@qgl2decl
def hadamard(q: qreg):
    Y90(q)
    X(q)

@qgl2decl
def CZ_k(c: qreg, t: qreg, k):
    theta = 2 * pi / 2**k
    Ztheta(t, angle=theta/2)
    CNOT(c, t)
    Ztheta(t, angle=-theta/2)
    CNOT(c, t)

@qgl2decl
def qft(qs: qreg):
    for i in range(len(qs)):
        hadamard(qs[i])
        for j in range(i+1, len(qs)):
            CZ_k(qs[i], qs[j], j-i)
    MEAS(qs)
```

By embedding in Python powerful metaprogramming of sequences is possible. For
example process tomography on a two qubit sequence comes a function.

```python
@qgl2decl
def tomo(f, q1: qreg, q2: qreg):
    fncs = [Id, X90, Y90, X]
    for prep in product(fncs, fncs):
        for meas in product(fncs, fncs):
            init(q1, q2)
            for p, q in zip(prep, (q1,q2)):
                p(q)
            f(q1, q2)
            for m, q in zip(meas, (q1, q2)):
                m(q)
            for q in (q1, q2):
                MEAS(q)
```


## Installation

### Dependencies

 * Working QGL installation (including networkx, bokeh, numpy, scipy)
 * Python 3.5 or 3.6
 * PYTHONPATH includes <QGL2 install directory>/src/python

Expanding on that:
Requires python3 anaconda, python 3 compatible atom (either atom 1.0.0-dev or
ecpy channel atom 0.4), and latest QGL repo. The quickest way to get started is:

```bash
conda install future
conda install -c ecpy atom watchdog
pip install meta
git clone --recurse-submodules git@github.com:BBN-Q/QGL
cd QGL
pip install -e .
cd ..
git clone git@qiplab.bbn.com:buq-lab/pyqgl2.git
```

## License

Apache License v2.0

## Funding ##

This software is based in part upon work supported by the Office of the Director
of National Intelligence (ODNI), Intelligence Advanced Research Projects
Activity (IARPA), through the Army Research Office contract Nos.
W911NF-10-1-0324 and W911NF-16-1-0114. All statements of fact, opinion or
conclusions contained herein are those of the authors and should not be
construed as representing the official views or policies of IARPA, the ODNI, or
the U.S. Government.
