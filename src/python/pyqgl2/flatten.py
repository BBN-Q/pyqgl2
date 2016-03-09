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
from pyqgl2.ast_util import ast2str

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
            if isinstance(stmnt, ast.While):
                while_body = self.while_flattener(stmnt)
                new_body += while_body
            elif isinstance(stmnt, ast.If):
                if_body = self.if_flattener(stmnt)
                new_body += if_body

            # TODO: there are other things to flatten,
            # and also things to gripe about if we see
            # them here because they shouldn't reach
            # the flattener.  Detect/handle them here

            else:
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
        goto_ast = ast.parse(goto_str, mode='exec')
        return goto_ast

    def make_cgoto_call(self, label, condition):
        """
        Create a conditional goto call
        """

        goto_ast = ast.Expr(value=ast.Call(
                func=ast.Name(id='Qcond', ctx=ast.Load()),
                args=list([ast.Str(s=label), condition]),
                keywords=list()))

        return goto_ast

    def make_label_call(self, label):

        label_ast = ast.Expr(value=ast.Call(
                func=ast.Name(id='BlockLabel', ctx=ast.Load()),
                args=list([ast.Str(s=label)]),
                keywords=list()))

        return label_ast

    def flatten_node_body(self, node):
        """
        generic routine for flattening a statement with a body
        """

        new_body = self.flatten_body(node.body)
        node.body = new_body
        return node

    def visit_FunctionDef(self, node):
        return self.flatten_node_body(node)

    def visit_With(self, node):
        return self.flatten_node_body(node)

    def visit_Break(self, node):
        """
        Replace a "break" statement with
        a goto out of the current loop,
        or fail if there is no current loop.
        """

        if len(self.loop_label_stack) == 0:
            NodeError.fatal_msg(node, 'empty label stack')
            return node
        else:
            _start_label, end_label = self.loop_label_stack[-1]

            call = self.make_ugoto_call(end_label)

            # TODO: patch up the location information

            return call

    def visit_Continue(self, node):
        """
        Replace a "continue" statement with
        a goto to the top of the current loop,
        or fail if there is no current loop.
        """

        if len(self.loop_label_stack) == 0:
            NodeError.fatal_msg(node, 'empty label stack')
            return node
        else:
            start_label, _end_label = self.loop_label_stack[-1]

            call = self.make_ugoto_call(start_label)

            # TODO: patch up the location information

            return call

    def visit_While(self, node):
        """
        Flatten a "while" loop, turning it into a degenerate
        "if" statement (which may be optimized further later)

        Shouldn't be called any more; only while_flattener
        should be used unless there's a while at the top level.
        """

        new_body = self.while_flattener(node)
        dbg_if = ast.If(test=ast.NameConstant(value=True),
                body=new_body, orelse=list())
        return dbg_if

    def visit_If(self, node):
        """
        Flatten an "if" loop, turning it into a degenerate
        "if" statement (which may be optimized further later)

        Shouldn't be called any more; only while_flattener
        should be used unless there's a while at the top level.
        """

        new_body = self.if_flattener(node)
        dbg_if = ast.If(test=ast.NameConstant(value=True),
                body=new_body, orelse=list())

        return dbg_if

    def while_flattener(self, node):
        """
        flatten a "while" statement, returning a new list of
        expressions that represent the flattened sequence

        FIXME: does not handle while loops with "orelse" blocks yet
        """

        start_label, end_label = LabelManager.allocate_labels(
                'while_start', 'while_end')

        self.loop_label_stack.append((start_label, end_label))

        start_ast = self.make_label_call(start_label)
        end_ast = self.make_label_call(end_label)

        loop_ast = self.make_ugoto_call(start_label)

        new_body = list([start_ast])

        if isinstance(node.test, ast.NameConstant) and node.test.value:
            # If the condition is defined to always be True,
            # then don't bother testing it; just fall through
            #
            pass
        else:
            cond_ast = self.make_cgoto_call(end_label, node.test)
            new_body.append(cond_ast)

        new_body += self.flatten_body(node.body)

        new_body += list([loop_ast, end_ast])

        return new_body

    def if_flattener(self, node):
        """
        flatten an "if" statement, returning a new list of
        expressions that represent the flattened sequence
        """

        else_label, end_label = LabelManager.allocate_labels(
                'if_else', 'if_end')

        if node.orelse:
            cond_ast = self.make_cgoto_call(else_label, node.test)
        else:
            cond_ast = self.make_cgoto_call(end_label, node.test)

        end_goto_ast = self.make_ugoto_call(end_label)
        else_ast = self.make_label_call(else_label)
        end_label_ast = self.make_label_call(end_label)

        new_body = list([cond_ast])

        new_body += self.flatten_body(node.body)

        if node.orelse:
            new_body.append(end_goto_ast)
            new_body.append(else_ast)
            new_body += self.flatten_body(node.orelse)

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
