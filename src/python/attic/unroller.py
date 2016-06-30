# Copyright 2015-2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
Old loop unroller

Functionality is now done within eval
"""

class Unroller(ast.NodeTransformer):
    """
    A more general form of the ConcurUnroller, which knows how to
    "unroll" FOR loops and IF statements in more general contexts.

    TODO: document the subset of all possible cases that this
    code actually recognizes/handles
    """

    def __init__(self, importer):

        self.bindings_stack = list()
        self.change_cnt = 0

        self.importer = importer

    def unroll_body(self, body):
        """
        Look through the body of a block statement, and expand
        whatever statements can be expanded/unrolled within the block

        TODO: combine with the logic for inlining functions
        """

        while True:
            old_change_cnt = self.change_cnt

            new_outer_body = list()

            for outer_stmnt in body:
                if isinstance(outer_stmnt, ast.For):
                    unrolled = self.for_unroller(outer_stmnt)
                    new_outer_body += unrolled
                elif isinstance(outer_stmnt, ast.If):
                    unrolled = self.if_unroller(outer_stmnt)
                    new_outer_body += unrolled

                # TODO: add cases for handling other things we
                # can unroll, like ifs or possibly list comprehensions:
                # basically any control flow where we can anticipate
                # exactly what's going to happen

                else:
                    new_outer_body.append(self.visit(outer_stmnt))

            body = new_outer_body

            # If we made changes in the last iteration,
            # then the resulting code might have more changes
            # we can make.  Keep trying until we manage to
            # iterate without making any changes.
            #
            if self.change_cnt == old_change_cnt:
                break

        return body

    def visit_While(self, node):
        node.body = self.unroll_body(node.body)
        return node

    def visit_With(self, node):
        node.body = self.unroll_body(node.body)
        return node

    def visit_FunctionDef(self, node):
        node.body = self.unroll_body(node.body)
        return node

    def visit_Name(self, node):
        """
        If the name has a binding in any local scope (which may
        be nested), then substitute that binding
        """

        name_id = node.id

        for ind in range(len(self.bindings_stack) -1, -1, -1):
            if name_id in self.bindings_stack[ind]:
                self.change_cnt += 1
                return self.bindings_stack[ind][name_id]

        return node

    def if_unroller(self, if_node):

        # Figure out whether we have a constant predicate (of the
        # types of constants we understant) and then what the value
        # of the predicate is:
        #
        # If the test is a Num, check whether it is non-zero.
        # If the test is a NameConstant, then check whether its
        # value is True, False, or None.
        # If the test is a String, then check whether it's the
        # empty string.
        #
        if isinstance(if_node.test, ast.Num):
            const_predicate = True
            predicate = if_node.test.n
        elif isinstance(if_node.test, ast.NameConstant):
            const_predicate = True
            predicate = if_node.test.value
        elif isinstance(if_node.test, ast.Str):
            const_predicate = True
            predicate = if_node.test.s
        else:
            const_predicate = False

        if const_predicate:
            if predicate:
                return self.unroll_body(if_node.body)
            else:
                return self.unroll_body(if_node.orelse)
        else:
            if_node.body = self.unroll_body(if_node.body)
            if_node.orelse = self.unroll_body(if_node.orelse)

            return list([if_node])

    def check_value_types(self, target, values):
        """
        check that the list contains simple expressions:
        numbers, symbols, or other constants.  If there's
        anything else in the list, then bail out because
        we can't do a simple substitution.

        TODO: There are cases where we can't use names; if
        the body of the loop modifies the value bound to a
        symbol mentioned in iter.elts, then this may break.
        This case is hard to analyze but we could warn the
        programmer that something risky is happening.

        TODO: For certain idempotent exprs, we can do more
        inlining than for arbitrary expressions.  We don't
        have a mechanism for determining whether an expression
        is idempotent yet.
        """

        all_simple = True
        simple_expr_types = set(
                [ast.Num, ast.Str, ast.Name, ast.NameConstant])

        if isinstance(target, ast.Tuple):
            target_elts = target.elts
            target_len = len(target_elts)

            # Make sure this is a straightforward tuple of
            # names, and not nested in some way.  We don't
            # handle nested targets yet
            #
            for target_elt in target_elts:
                if not isinstance(target_elt, ast.Name):
                    NodeError.error_msg(target_elt,
                            'expected name, got [%s]' % type(target_elt))
                    return False

            # OK, now that we've determined that the target
            # is good, now check that every value that we need
            # to assign to the target is "compatible" and "simple":
            # it's got to be a list or tuple of the right length,
            # and consist of simple values.
            #
            for ind in range(len(values)):
                value = values[ind]

                if (not isinstance(value, ast.Tuple) and
                        not isinstance(value, ast.List)):
                    NodeError.error_msg(value,
                            'element %d is not a list or tuple' % ind)
                    return False

                if target_len != len(value.elts):
                    NodeError.error_msg(value,
                            ('element %d len != target len (%d != %d)' %
                                (ind, len(value.elts), target_len)))
                    return False

                for elem in value.elts:
                    if type(elem) not in simple_expr_types:
                        all_simple = False
                        break

        else:
            for elem in values:
                if type(elem) not in simple_expr_types:
                    all_simple = False
                    break

        if not all_simple:
            NodeError.diag_msg(target, 'not all loop elements are consts')

        return True # FIXME

    def is_simple_iteration(self, for_node):
        """
        returns (success, count), where success is True if the loop is
        a "simple iteration" (a single loop variable, which is never
        referenced inside the loop), and count is the number of times
        that the loop iterates.

        We could handle loops with multiple targets (as long as
        none of them are ever referenced), but we don't deal with
        this case yet.  The iters either needs to be a literal list
        (ast.List) or a call to the simple form of range().
        """

        assert isinstance(for_node, ast.For)

        if not isinstance(for_node.target, ast.Name):
            return False, 0

        if (isinstance(for_node.iter, ast.Call) and
                isinstance(for_node.iter.func, ast.Name) and
                (collapse_name(for_node.iter.func) == 'range')):

            # We can only handle simple things right now:
            # a simple range, with a simple parameter.
            #
            args = for_node.iter.args
            if len(args) != 1:
                return False, 0

            arg = args[0]
            if not isinstance(arg, ast.Num):
                return False, 0
            elif not isinstance(arg.n, int):
                NodeError.warning_msg(arg, 'range value is not an integer?')
                return False, 0

            iter_cnt = arg.n
        elif isinstance(for_node.iter, ast.List):
            print('EV GOT LIST')
            iter_cnt = len(for_node.iter.elts)
        else:
            return False, 0

        # Search through the body, looking for any of the following:
        #
        # a) a reference to the target name
        # (Omitted) b) a break statement
        # (Omitted) c) a continue statement
        #
        # If we find any of these, then it's not pure iteration; bail out
        #
        target_name = for_node.target.id
        for body_node in for_node.body:
            for subnode in ast.walk(body_node):
                if (isinstance(subnode, ast.Name) and
                        subnode.id == target_name):
                    NodeError.diag_msg(subnode,
                            ('ref to loop var [%s] disables Qrepeat' %
                                subnode.id))
                    return False, 0

        return True, iter_cnt

    def for_unroller(self, for_node, unroll_inner=True):
        """
        Unroll a for loop, if possible, returning the resulting
        list of statements that replace the original "for" expression

        TODO: does it make sense to try to unroll elements of the
        loop, if the loop itself can't be unrolled?  If we reach a
        top-level loop that we can't unroll, that usually means
        that the compilation is going to fail to linearize things
        (although it can be OK if a "leaf" loop can't be unrolled).
        I'm going to leave this as a parameter (unroll_inner) with
        a default value of True, which we can change if it's a bad
        idea.
        """
        DebugMsg.log("Unrolling a for loop %s" % for_node)
        # The iter has to be an ordinary ast.List, or a range expression.
        # expression.  Except for range expressions, it is not enough
        # for it to be an expression that evaluates to a list or
        # collection--it has to be a real, naked list, so we know
        # exactly how long it is.
        #
        # Right now we need it to consist of literals (possibly grouped
        # in tuples or similar simple structures).  Hopefully we'll relax
        # this to include things like range() expressions where the
        # parameters are known.

        if for_node.orelse:
            NodeError.warning_msg(for_node.orelse,
                    'cannot expand for with orelse')
            return list([for_node])

        # check to see if the for loop is a simple repeat.
        # In order for us to detect this, it really does
        # need to be pretty simple: the iter needs to be
        # a range() expression with a counter range, and
        # the target needs to not be referenced anywhere
        # within the body of the loop.
        #
        # If it's simple, then turn the for loop into a
        # "with repeat(N)" block, where N is the number
        # of iterations.  The flattener will turn this
        # into the proper ASP2 code.
        #
        (is_simple, iter_cnt) = self.is_simple_iteration(for_node)
        if is_simple:
            # If is_simple_iteration returns True, then this
            # chain of derefs should just work...
            #
            repeat_txt = 'with %s(%d):\n    pass' % (QGL2.ITER, iter_cnt)
            repeat_ast = expr2ast(repeat_txt)

            pyqgl2.ast_util.copy_all_loc(repeat_ast, for_node, recurse=True)

            # even if we can't unroll this loop, we might
            # be able to unroll statements in the body of
            # the loop, so give that try
            #
            if unroll_inner:
                repeat_ast.body = self.unroll_body(for_node.body)
            else:
                repeat_ast.body = for_node.body

            return list([repeat_ast])

        # If we've expanded and evaluated for_node.iter, then
        # we expect it to be a list.  This might not have happened
        # yet, however.

        if not isinstance(for_node.iter, ast.List):
            if unroll_inner:
                # even if we can't unroll this loop, we might
                # be able to unroll statements in the body of
                # the loop, so give that try
                #
                new_body = self.unroll_body(for_node.body)
                for_node.body = new_body
            return list([for_node])

        vals = for_node.iter.elts
        if not self.check_value_types(for_node.target, vals):
            NodeError.diag_msg(for_node, 'not all loop elements are simple')

            if unroll_inner:
                # even if we can't unroll this loop, we might
                # be able to unroll statements in the body of
                # the loop, so give that try
                #
                new_body = self.unroll_body(for_node.body)
                for_node.body = new_body
            return list([for_node])

        # TODO more checking for consistency/fit

        new_stmnts = list()

        for index in range(len(vals)):

            try:
                bindings = self.make_bindings(for_node.target, vals[index])
            except TypeError as exc:
                NodeError.error_msg(vals[index], str(exc))
                return new_stmnts # return partial results; bail out later

            # Things to think about: should all the statements that
            # come from the expansion of one pass through the loop
            # be grouped in some way (such as a 'with seq' block)?
            # Or should they just be dumped onto the end, as we do now?

            self.bindings_stack.append(bindings)

            new_body = deepcopy(for_node.body)

            new_stmnts += self.replace_bindings(bindings, new_body)

            self.bindings_stack.pop()

        return new_stmnts

    def make_bindings(self, targets, values):
        """
        make a dictionary of bindings for the "loop variables"

        If the target is a single name, then just assign the values
        to it as a tuple.  If the target is a tuple, then try to match
        up the values to the names in the tuple.

        There are a lot of things that could go wrong here, but we
        don't detect/handle many of them yet

        There's some deliberate sloppiness permitted: the loop target
        can be a list (which is weird style) and the parameters can
        be a combination of lists and tuples.  As long as the target
        and each element of the values can be indexed, things will
        work out.  We could be stricter, because if these types are
        mixed it's almost certainly an error of some kind.
        """

        bindings = dict()

        if isinstance(targets, ast.Name):
            bindings[targets.id] = values
        elif isinstance(targets, ast.Tuple) or isinstance(targets, ast.List):

            # If the target is a list or tuple, then the values must
            # be as well
            #
            if (not isinstance(values, ast.List) and
                    not isinstance(values, ast.Tuple)):
                NodeError.error_msg(values,
                        'if loop vars are a tuple, params must be list/tuple')
                return bindings

            # The target and the values must be the same length
            #
            if len(targets.elts) != len(values.elts):
                NodeError.error_msg(values,
                        'mismatch between length of loop variables and params')
                return bindings

            for index in range(len(targets.elts)):
                name = targets.elts[index].id
                value = values.elts[index]

                bindings[name] = value
        else:
            NodeError.error_msg(targets,
                    'loop target variable must be a name or tuple')

        return bindings

    def replace_bindings(self, bindings, stmnts):

        new_stmnts = list()

        for stmnt in stmnts:
            new_stmnt = self.visit(stmnt)
            new_stmnts.append(new_stmnt)

        return new_stmnts

