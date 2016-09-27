# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
QGL1 or higher-level functions separated from the QGL2 code
because the QGL2 preprocessor cannot (at this time) handle
importing QGL modules
"""

from QGL.Compiler import compile_to_hardware
from QGL.PulseSequencePlotter import plot_pulse_files

# No longer a qgl2decl function, and not annotated so later code doesn't
# complain
def compileAndPlot(listOfSequences, filePrefix, showPlot=False, suffix=''):
    """Compile the listOfSequences to hardware using the given filePrefix, 
    print the filenames, and optionally plot the pulse files.

    Maybe soon again but not now: 
    Return a handle to the plot window; caller can hold it to prevent window
    destruction.
    """

    fileNames = compile_to_hardware(
            listOfSequences, filePrefix, suffix, qgl2=True)
    print(fileNames)

    if showPlot:
        plotWin = plot_pulse_files(fileNames)
        # FIXME: QGL2 won't inline this if there is a return statement
        # return plotWin


