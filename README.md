# QGL2 Compiler

This is the QGL2 language compiler. QGL2 is a python-like language for
programming quantum computers. It is an "assembly language" in the sense that
programs directly specify gates at the physical layer, but with many of the
niceties of a high-level programming language provided by the python host
language.

## Dependencies

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

## Funding ##

This software is based in part upon work supported by the Office of the Director
of National Intelligence (ODNI), Intelligence Advanced Research Projects
Activity (IARPA), through the Army Research Office contract Nos.
W911NF-10-1-0324 and W911NF-16-1-0114. All statements of fact, opinion or
conclusions contained herein are those of the authors and should not be
construed as representing the official views or policies of IARPA, the ODNI, or
the U.S. Government.
