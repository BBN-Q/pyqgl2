# QGL2 Compiler

[![Build Status](https://travis-ci.org/BBN-Q/pyqgl2.svg?branch=master)](https://travis-ci.org/BBN-Q/pyqgl2) [![Coverage Status](https://coveralls.io/repos/BBN-Q/pyqgl2/badge.svg?branch=master)](https://coveralls.io/r/BBN-Q/pyqgl2)

This is the QGL2 language compiler. QGL2 is a python-like language for
programming quantum computers. It is a "low-level language" in the sense that
programs directly specify gates at the physical layer, but with many of the
niceties of a high-level programming language provided by the python host
language.

Documentation on the QGL2 compiler and language, including current known limitations, is in [doc].

## Examples

For usage examples, see the sample Jupyter notebooks in the [sample notebooks directory](/notebooks).

For code samples, see the [Basic Sequences](/src/python/qgl2/basic_sequences).

For an example of compiling a QGL2 program from the command-line, see [doc/README.txt].

QGL2 directly parses the Python syntax to give natural looking qubit sequences and control flow.
measurement results to variables and control flow statements. For example:

```python
@qgl2decl
def RabiAmp(qubit: qreg, amps, phase=0):
    """Variable amplitude Rabi nutation experiment."""
    for amp in amps:
        init(qubit)
        Utheta(qubit, amp=amp, phase=phase)
        MEAS(qubit)

Once a function is decorated with `@qgl2decl` it can act as the `main` for
compiling a QGL2 program. If the `RabiAmp` function is placed in a Python module
then it can be compiled with something like:

```python
from pyqgl2.main import compile_function
from pyqgl2.qreg import QRegister
import numpy as np
q = QRegister(1)
qgl1Function = compile_function(filename, "RabiAmp", (q, np.linspace(0, 1, 1), 0))
```

The result is a function, whose execution generates a QGL sequence.
```python
# Run the compiled function. Note that the generated function takes no arguments itself
seq = qgl1Function()
```
That sequence can then be examined or compiled to hardware, as described in the [QGL documentation](https://github.com/BBN-Q/QGL).

QGL2 uses type annotations in function calls to mark quantum and classical
values. Encapsulating subroutines makes it possible to write tidy compact code
using natural pythonic iteration tools.

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

By embedding in Python, powerful metaprogramming of sequences is possible. For
example process tomography on a two qubit sequence becomes a function.

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
### Current instructions
<!-- Be sure to keep this in sync with .travis.yml and setup.py -->
 * Most any OS should be OK. Instructions tested on Ubuntu 18.04
 * Install `git` and `buildessentials` packages
 * `git-lfs` is now required: See https://git-lfs.github.com/
  * Download it & unpack and run `install.sh`
 * Install python 3.6; easiest done using [Anaconda](https://www.anaconda.com/distribution/#download-section)
  * See below for sample installation given an Anaconda install
  * You will need python 3 compatible atom (either atom 1.0.0-dev or ecpy channel atom 0.4)
 * Install QGL: (https://github.com/BBN-Q/QGL)
  * Install QGL dependencies: `cd QGL; pip install -e .`
  * From within the QGL git clone, set up git lfs: `<QGL>$ git lfs install`
  * Add QGL to your `.bashrc`: `export PYTHONPATH=$QHOME/QGL:$QHOME/pyqgl2/src/python`
 * Then: `pip install meta` and `pip install watchdog`
 * Optional: `pip install pep8` and `pip install pylint`
 * For typical usage, you also need Auspex (https://github.com/BBN-Q/Auspex)
  * See install instructions at https://auspex.readthedocs.io/en/latest/
   * Download or clone, then `cd auspex; pip install -e .`
  * Put `Auspex/src` on your `PYTHONPATH` as in above
 * Install `bbndb` as well (if not installed by QGL): `git clone git@github.com:BBN-Q/bbndb.git`
  * Put the bbndb directory on your PYTHONPATH
  * `pip install -e .`
 * ?Optional: Get the BBN Adapt module as well
  * `git@github.com:BBN-Q/Adapt.git`
  * Put `Adapt/src` on your `PYTHONPATH` as in above
 * Create a measurement file, typically eg `QHOME/test_measure.yml`, containing:
```
config:
  AWGDir: /tmp/awg
  KernelDir: /tmp/kern
  LogDir: /tmp/alog
```
 * Set an environment variable to point to it in your `.bashrc`: `export BBN_MEAS_FILE=$QHOME/test_measure.yml`
 * Optional: Install `coveralls` (i.e. for CI)
 * Download `pyqgl2` source from git (https://github.com/BBN-Q/pyqgl2)
 * Test: `cd pyqgl2; python -m unittest discover`. Should see 80+ tests run without errors (warnings are OK).

### Dependencies
<!-- Be sure to keep this in sync with .travis.yml and setup.py -->
 * Working [https://github.com/BBN-Q/QGL] installation (including `networkx`, `numpy`, `scipy`, `bqplot`, `sqlalchemy`)
 * Python 3.6
 * watchdog and meta
 * PYTHONPATH includes `<QGL2 install directory>/src/python`

### Sample install using Anaconda
```bash
<install anaconda python3>
conda install future
conda install -c ecpy atom watchdog
pip install meta
git clone --recurse-submodules git@github.com:BBN-Q/QGL
cd QGL
pip install -e .
git lfs install
cd ..
git clone https://github.com/BBN-Q/auspex.git
cd auspex
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
