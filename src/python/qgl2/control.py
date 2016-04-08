# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# In order to force the import of the stubs for QGL functions
# that are referenced by the output of the preprocessor,
# always add a 'from qgl2.control import *' into the top-level
# of your QGL2 program.
#
# TODO: this should happen implicitly; the QGL2 programmer
# shouldn't have to pull in imports they don't know they need.

from .qgl1 import BlockLabel, Call, Return, Goto
from .qgl1 import LoadRepeat, Repeat
from .qgl1 import Sync, Wait
