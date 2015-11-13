
# We don't need all the QGL2 symbols here,
# but this is the generic boilerplate
#
from qgl2.qgl2 import concur, qgl2decl, qgl2main
from qgl2.qgl2 import classical, pulse, qbit, qbit_list
from qgl2.qgl2 import Qbit

@qgl2decl
def bar(chan) -> qbit:
    return Qbit(chan)
