# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
QGL1 or higher-level functions separated from the QGL2 code
because the QGL2 preprocessor cannot (at this time) handle
importing QGL modules
"""

from pyqgl2.main import qgl2_compile_to_hardware
from QGL.PulseSequencePlotter import plot_pulse_files

def compileAndPlot(listOfSequences, filePrefix, showPlot=False, suffix=''):
    """Compile the listOfSequences to hardware using the given filePrefix,
    print the filenames, and optionally plot the pulse files.
    """

    meta_info = qgl2_compile_to_hardware(
            listOfSequences, filePrefix, suffix)

    if showPlot:
        plot_pulse_files(meta_info)

    return meta_info
