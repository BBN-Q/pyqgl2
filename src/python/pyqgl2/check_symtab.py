# Copyright 2015 by Raytheon BBN Technologies Corp.  All rights reserved.

import ast

from pyqgl2.ast_util import NodeError
from pyqgl2.ast_util import NodeTransformerWithFname
from pyqgl2.ast_util import NodeVisitorWithFname
from pyqgl2.builtin_decl import QGL2Functions

class CheckSymtab(NodeTransformerWithFname):
    """
    Second pass through the abstract syntax tree:
    at this point we have a preliminary definition
    (at least to the extent of knowing a type)
    of every symbol that we're going to manipulate,
    so we can start to do type checking and
    inference.

    (some of this can be done in the preliminary
    pass, but there's not much to be gained from
    doing earlier)
    """

    def __init__(self, fname, func_defs):
        """
        fname is the name of the input

        func_defs is a reference to the function definition dictionary
        from a CheckType instance that has 'visit'ed the AST.
        """

        super(CheckSymtab, self).__init__(fname)
        self.func_defs = func_defs

    def check_arg(self, call_node, arg, argpos):
        if type(arg) != ast.Name:
            self.error_msg(call_node, '%s param to %s must be a symbol' %
                    (argpos, call_node.func.id))
            return False

        if arg.id not in call_node.qgl_scope:
            print('call scope %s' % str(call_node.qgl_scope))
            self.error_msg(call_node, '%s param to %s must be a qbit' %
                    (argpos, call_node.func.id))
            return False

        return True

    def visit_Call(self, node):

        func_name = node.func.id

        if func_name in QGL2Functions.UNI_WAVEFORMS:
            if len(node.args) < 1:
                self.error_msg(node,
                        '%s requires a qbit parameter' % func_name)
                return node

            first_arg = node.args[0]
            self.check_arg(node, first_arg, 'first')

            self.gen_waveform(func_name, node.args, node.keywords)

        elif func_name in QGL2Functions.BI_OPS:
            if len(node.args) < 2:
                self.error_msg(node,
                        '%s requires two qbit parameters' % func_name)
                return node

            arg1 = node.args[0]
            arg2 = node.args[1]

            self.check_arg(node, arg1, 'first')
            self.check_arg(node, arg2, 'second')

        elif func_name in self.func_defs:
            (fparams, func_def) = self.func_defs[func_name]

            if len(fparams) != len(node.args):
                self.diag_msg(node,
                        '%s %s %s' % (func_name, str(node.args), str(fparams)))
                self.error_msg(node,
                        '%s actual params do not match declaration' %
                            func_name)
            else:
                for ind in range(len(node.args)):
                    arg = node.args[ind]
                    fparam = fparams[ind]

                    if fparam.endswith(':qbit'):
                        self.check_arg(node, arg, fparam)

        else:
            # If it's a function that we don't know about, then
            # it's OK if it's an arbitrary Python function, but
            # it is not permitted to have any quantum parameters
            # (because this would imply that it's a QGL function
            # that wasn't declared, or was declared incorrectly)
            #
            # Note that this means that functions that have
            # "pass through" parameters that they never reference
            # except in other function calls cannot take arbitrary
            # parameters without tripping this error.

            for ind in range(len(node.args)):
                arg = node.args[ind]

                if (type(arg) == ast.Name) and (arg.id in node.qgl_scope):
                    self.error_msg(node,
                            'undeclared function %s called with qbit (%s)' %
                                (func_name, arg.id))

        return node

