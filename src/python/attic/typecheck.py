# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import ast
import meta

from copy import deepcopy

from pyqgl2.ast_util import NodeError, expr2ast
from pyqgl2.importer import NameSpaces
from pyqgl2.importer import collapse_name
from pyqgl2.lang import QGL2

import pyqgl2.ast_util
import pyqgl2.scope

from pyqgl2.ast_util import ast2str

class RuntimeTypeChecker(ast.NodeTransformer):

    def __init__(self, importer):
        print('RTC INIT')

        self.importer = importer

    def visit_With(self, node):
        self.expand(node)

        return node

    def visit_For(self, node):
        self.expand(node)

        return node

    def visit_If(self, node):
        self.expand(node)

        return node

    def visit_While(self, node):
        self.expand(node)

        return node

    def visit_Expr(self, node):

        # we only really understand stubs right now
        if isinstance(node.value, ast.Call):
            print('RTC CALL: %s' % ast2str(node.value).strip())

        return node

    def expand(self, node):
        print('RTC EXPAND')

        if hasattr(node, 'body'):
            print('RTC HAS BODY')
            node.body = self.expand_body(node.body)
        if hasattr(node, 'orelse'):
            print('RTC HAS ORELSE')
            node.orelse = self.expand_body(node.orelse)

        return node

    def expand_body(self, body):
        new_body = list()

        for stmnt in body:
            new_stmnts = self.visit(stmnt)
            new_body.append(new_stmnts)

        return new_body
