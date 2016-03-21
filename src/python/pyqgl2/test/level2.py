# Run main.py

# We don't need all the QGL2 symbols here,
# but this is the generic boilerplate
#
from qgl2.qgl2 import concur, qgl2decl, qgl2main
from qgl2.qgl2 import classical, pulse, qbit, qbit_list
from qgl2.qgl1 import Qubit

@qgl2decl
def bar(chan:classical) -> qbit:
    # This next line gives an error
    # You can't create a qubit in a return statement
    # And you can't create a qubit using a variable for the label
    return Qubit(chan)
