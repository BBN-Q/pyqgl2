import unittest

import ast
from pyqgl2.qreg import QRegister, QReference

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
