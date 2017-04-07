'''
Copyright 2017 Raytheon BBN Technologies

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import ast
from pyqgl2.lang import QGL2
from pyqgl2.debugmsg import DebugMsg
from pyqgl2.ast_util import NodeError, ast2str

# from QGL.ChannelLibrary import QubitFactory

class QRegister(object):
    """
    Registers of Qubits.

    Instances should never be created directly;
    use QRegister.factory() to create
    instances.
    """

    # mapping from index to reference
    KNOWN_QUBITS = dict()
    NUM_REGISTERS = 0

    def __init__(self, *args):
        '''
        Valid constructor calls:
            QRegister(N) where N is an integer
            QRegister("q2", "q5", ...) where the strings are the names of Qubits
            QRegister(qr1, qr2, qr3, ...) where each object is a QRegister
        '''

        self.qubits = []
        if len(args) == 0:
            raise NameError("Must provide at least one argument to QRegister()")
        elif len(args) == 1 and isinstance(args[0], int):
            # width declaration
            N = args[0]
            # find the N lowest qubit indices we haven't used yet
            ct = 1
            while len(self.qubits) < N:
                if ct not in QRegister.KNOWN_QUBITS:
                    self.qubits.append(ct)
                ct += 1
        elif all(isinstance(x, str) for x in args):
            # named qubits
            for arg in args:
                # assume names are of the form "qN"
                # TODO throw an error if the provided string doesn't have that form
                idx = int(arg[1:])
                self.qubits.append(idx)
        elif all(isinstance(x, QRegister) for x in args):
            # concatenated register
            for arg in args:
                if arg.qubits in self.qubits:
                    raise NameError("Non-disjoint qubit sets in concatenated registers")
                self.qubits.extend(arg.qubits)

        # add qubits to KNOWN_QUBITS
        for q in self.qubits:
            QRegister.KNOWN_QUBITS[q] = None

        QRegister.NUM_REGISTERS += 1
        self.reg_name = 'QREG_' + str(QRegister.NUM_REGISTERS)

    def __repr__(self):
        return str(self)

    def __str__(self):
        args = ", ".join("'q{}'".format(q) for q in self.qubits)
        return "QRegister({})".format(args)

    def __eq__(self, other):
        return self.qubits == other.qubits

    def use_name(self, idx=None):
        if idx is not None:
            return 'QBIT_' + str(self.qubits[idx])
        else:
            return self.reg_name

    def __len__(self):
        return len(self.qubits)

    def __getitem__(self, n):
        return QRegister("q" + str(self.qubits[n]))

    def __add__(self, other):
        return QRegister(self, other)

    @staticmethod
    def factory(node, allocated_qbits):
        '''
        Evaluates a ast.Call node of a QRegister and returns its value.

        allocated_qbits is a dictionary of QRegister symbol names mapped
        to their corresponding values.
        '''
        if not is_qbit_create(node):
            NodeError.error_msg(node,
                "Attempted to create a QRegister from an invalid AST node [%s]." % ast2str(node))

        # convert args into values
        arg_values = []
        for arg in node.value.args:
            if isinstance(arg, ast.Num):
                arg_values.append(arg.n)
            elif isinstance(arg, ast.Str):
                arg_values.append(arg.s)
            elif isinstance(arg, ast.Name) and arg.id in allocated_qbits:
                arg_values.append(allocated_qbits[arg.id])
            else:
                NodeError.error_msg(node,
                    "Unhandled argument to QRegister [%s]" % ast2str(arg))

        return QRegister(*arg_values)

    @staticmethod
    def reset():
        QRegister.KNOWN_QUBITS.clear()
        QRegister.NUM_REGISTERS = 0

def is_qbit_create(node):
    """
    Returns True if node represents a qbit creation and assignment.

    There are several sloppy assumptions here.
    """

    if not isinstance(node, ast.Assign):
        return False

    # Only handles simple assignments; not tuples
    # TODO: handle tuples
    if len(node.targets) != 1:
        return False

    if not isinstance(node.value, ast.Call):
        return False

    if not isinstance(node.value.func, ast.Name):
        return False

    if node.value.func.id != QGL2.QBIT_ALLOC:
        return False

    return True
