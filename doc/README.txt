QGL2 Compiler

This is the QGL2 language compiler. QGL2 is a python-like language for
programming quantum computers.

Dependencies
 * Working QGL installation (including networkx, bokeh, numpy, scipy, jupyter)
 * Python 3.5
 * Set PYTHONPATH to <QGL2 install directory>/src/python:<QGL install directory>

Expanding on that:
Requires python3 anaconda, cppy, atom 1.0.0, latest QGL repo, and the latest
JSONLibraryUtils repo cloned as a sub-dir to QGL (if you use the
--recurse-submodules arg when cloning QGL, you get it for free).
E.G.
pip install cppy; pip install
git+https://github.com/nucleic/atom.git@1.0.0-dev
git clone <QGL>
cd QGL
git submodule update, or git clone <JSONLibraryUtils>

----

QGL2 is similar to python, but is not python. For some basic
restrictions / limitations / ways it is not full python, see
restrictions.txt

To run a QGL2 program:
See sample Jupyter notebooks in <qgl2>/notebooks. Start with QGL2
RabiAmp.ipynb

The QGL2 main is in pyqgl2.main

Run that with -h to get commandline help.

Sample commandline:

<qgl2>/src/python $ python pyqgl2/main.py qgl2/basic_sequences/RabiMin.py -m doRabiAmp
Using ChannelLibrary from config
Compiled 1 sequences.
['<QGL>/QGL/awg/qgl2main/test/test-APS1.h5', '<QGL>/QGL/awg/qgl2main/test/test-APS2.h5']

When using pyqgl2.main as your main:
 - Any Channel library defined in the usual QGL JSON files will be
 used.
 - The qubit named 'q1' will be used as the Qubit in your QGL2
 program, which must us a single qubit variable named 'q'.
 - If you have no Channel library, a default one will be created.

The QGL2 programs in qgl2/basic_sequences/*Min.py are tuned for
working with the latest QGL2 compiler. Note they all use a single
qubit variable named 'q' that is given a default value at the
start. This value will be replaced by the compiler if a different
value is given as the sole argument to the function.

Note that not all the QGL2 programs in the basic_sequences/*Min.py will
currently work. E.G.:
 * RabiWidth has a problem importing some needed QGL functions
 * Some pulses use calibration sequences, but the helper to produce
 those does not yet work.


Note that the unit tests defined in tests/test_QGL2_Sequences.py do
not currently work.
