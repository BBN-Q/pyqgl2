# Copyright 2015-2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
Old group-by-qbit code

Functionality is now done within grouper.QbitGrouper
"""


class QbitGrouper(ast.NodeTransformer):
    """
    TODO: this is just a prototype and needs some refactoring
    """

    def __init__(self, local_vars=None):

        if not local_vars:
            local_vars = dict()

        self.local_vars = local_vars

    def visit_FunctionDef(self, node):
        """
        The grouper should only be used on a function def,
        and there shouldn't be any nested functions, so this
        should effectively be the top-level call.

        For every statement in the body of the function,
        if it's a with-concur, then do the grouping as implied
        by that.  Otherwise, treat each statement as if it was
        wrapped in an implicit with-concur/with-seq block,
        because we need to serialize them.  (This isn't the
        only way to deal with this situation, but it meshes
        well with the other mechanisms.)

        Note that the initial qbit creation/assignment is
        treated as a special case: these statements are
        purely classical bookkeeping, even though they look
        like quantum operations, and are left alone.

        TODO: need to figure out how to handle nested with-concurs,
        particularly within conditional statements.
        """

        for i in range(len(node.body)):
            stmnt = node.body[i]

            # If it's a with-concur statement, then recurse.
            # If it's a qbit creation/assigment statement, then
            # leave it alone.
            # If it's anything else, then treat it as strictly
            # sequential; wrap it in a with-concur and with-seq
            # to create a global barriers before/after the statement.
            #
            # TODO: we've been talking about non-global barriers.
            # Adding this will require changes to this logic.
            #
            if is_concur(stmnt):
                node.body[i] = self.visit(stmnt)
                continue
            elif is_infunc(stmnt):
                node.body[i] = self.visit(stmnt)
                continue

            elif (isinstance(stmnt, ast.Assign) and
                    stmnt.targets[0].qgl_is_qbit):
                # Leave the stmnt untouched.
                # TODO: this is an awkward way of determining
                # whether the statement is a qbit assignment.
                # FIXME: really need a cleaner method (here and elsewhere)
                continue
            else:
                seq_node = ast.With(
                        items=list([ast.withitem(
                            context_expr=ast.Name(id='seq', ctx=ast.Load()),
                            optional_vars=None)]),
                        body=list())
                concur_node = ast.With(
                        items=list([ast.withitem(
                            context_expr=ast.Name(id='concur', ctx=ast.Load()),
                            optional_vars=None)]),
                        body=list([seq_node]))

                pyqgl2.ast_util.copy_all_loc(concur_node, stmnt, recurse=True)

                # NOTE: I don't like this.  If the stmnt is a compound
                # statement, then we've put the body into a with-concur
                # and a with-seq, which might not be what the programmer
                # expects (or what we want).
                #
                seq_node.body = list([self.generic_visit(stmnt)])

                # DESTRUCTIVE
                #
                node.body[i] = concur_node

        return node

    def visit_With(self, node):

        if is_concur(node) or is_infunc(node):

            # Hackish way to create a seq node to use
            seq_node = expr2ast('with seq: pass')

            pyqgl2.ast_util.copy_all_loc(seq_node, node)

            groups = self.group_stmnts2(node.body)
            new_body = list()

            for qbits, stmnts in groups:
                new_seq = deepcopy(seq_node)
                new_seq.body = stmnts
                # Mark an attribute on new_seq naming the qbits
                new_seq.qgl_chan_list = qbits
                NodeError.diag_msg(node,
                        ("Adding new with seq marked with qbits %s" %
                            (str(qbits))))
                new_body.append(new_seq)

            node.body = new_body

            # print('Final:\n%s' % pyqgl2.ast_util.ast2str(node))

            return node
        else:
            return self.generic_visit(node) # check

    def group_stmnts2(self, stmnts, find_qbits_func=None):
        """
        A different approach to grouping statements,
        which (hopefully) will work more cleanly on deep
        structures.  See group_stmnts for a basic overview
        of what this function attempts to do.

        NOTE: this function assumes that each statement
        is associated with exactly one qbit.  Operations
        that involve multiple qbits (like CNOT) are treated
        as having a "source" qbit, and this is the qbit
        associated with the statement.  (this may be
        overly simplistic)

        The basic approach taken by this method is:

        a) find all the qbits referenced by the stmnts

        b) for each qbit referenced:

            i) make a copy of the stmnts

            ii) for each qbit, traverse the copy, removing
                any statement that does not reference that qbit.
                (this is a recursive process, if the statements
                are themselves compound)

            iii) for each copy, remove any statements made
                degenerate by removing substatements (for
                example, you could end up with loops filled with
                "with Qiter: pass" statements, which can be safely
                elided).

        (To make this slightly simpler, we stripe this by
        statement, instead of doing the entire statement list
        at once in steps b.i--b.ii.)

        This consumes more memory than a pure construction,
        but it's simpler.
        """

        if find_qbits_func is None:
            find_qbits_func = find_all_channels

        all_qbits = set()

        for stmnt in stmnts:
            all_qbits.update(find_qbits_func(stmnt, self.local_vars))

        qbit2stmnts = dict()

        for qbit in all_qbits:
            new_stmnts = list()

            for stmnt in stmnts:
                pruned_stmnt = self.keep_qbit(stmnt, qbit, find_qbits_func)
                if pruned_stmnt:
                    new_stmnts.append(pruned_stmnt)

            if new_stmnts:
                qbit2stmnts[qbit] = new_stmnts
            else:
                print('GR2: expected to find at least one stmnt? [%s]', qbit)

        """
        for qbit in qbit2stmnts:
            print('GR2 final %s' % qbit)
            for substmnt in qbit2stmnts[qbit]:
                print('   %s' % ast2str(substmnt).strip())
        """

        groups = [ (list([qbit]), qbit2stmnts[qbit])
                for qbit in qbit2stmnts.keys() ]

        return groups

    def keep_qbit(self, stmnt, qbit, finder):
        """
        Fake scaffolding that only looks at the top-level

        NOTE: only looks at the top level and
        determines whether they match the given qbit
        and whether the stmnt contains more than
        one qbit

        TODO: does not examine the internal structure
        of statements in general; the only compound structure
        it considers is the body of top-level Qfor statements

        TODO: add special case (probably to the finder)
        to address the problem of operators that take
        multiple qbits, such as CNOT.
        """

        if is_with_label(stmnt, QGL2.FOR):
            new_body = list()

            # this is wasteful: we make a copy of the whole
            # thing, and then end up throwing away everything
            # but the header.  Should allocate only the header.
            #
            new_qfor = deepcopy(stmnt)

            # TODO: the only thing that should be in the body of a
            # Qfor is a Qiter, but we don't do anything if this
            # assumption is violated.
            #
            for substmnt in stmnt.body:
                if not is_with_label(substmnt, QGL2.ITER):
                    print('EXPECTED %s' % QGL2.ITER)

                if self.keep_qbit(substmnt, qbit, finder):
                    new_body.append(substmnt)

            # We can't have a completely empty body, so add a pass
            # if necessary
            #
            if not new_body:
                new_body = list([ast.Pass()])

            new_qfor.body = new_body
            return new_qfor

        # The general case: it's not a Qfor, at least not at the
        # top level.  It's all or nothing, then.

        qbits = finder(stmnt, self.local_vars)
        n_qbits = len(qbits)
        if n_qbits == 0:
            NodeError.error_msg(stmnt,
                    ('no qbit references in stmnt? [%s]' %
                        ast2str(stmnt).strip()))
            return None
            
        elif n_qbits > 1:
            print('multiple qbit references (%s) in stmnt [%s]' %
                        (str(qbits), ast2str(stmnt).strip()))
            NodeError.error_msg(stmnt,
                    ('multiple qbit references (%s) in stmnt [%s]' %
                        (str(qbits), ast2str(stmnt).strip())))
            return None

        if qbit in qbits:
            return stmnt
        else:
            return None

    def group_stmnts(self, stmnts, find_qbits_func=None):
        """
        Return a list of statement groups, where each group is a tuple
        (qbit_list, stmnt_list) where qbit_list is a list of all of
        the qbits referenced in the statements in stmnt_list.

        The stmnts list is partitioned such that each qbit is referenced
        by statements in exactly one partition (with a special partition
        for statements that don't reference any qbits).

        TODO: Independence is defined ad-hoc here, and will need
        to be something more sophisticated that understands the
        interdependencies between qbits/channels.

        For example, assuming that "x", "y", and "z" refer to
        qbits on non-conflicting channels, the statements:

                X90(x)
                Y90(y)
                Id(z)
                Y90(x)
                X180(z)

        can be grouped into:

                [ [ X90(x), Y90(x) ], [ Y90(y) ], [ Id(z), X180(z) ] ]

        which would result in a returned value of:

        [ ([x], [X90(x), Y90(x)]), ([y], [Y90(y)]), ([z], [Id(z), X180(z)]) ]

        If there are operations over multiple qbits, then the
        partitioning may fail.

        Note that the first step in the partitioning may result
        in the creation of additional statements, with the goal
        of simplifying the later partitioning.  For example, if
        we have a simple iterative loop with more than one qbit
        referenced within it:

                with qrepeat(3):
                    something(QBIT_1)
                    something(QBIT_2)
                    something(QBIT_3)

        In this example, the with statement references three qbits,
        which is an awkward partition.  We can partition the body
        to create three separate loops:

                with qrepeat(3):
                    something(QBIT_1)
                with qrepeat(3):
                    something(QBIT_2)
                with qrepeat(3):
                    something(QBIT_3)

        This seems to create more work, but since the loops are
        going to run on three disjoint sets of hardware, it's
        actually simpler and closer to the actual instruction
        sequence.
        """

        if find_qbits_func is None:
            find_qbits_func = find_all_channels

        qbit2list = dict()

        expanded_stmnts = list()

        # Make a first pass over the list of statements,
        # looking for any that need to be partitioned by creating
        # new statements, thus creating an expanded list of
        # statements.
        #
        # See above for an example.
        #
        for stmnt in stmnts:

            # If this is a qrepeat statement, then partition
            # its body and then create a new qrepeat statement
            # for each partition.
            #
            # Eventually there may be other kinds of statements
            # that we expand, but qrepeat is the only one we
            # expand now
            #
            if is_with_call(stmnt, QGL2.REPEAT):

                rep_groups = self.group_stmnts(stmnt.body)
                for partition, substmnts in rep_groups:
                    # lazy way to create the specialized qrepeat:
                    # copy the whole thing, and then throw away
                    # its body and replace it with the partition.
                    #
                    new_qrepeat = deepcopy(stmnt)
                    new_qrepeat.body = substmnts

                    expanded_stmnts.append(new_qrepeat)
            elif is_with_label(stmnt, QGL2.FOR):
                # TODO: must deal with Qfor and Qiters here.
                expanded_stmnts.append(stmnt)

            else:
                expanded_stmnts.append(stmnt)

        for stmnt in expanded_stmnts:

            qbits_referenced = list(find_qbits_func(stmnt, self.local_vars))
            # print('GR %s -> %s' %
            #         (ast2str(stmnt).strip(), str(qbits_referenced)))

            if len(qbits_referenced) == 0:
                # print('unexpected: no qbit referenced')

                # Not sure whether this should be an error;
                # for now we'll add this to a special 'no qbit'
                # bucket.

                if 'no_qbit' not in qbit2list:
                    qbit2list['no_qbit'] = list([stmnt])
                else:
                    qbit2list['no_qbit'].append(stmnt)

            elif len(qbits_referenced) == 1:
                qbit = qbits_referenced[0]
                if qbit not in qbit2list:
                    qbit2list[qbit] = list([stmnt])
                else:
                    qbit2list[qbit].append(stmnt)
            else:
                # There are multiple qbits referenced by the stmnt,
                # then we need to find any other stmnt lists that
                # we've built up for each of the qbits, and combine
                # them into one sequence of statments, and then
                # map each qbit to the resulting sequence.
                #
                # This would be more elegant if we could have a set
                # of lists, but in Python lists aren't hashable,
                # so we need to fake a set implementation with a list.
                #
                stmnt_set = list()
                stmnt_list = list()

                for qbit in qbits_referenced:
                    if qbit in qbit2list:
                        curr_list = qbit2list[qbit]

                        if curr_list not in stmnt_set:
                            stmnt_set.append(curr_list)

                for seq in stmnt_set:
                    stmnt_list += seq

                stmnt_list.append(stmnt)

                for qbit in qbits_referenced:
                    qbit2list[qbit] = stmnt_list

        # neaten up qbit2list to eliminate duplicates;
        # present the result in a more useful manner

        tmp_groups = dict()

        for qbit in qbit2list.keys():
            # this is gross, but we can't use a mutable object as a key
            # in a table, so we use a string representation

            stmnts_str = str(qbit2list[qbit])
            if stmnts_str in tmp_groups:
                (qbits, _stmnts) = tmp_groups[stmnts_str]
                qbits.append(qbit)
            else:
                tmp_groups[stmnts_str] = (list([qbit]), qbit2list[qbit])

        groups = [ (sorted(tmp_groups[key][0]), tmp_groups[key][1])
                for key in tmp_groups.keys() ]

        return sorted(groups)

