import unittest

import ast
from pyqgl2.qreg import QRegister, QReference
from test.helpers import channel_setup

class TestQRegister(unittest.TestCase):
    def setUp(self):
        QRegister.reset()

    def test_reg_width(self):
        a = QRegister(4)
        self.assertEqual(len(a), 4)
        self.assertEqual(a.qubits, [1,2,3,4])

    def test_reg_names(self):
        a = QRegister("q1", "q3")
        self.assertEqual(len(a), 2)
        self.assertEqual(a.qubits, [1, 3])

    def test_reg_concat(self):
        a = QRegister(2)
        b = QRegister(3)
        c = QRegister(a, b)
        self.assertEqual(len(c), len(a) + len(b))
        self.assertEqual(c.qubits, a.qubits + b.qubits)

    def test_reg_ordering(self):
        a = QRegister("q2")
        b = QRegister(3)
        self.assertEqual(len(b), 3)
        self.assertEqual(b.qubits, [1,3,4])

    def test_qref(self):
        a = QRegister(3)
        b = a[2]
        self.assertTrue(isinstance(b, QReference))
        self.assertEqual(b.ref, a)
        self.assertEqual(b.idx, 2)

    # Supplying qubit of same name/index multiple times is no-op; remove duplicates
    # Can use lists and tuples too; sets don't work yet
    def test_unique(self):
        a = QRegister(3)
        b = QRegister('q3')
        c = QRegister(QRegister(a))
        d = QRegister(a,[b,a],(c,a))
        self.assertEqual(a,d)

    # QRegister from Qubit produces QRegister of same name
    def test_qreg_from_qubit(self):
        from QGL import QubitFactory
        channel_setup()
        a = QRegister(1)
        bq = QubitFactory('q1')
        c = QRegister((bq,))
        self.assertEqual(a, c)

    def test_factory(self):
        node = ast.parse("a = QRegister('q1', 'q5')").body[0]
        a = QRegister.factory(node, {})
        self.assertEqual(len(a), 2)
        self.assertEqual(a.qubits, [1,5])

    def test_factory_slice(self):
        local_vars = {'qr': QRegister(3), 'n': 1}
        node = ast.parse("a = QRegister(qr[0], qr[1])").body[0]
        a = QRegister.factory(node, local_vars)
        self.assertEqual(len(a), 2)
        self.assertEqual(a.qubits, [1,2])

        node = ast.parse("a = QRegister(qr[0:2])").body[0]
        a = QRegister.factory(node, local_vars)
        self.assertEqual(len(a), 2)
        self.assertEqual(a.qubits, [1,2])

        node = ast.parse("a = QRegister(qr[:2])").body[0]
        a = QRegister.factory(node, local_vars)
        self.assertEqual(len(a), 2)
        self.assertEqual(a.qubits, [1,2])

        node = ast.parse("a = QRegister(qr[1:])").body[0]
        a = QRegister.factory(node, local_vars)
        self.assertEqual(len(a), 2)
        self.assertEqual(a.qubits, [2,3])

        node = ast.parse("a = QRegister(qr[n:])").body[0]
        a = QRegister.factory(node, local_vars)
        self.assertEqual(len(a), 2)
        self.assertEqual(a.qubits, [2,3])

        node = ast.parse("a = QRegister(qr[-1:])").body[0]
        a = QRegister.factory(node, local_vars)
        self.assertEqual(len(a), 1)
        self.assertEqual(a.qubits, [3])

        node = ast.parse("a = QRegister(qr[0::2])").body[0]
        a = QRegister.factory(node, local_vars)
        self.assertEqual(len(a), 2)
        self.assertEqual(a.qubits, [1,3])

    def test_iter(self):
        a = QRegister(4)
        ct = 0
        for q in a:
            self.assertEqual(q, a[ct])
            ct += 1
