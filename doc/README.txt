QGL2 is similar to python, but is not python. For some basic
restrictions / limitations / ways it is not full python, see
restrictions.txt

To run a QGL2 program:
See sample Jupyter notebooks in <qgl2>/notebooks.

The QGL2 main is in `pyqgl2.main`. Run that with -h to get commandline
help. See sample uses in [src/pythong/qgl2/basic_sequences].

Sample commandline:

```
$ python src/python/pyqgl2/main.py -C src/python/qgl2/basic_sequences/Rabi.py -m SingleShotNoArg
AWG_DIR environment variable not defined. Unless otherwise specified, using temporary directory for AWG sequence file outputs.
Will create and use APS2ish 3 qubit test channel library
Creating engine...


COMPILING [src/python/qgl2/basic_sequences/Rabi.py] main SingleShotNoArg
...
Generated sequences:

[WAIT((Qubit('q1'),)),
 Id(q1),
 MEAS(M-q1, shape_fun=<autodyne>),
 WAIT((Qubit('q1'),)),
 X(q1),
 MEAS(M-q1, shape_fun=<autodyne>)]
```

When using pyqgl2.main as your main:
 - Supply `-C` to use a test channel library, or supply a Channel
 Library name to load from a file (see QGL / Auspex documentation).
 - QGL2 function should be rewritten to require no arguments. See the
 sample in `Rabi.py` - `SingleShotNoArg`
