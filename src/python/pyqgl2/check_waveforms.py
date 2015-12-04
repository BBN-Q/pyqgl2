# Copyright 2015 by Raytheon BBN Technologies Corp.  All rights reserved.

import ast

from pyqgl2.ast_util import NodeError
from pyqgl2.ast_util import NodeTransformerWithFname
from pyqgl2.ast_util import NodeVisitorWithFname
from pyqgl2.builtin_decl import QGL2Functions

class CheckWaveforms(NodeTransformerWithFname):
    """
    Waveform generation pass through the abstract syntax tree:
    at this point we have complete information about each qbit
    channel and can generate and consolidate waveforms
    """

    def __init__(self, fname, func_defs):
        """
        fname is the name of the input

        func_defs is a reference to the function definition dictionary
        from a CheckType instance that has 'visit'ed the AST.
        """

        super(CheckWaveforms, self).__init__()
        self.func_defs = func_defs
        self.waveforms = dict()

    def check_arg(self, call_node, arg, argpos):
        if type(arg) != ast.Name:
            self.error_msg(call_node, '%s param to %s must be a symbol' %
                    (argpos, call_node.func.id))
            return False

        if not self.is_qbit(call_node, arg.id):
            self.error_msg(call_node, '%s param to %s must qbit or channel' %
                    (argpos, call_node.func.id))
            return False

        return True

    def is_qbit(self, context_node, name):
        # print('params %s locals %s' %
        #         (str(context_node.qgl_scope), str(context_node.qgl_local)))

        qbit_name = '%s:qbit' % name
        qchan_name = '%s:qchan' % name

        # TODO: need to check for qchan references in the local context
        #
        # TODO: everything in the local context is a "qbit" of some kind
        # but we should distinguish between qbits, channels, and classical
        # types; all will be useful soon
        #
        if name in context_node.qgl_local:
            return True
        elif qbit_name in context_node.qgl_scope:
            return True
        elif qchan_name in context_node.qgl_scope:
            return True
        else:
            return False

    def visit_Call(self, node):

        print('xxxxx xxxxxxxxxxx HERE')
        func_name = node.func.id

        if func_name in QGL2Functions.UNI_WAVEFORMS:
            print('CASE 1')
            if len(node.args) < 1:
                self.error_msg(node,
                        '%s requires a qbit parameter' % func_name)
                return node

            first_arg = node.args[0]
            # self.check_arg(node, first_arg, 'first')

            self.gen_waveform(func_name, node.args, node.keywords)

        elif func_name in QGL2Functions.BI_OPS:
            print('CASE 2')
            if len(node.args) < 2:
                self.error_msg(node,
                        '%s requires two qbit parameters' % func_name)
                return node

            arg1 = node.args[0]
            arg2 = node.args[1]

            self.check_arg(node, arg1, 'first')
            self.check_arg(node, arg2, 'second')

        elif func_name in self.func_defs:
            print('CASE 3 [%s]' % func_name)
            (fparams, func_def) = self.func_defs[func_name]

            print('FPARAMS %s' % str(fparams))

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

    def find_val(self, call_node, expr): 

        print('EXPR %s' % ast.dump(expr))
        if type(expr) == ast.Name:
            return expr.id
        elif type(expr) == ast.Num:
            return expr.num


    def gen_waveform(self, name, args, kwargs):

        for arg in args:
            self.find_val(None, arg)

        arg_text = ', '.join([ast.dump(arg) for arg in args])
        kwarg_text = ', '.join(sorted([ast.dump(arg) for arg in kwargs]))

        errs = 0
        for arg_index in range(1, len(args)):
            if type(args[arg_index]) != ast.Num:
                self.error_msg(arg, 'arg %d must be a number' % arg_index)
                errs += 1

        if errs:
            return

        signature = '%s-%s' % (name, arg_text)
        if kwarg_text:
            signature += '-%s' % kwarg_text

        # print 'WAVEFORM %s %s %s' % (name, arg_text, kwarg_text)
        # print signature

        if signature in self.waveforms:
            print('xNOTE: already generated waveform %s' % signature)
        else:
            print('generating waveform %s' % signature)
            self.waveforms[signature] = 1 # BOGUS


