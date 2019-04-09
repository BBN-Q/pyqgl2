# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
Flatten control structures in terms of simple label,
conditional jumps, and unconditional jumps.

We're still figuring out how this is going to look,
so this is initially a sketch.  It may be overtaken
by events.
"""

import ast

from copy import deepcopy

import pyqgl2.ast_util

from pyqgl2.ast_util import NodeError
from pyqgl2.ast_util import ast2str, expr2ast

from pyqgl2.ast_qgl2 import is_with_label, is_with_call
from pyqgl2.ast_qgl2 import is_concur, is_infunc

class LabelManager(object):
    """
    Simplify the creation of labels.

    This is intended to be used to create labels that express
    more mnemonic information than the pure labels created via
    BlockLabel.newlabel().  If the labels are never looked at
    by a human, however, then any identifier is as good as
    any other.
    """

    NEXT_LABEL_NUM = 0

    @staticmethod
    def allocate_ind():
        """
        Allocate and return the next label index

        Since the preprocessor is single-threaded, there is
        no need to guard against concurrent allocations
        """

        ind = LabelManager.NEXT_LABEL_NUM
        LabelManager.NEXT_LABEL_NUM += 1

        return ind

    @staticmethod
    def allocate_labels(*args):
        """
        Allocate labels for each of the args, with each label
        made unique with a freshly allocated label index

        Each arg of the args must be unique, and is used as
        the prefix of the label strings created.  For example,
        allocate_labels('foo', 'bar') might return ['foo_1', 'bar_1']
        the first time it is called, and ['foo_2', 'bar_2'] the
        second time it is called, etc.
        """

        if len(args) == 0:
            return list()

        for name in args:
            assert isinstance(name, str), 'name must be a str'

        assert len(args) == len(set(args)), 'each name must be unique'

        ind = LabelManager.allocate_ind()

        return [ '%s_%d' % (name, ind) for name in args ]


class Flattener(ast.NodeTransformer):
    """
    Flatten control statements to labels, unconditional gotos,
    and conditional gotos

    Note that many of the methods are destructive and modify
    the input AST structure; if you need to preserve the original
    AST, then make a copy of it before using visit().
    """

    def __init__(self):

        # The loop label stack is a stack of (start_label, end_label)
        # tuples used to keep track of the labels for the start and
        # end labels for the current loop, so that "continue" and
        # "break" statements inside the loop will be able to find
        # the enclosing label for the (potentially) non-local
        # destination
        #
        # Only loop labels are pushed on this stack, since
        # "if/elif/else" and other control structures are purely
        # local
        #
        self.loop_label_stack = list()

    def flatten_body(self, body):
        """
        Flatten the body of a block statement, and expand
        whatever statements can be expanded (and flattened)
        within that block
        """

        new_body = list()

        for stmnt in body:
            flattened_stmnt = self.visit(stmnt)
            if isinstance(flattened_stmnt, list):
                new_body += flattened_stmnt
            else:
                new_body.append(flattened_stmnt)

        return new_body

    def make_ugoto_call(self, label):
        """
        Create an unconditional goto call
        """

        # Instead of constructing the AST piece by piece,
        # construct a string containing the code we
        # want, and then parse that to create the AST.
        #
        goto_str = 'Goto(BlockLabel(\'%s\'))' % label
        goto_ast = expr2ast(goto_str)
        return goto_ast

    def make_cgoto_call(self, label, node, cmp_operator, cmp_addr, value):
        """
        Create a conditional goto call
        """

        if isinstance(cmp_operator, ast.Eq):
            cmp_ast = expr2ast('CmpEq("%s", %s)' % (cmp_addr, str(value)))
        elif isinstance(cmp_operator, ast.NotEq):
            cmp_ast = expr2ast('CmpNeq("%s", %s)' % (cmp_addr, str(value)))
        elif isinstance(cmp_operator, ast.Gt):
            cmp_ast = expr2ast('CmpGt("%s", %s)' % (cmp_addr, str(value)))
        elif isinstance(cmp_operator, ast.Lt):
            cmp_ast = expr2ast('CmpLt("%s", %s)' % (cmp_addr, str(value)))
        else:
            NodeError.error_msg(node,
                'Unallowed comparison operator [%s]' % ast2str(node))
            return None
        label_ast = expr2ast('Goto(BlockLabel(\'%s\'))' % label)

        pyqgl2.ast_util.copy_all_loc(cmp_ast, node, recurse=True)
        pyqgl2.ast_util.copy_all_loc(label_ast, node, recurse=True)

        return list([cmp_ast, label_ast])

    def make_label_call(self, label):

        label_ast = ast.Expr(value=ast.Call(
                func=ast.Name(id='BlockLabel', ctx=ast.Load()),
                args=list([ast.Str(s=label)]),
                keywords=list()))

        return label_ast

    def visit_Assign(self, node):
        """
        Flatten an assignment. The only assignments we should see
        are Qubits, QValues, measurements, and runtime computations.
        If we see a measurement, we need to schedule the pulse (the RHS).
        A runtime computation is passed through as an opaque STORE command.
        """
        if not isinstance(node.value, ast.Call):
            NodeError.error_msg(node,
                "Unexpected assignment [%s]" % ast2str(node))
        if hasattr(node, 'qgl2_type'):
            if node.qgl2_type == 'qbit':
                return node
            elif node.qgl2_type == 'qval':
                return node
            elif node.qgl2_type == 'measurement':
                new_node = ast.Expr(value=node.value)
                new_node.qgl2_type = 'measurement'
                pyqgl2.ast_util.copy_all_loc(new_node, node)
                return new_node
            elif node.qgl2_type == 'runtime_call':
                # put the runtime_call in a STORE command
                new_node = expr2ast('Store()')
                # first argument is the STORE destination
                # TODO we want to re-write the target as an address
                target_str = ast2str(node.targets[0]).strip()
                new_node.value.args.append(ast.Str(s=target_str))
                # second argument is the str() representation
                # of the runtime call
                call_str = ast2str(node.value).strip()
                new_node.value.args.append(ast.Str(s=call_str))
                new_node.qgl2_type = 'runtime_call'
                pyqgl2.ast_util.copy_all_loc(new_node, node, recurse=True)
                return new_node

        return node

    def visit_If(self, node):
        """
        flatten an "if" statement, returning a new list of
        expressions that represent the flattened sequence
        """

        # make sure that the test involves runtime values.
        # This is the only kind of test that should survive
        # to this point; classical test would have already
        # been executed.
        # FIXME add this check
        # Also, if the test contains a call, we should
        # move the evaluation of that call to a expression before
        # the comparison

        if (isinstance(node.test, ast.Name) or
                isinstance(node.test, ast.Call)):
            mask = 0
            cmp_addr = node.test.id
            cmp_operator = ast.NotEq()
        elif (isinstance(node.test, ast.UnaryOp) and
                isinstance(node.test.op, ast.Not)):
            mask = 0
            cmp_addr = node.test.operand.id
            cmp_operator = ast.Eq()
        elif isinstance(node.test, ast.Compare):
            # FIXME the value can be on either side of the comparison
            # this assumes that it is on the right
            mask = node.test.comparators[0].n
            cmp_addr = node.test.left.id
            cmp_operator = node.test.ops[0]
        else:
            NodeError.error_msg(node.test,
                    'unhandled test expression [%s]' % ast2str(node.test))
            return node

        if_label, end_label = LabelManager.allocate_labels(
                'if', 'if_end')

        cond_ast = self.make_cgoto_call(if_label,
                                        node.test,
                                        cmp_operator,
                                        cmp_addr,
                                        mask)

        # cond_ast is actually a list of AST nodes
        new_body = cond_ast

        end_goto_ast = self.make_ugoto_call(end_label)
        if_ast = self.make_label_call(if_label)
        end_label_ast = self.make_label_call(end_label)

        pyqgl2.ast_util.copy_all_loc(end_goto_ast, node, recurse=True)
        pyqgl2.ast_util.copy_all_loc(if_ast, node, recurse=True)
        pyqgl2.ast_util.copy_all_loc(end_label_ast, node, recurse=True)

        if node.orelse:
            new_body += self.flatten_body(node.orelse)

        new_body.append(end_goto_ast)
        new_body.append(if_ast)
        new_body += self.flatten_body(node.body)
        new_body.append(end_label_ast)

        return new_body

def flatten(node):
    """
    Convenience method for the flattener: create a Flattener
    instance, make a copy of the given node, use the instance
    to flatten the copy of the node, and return the result
    """

    flattener = Flattener()
    new_node = deepcopy(node)
    flattened_node = flattener.visit(new_node)

    return flattened_node


if __name__ == '__main__':

    def test_allocate_label():
        t0 = LabelManager.allocate_labels('a', 'b', 'c')
        t1 = LabelManager.allocate_labels('a', 'b', 'c')
        t2 = LabelManager.allocate_labels('a', 'b', 'c')

        assert t0 == ['a_0', 'b_0', 'c_0'], 'failed test 0'
        assert t1 == ['a_1', 'b_1', 'c_1'], 'failed test 1'
        assert t2 == ['a_2', 'b_2', 'c_2'], 'failed test 2'

        print('test_allocate_label success')

    def test_code(code_text):
        tree = ast.parse(code_text, mode='exec')
        flat = Flattener()
        new = flat.visit(deepcopy(tree))
        print('ORIG\n%s\n=>\n%s' % (ast2str(tree), ast2str(new)))

    def t1_while():
        code = """
foo()
while True:
    foo()
    bar()
    qux()
"""
        test_code(code)

    def t2_while():
        code = """
while(MEAS(q1)):
    while True:
        foo()
        break
        bar()
    Id(q1)
    X90(q1)
"""
        test_code(code)

    def t1_if():
        code = """
if(MEAS(q1)):
    foo()
    if x:
        bar()
    else:
        qux()
else:
    if y:
        Id(q1)
    else:
        X90(q1)
"""
        test_code(code)

    def main():
        test_allocate_label()

        t1_while()
        t2_while()
        t1_if()

    main()
