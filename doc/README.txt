QGL2 is similar to python, but is not python. For some basic
restrictions / limitations / ways it is not full python, see
restrictions.txt

To run a QGL2 program:
See sample Jupyter notebooks in <qgl2>/notebooks. Start with
"QGL2 RabiAmp.ipynb" or "QGL2 RabiSingleShot.ipynb".

The QGL2 main is in `pyqgl2.main`

Run that with -h to get commandline help.

Sample commandline:

```
<qgl2>/src/python $ python pyqgl2/main.py qgl2/basic_sequences/RabiMin.py -m doRabiAmp
Using ChannelLibraries from config
Compiled 1 sequences.
['<QGL>/QGL/awg/qgl2main/test/test-APS1.h5', '<QGL>/QGL/awg/qgl2main/test/test-APS2.h5']
```

When using pyqgl2.main as your main:
 - Any Channel library defined in the usual QGL JSON files will be
 used.
 - The qubit named 'q1' will be used as the Qubit in your QGL2
 program, which must use a single qubit variable named 'q'.
 - If you have no Channel library, a default one will be created.

The QGL2 programs in `qgl2/basic_sequences/*Min.py` are tuned for
working with the latest QGL2 compiler. Note they all use a single
qubit variable named 'q' that is given a default value at the
start. This value will be replaced by the compiler if a different
value is given as the sole argument to the function.

Note that not all the QGL2 programs in the `basic_sequences/*Min.py` will
currently work. E.G.:
 * RabiWidth has a problem importing some needed QGL functions
 * Some pulses use calibration sequences, but the helper to produce
 those does not yet work.


Note that the unit tests defined in `tests/test_QGL2_Sequences.py` do
not currently work.
