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
            if isinstance(stmnt, ast.While):
                while_body = self.while_flattener(stmnt)
                new_body += while_body
            elif isinstance(stmnt, ast.If):
                if_body = self.if_flattener(stmnt)
                new_body += if_body
            elif isinstance(stmnt, ast.With):
                with_body = self.with_flattener(stmnt)
                new_body += with_body


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

    def flatten_node_body(self, node):
        """
        generic routine for flattening a statement with a body
        """

        new_body = self.flatten_body(node.body)
        node.body = new_body
        return node

    def visit_With(self, node):
        """
        This is where the recursive traversal ends for this
        transformer, and a different traversal begins.
        When we reach this node, we expect it to either
        be a with-concur with a body that consists entirely
        of with-seq statements, or else a with-seq itself
        (outside the context of a with-concur).
        If we are starting at the top level, we will be
        concerned if the first "with" block we encounter is
        anything else.

        If it is a with-seq node, then everything beneath
        this node should be able to translate into a list of
        statements by recursively flattening the contents
        of this with-seq, but this recursion is somewhat
        different than the NodeTransformer traversal because
        it returns lists of statements, not nodes.

        We destructively create a new with-seq that has
        as its body this list of statements.
        """

        if is_with_label(node, 'grouped'):
            # replace all the with-group statements with with-seq
            # statements.  This seems cosmetic, but means that
            # we don't have to make invasive changes in the sequencer
            #

            new_body = list()

            for group in node.body:
                # check that this is a with-group() stmnt.
                # anything else is a FATAL problem

                if not is_with_call(group, 'group'):
                    NodeError.fatal_msg(group, 'expected a with-group node')

                new_seq = expr2ast('with seq: pass')
                pyqgl2.ast_util.copy_all_loc(new_seq, group, recurse=True)

                new_seq.body = self.flatten_body(group.body)

                new_seq.qgl2_referenced_qbits = group.qgl2_referenced_qbits
                new_seq.qgl_chan_list = list(
                        [group.items[0].context_expr.args[0].id])

                new_body.append(new_seq)

            node.body = new_body

        return node

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
        Flatten an "if" statement, turning it into a degenerate
        "if" statement (which may be optimized further later)

        Shouldn't be called any more; only while_flattener
        should be used unless there's a while at the top level.
        """

        new_body = self.if_flattener(node)
        return new_body
        # dbg_if = ast.If(test=ast.NameConstant(value=True),
        #         body=new_body, orelse=list())
        #
        # return dbg_if

    def visit_Assign(self, node):
        """
        Flatten an assignment. The only assignments we should see
        are Qubits, measurements, and runtime computations. If we see a
        measurement, we need to schedule the pulse (the RHS). A runtime
        computation is passed through as an opaque STORE command.
        """
        if not isinstance(node.value, ast.Call):
            NodeError.error_msg(node,
                "Unexpected assignment [%s]" % ast2str(node))
        if hasattr(node, 'qgl2_type'):
            if node.qgl2_type == 'qbit':
                return node
            elif node.qgl2_type == 'measurement':
                new_node = ast.Expr(value=node.value)
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
                pyqgl2.ast_util.copy_all_loc(new_node, node, recurse=True)
                return new_node

        return node

    def with_flattener(self, node):
        """
        For "embedded" with statements, below the top-level
        (which is handled by visit_With)
        """

        if is_with_call(node, 'Qrepeat'):
            return self.repeat_flattener(node)
        elif is_with_label(node, 'Qfor'):
            return self.qfor_flattener(node)
        elif is_with_label(node, 'concur'):
            return self.flatten_body(node.body)
        elif is_with_call(node, 'infunc'):
            return self.flatten_body(node.body)
        elif is_with_label(node, 'Qiter'):
            print('ERROR: should not see Qiter at this level')
            # Bogus
            return self.qiter_flattener(node)
        else:
            NodeError.error_msg(node,
                    ('confused about with statement: %s' % ast.dump(node)))
            return list()

    def qfor_flattener(self, node):
        """
        flatten a 'with Qfor' block
        """

        # figure out what to do here.  Mostly modifying the
        # the context to make sure that the "break" reference
        # points to the right things, and scooping out the
        # guts and returning them.

        # We always allocate a label and update the stack,
        # even if we know we won't need it, just for the
        # sake of simplicity.
        #
        (end_label,) = LabelManager.allocate_labels('qfor_end')

        # the bogus label will be replaced by the qiter_flattener
        # with the label for the next iteration, if any.  It is
        # a placeholder and should never be emitted.
        #
        self.loop_label_stack.append(('BOGUS_LABEL', end_label))

        new_stmnts = list()
        for subnode in node.body:
            if is_with_label(subnode, 'Qiter'):
                new_stmnts += self.qiter_flattener(subnode)
            elif is_with_call(subnode, 'Qrepeat'):
                new_stmnts += self.repeat_flattener(subnode)
            else:
                print('Error: unexpected non-Qiter node')

        self.loop_label_stack.pop()

        # If the original code contains a break statement,
        # then we need to emit code to create the label for
        # the end of the loop.  Otherwise, we can omit it.
        #
        if self.contains_type(node, ast.Break):
            end_ast = expr2ast('BlockLabel(\'%s\')' % end_label)
            new_stmnts.append(end_ast)

        return new_stmnts

    def contains_type(self, node_or_list, ast_type):
        """
        Return True if the given node or any of its descendants is
        of the given ast_type, False otherwise

        For the sake of convenience, this function can also
        take a list of AST nodes instead of a single node.

        TODO: this is a general AST utility and should be moved
        to AST utils.
        """

        if isinstance(node_or_list, list):
            return any(self.contains_type(node, ast_type)
                    for node in node_or_list)

        for subnode in ast.walk(node_or_list):
            if isinstance(subnode, ast_type):
                return True

        return False

    def qiter_flattener(self, node):
        """
        flatten a 'with Qiter' block
        """

        new_body = self.flatten_body(node.body)

        # Modify the continue reference to point to the
        # end of the current iteration.
        #
        # For the sake of simplicity, we *always* allocate
        # a label and update the label stack, even if we
        # know that we're not going to use it.  (this may
        # vary from one iter to another, so we cannot
        # make non-local assumptions about whether or not
        # we need it)

        (next_start_label,) = LabelManager.allocate_labels('continue_iter')

        (old_start_label, end_label) = self.loop_label_stack.pop()
        self.loop_label_stack.append((next_start_label, end_label))

        # We only need to insert the label for the end of the
        # iteration if we know that there is a 'continue' statement
        # somewhere in this iteration
        #
        if self.contains_type(new_body, ast.Continue):
            end_ast = expr2ast('BlockLabel(\'%s\')' % next_start_label)
            pyqgl2.ast_util.copy_all_loc(end_ast, node, recurse=True)

            new_body += [end_ast]

        return new_body

    def repeat_flattener(self, node):
        """
        flatten a 'with qrepeat' block

        A block of the form:

            with qrepeat(n_iters):
                STMNTS

        becomes a sequence of the form

                Call(BlockLabel('repeat_start'))
                Goto(BlockLabel('repeat_end'))
            repeat_start:
                LOAD(n_iters)
            repeat_loop:
                STMNTS
            repeat_repeat: # needed only by "continue" statements
                REPEAT(BlockLabel('repeat_loop'))
            repeat_return: # needed only by "break" statements
                RETURN
            repeat_end:

        NOTE: the block of STMNTS must not contain a break or
        continue statement, except within an enclosing loop
        of its own.  We DO NOT handle breaking or continuing
        a simple iteration at this time, and we DO NOT check
        whether the STMNTS contains any such control statements!

        TODO: at least warn the user if they're heading
        for a disaster.
        """

        n_iters = node.items[0].context_expr.args[0].n

        (start_label, loop_label, end_label, repeat_label, return_label
                ) = LabelManager.allocate_labels(
                        'repeat_start', 'repeat_loop', 'repeat_end',
                        'repeat_repeat', 'repeat_return')

        call_ast = expr2ast('Call(BlockLabel(\'%s\'))' % start_label)
        goto_ast = expr2ast('Goto(BlockLabel(\'%s\'))' % end_label)
        start_ast = expr2ast('BlockLabel(\'%s\')' % start_label)
        load_ast = expr2ast('LoadRepeat(%d)' % n_iters)
        loop_ast = expr2ast('BlockLabel(\'%s\')' % loop_label)

        repeat_label_ast = expr2ast('BlockLabel(\'%s\')' % repeat_label)
        repeat_ast = expr2ast('Repeat(BlockLabel(\'%s\'))' % loop_label)
        return_label_ast = expr2ast('BlockLabel(\'%s\')' % return_label)
        return_ast = expr2ast('Return()')
        end_ast = expr2ast('BlockLabel(\'%s\')' % end_label)

        pyqgl2.ast_util.copy_all_loc(call_ast, node, recurse=True)
        pyqgl2.ast_util.copy_all_loc(goto_ast, node, recurse=True)
        pyqgl2.ast_util.copy_all_loc(start_ast, node, recurse=True)
        pyqgl2.ast_util.copy_all_loc(load_ast, node, recurse=True)
        pyqgl2.ast_util.copy_all_loc(loop_ast, node, recurse=True)
        pyqgl2.ast_util.copy_all_loc(repeat_label_ast, node, recurse=True)
        pyqgl2.ast_util.copy_all_loc(repeat_ast, node, recurse=True)
        pyqgl2.ast_util.copy_all_loc(return_ast, node, recurse=True)
        pyqgl2.ast_util.copy_all_loc(end_ast, node, recurse=True)

        preamble = list([call_ast, goto_ast, start_ast, load_ast, loop_ast])

        self.loop_label_stack.append((repeat_label, return_label))

        body = self.flatten_body(node.body)

        self.loop_label_stack.pop()

        postamble = list(
                [repeat_label_ast, repeat_ast,
                    return_label_ast, return_ast, end_ast])

        return preamble + body + postamble

    def while_flattener(self, node):
        """
        flatten a "while" statement, returning a new list of
        expressions that represent the flattened sequence

        FIXME: does not handle while loops with "orelse" blocks yet
        """

        start_label, end_label = LabelManager.allocate_labels(
                'while_start', 'while_end')

        start_ast = self.make_label_call(start_label)
        end_ast = self.make_label_call(end_label)
        loop_ast = self.make_ugoto_call(start_label)

        print('WFF %s' % ast.dump(node))

        pyqgl2.ast_util.copy_all_loc(start_ast, node, recurse=True)
        pyqgl2.ast_util.copy_all_loc(end_ast, node, recurse=True)
        pyqgl2.ast_util.copy_all_loc(loop_ast, node, recurse=True)

        new_body = list([start_ast])

        if isinstance(node.test, ast.NameConstant) and node.test.value:
            # If the condition is defined to always be True,
            # then don't bother testing it; just fall through
            #
            pass
        else:
            # TODO: this call to cgoto_call is BOGUS FIXME.
            # The parameters for cgoto_call, and the way it
            # depends on the mask, are mockups
            #
            cond_stmnts = self.make_cgoto_call(end_label, node.test, 1)
            new_body += cond_stmnts

        self.loop_label_stack.append((start_label, end_label))

        new_body += self.flatten_body(node.body)

        self.loop_label_stack.pop()

        new_body += list([loop_ast, end_ast])

        return new_body

    def if_flattener(self, node):
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
