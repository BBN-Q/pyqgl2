# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved

"""
Analyze the body of a with-qfor statement to see whether it can be
converted into a "repeat" statement, and make the transformation if
appropriate.
"""


from pyqgl2.ast_util import ast2str, expr2ast

def with_qiter_eq(stmnt1, stmnt2):
    """
    Given two "with-qiter" statements, determine whether they are
    identical and therefore the effect of the two statements
    can be implemented by repeating one of the statements twice.

    Returns True if the statements are identical, False otherwise.

    Note that the statements are assumed to be consecutive,
    NOT separated by a third statement.  If the statements are
    separated, then the comparison is still legitimate, but
    does not imply that the two statements can be replaced with
    iteration.

    Also note that the comparison is assumed to be done
    AFTER the evaluator has finished transforming the statements,
    including rebinding any variables and/or variable names.
    At this point, only a small subset of valid Python statements
    and expressions may appear in the given statements.  We use
    this assumption liberally, and therefore this method may
    need to change if/when the evaluator changes.
    """

    try:
        stmnt_txt1 = ast2str(stmnt1).strip()
    except BaseException as exc:
        print('with_qiter_eq ast2str failed stmnt1')
        return False

    try:
        stmnt_txt2 = ast2str(stmnt2).strip()
    except BaseException as exc:
        print('with_qiter_eq ast2str failed stmnt2')
        return False

    # Just to be doubly certain, try converting the text back
    # to AST again, and then check those results.

    try:
        stmnt1_ast_again = expr2ast(stmnt1_txt1)
        stmnt1_txt_again = ast2str(stmnt1_ast_again).strip()
    except BaseException as exc:
        print('with_qiter_eq expr2ast failed stmnt1')
        return False

    try:
        stmnt2_ast_again = expr2ast(stmnt2_txt1)
        stmnt2_txt_again = ast2str(stmnt2_ast_again).strip()
    except BaseException as exc:
        print('with_qiter_eq expr2ast failed stmnt2')
        return False

    if stmnt_txt1 != stmnt_txt2:
        return False
    elif stmnt1_txt_again != stmnt2_txt_again:
        return False
    else:
        return True


def find_left_dup_qiters(stmnts, compare=None):
    """
    Given a list of statements, return a tuple (base, iter_cnt, iter_len)
    where base is the offset where the iterations begin, iter_cnt is
    the number of repetitions discovered, and iter_len is the number
    of statements in each iteration.  Note that if iter_cnt is 1, then
    no iterations were discovered at all.

    A function to "compare" two statements for equality may be
    passed in as a parameter.  This simplifies testing.

    For example, the sequence [ A, B, C, A, B, C, A ] would result in
    (0, 2, 2), meaning that starting at a base offset of zero,
    there are two iterations of length three.

    This function only attempts to find one iteration, starting at
    the beginning of the stmnts list.  If may be necessary to call
    this function repeatedly, in order to find all the possible
    iterations.  For example, [ A, A, A, B, B, B ] would find the
    three As, and return (0, 3, 1), and then would have to be called
    again on the remainder of the list to find the three Bs.

    The current heuristics for discovering repetitions are incomplete.
    We look for the simple patterns that we expect to be the common case.
    The heurstics may be updated if our expectations turn out to be
    incorrect.

    The current heuristic is that it's better to try to maximize iter_cnt
    and minimize iter_len, in order to compress the code as much as
    possible.  Therefore we look for short subsequences first, starting
    at the beginning of the stmnts, and then if that fails, look for
    longer subsequences.  This greedy approach can miss longer sequences.
    For example, [ A, A, B, A, A, B, A, A, B ] can be expressed as
    three iterations of [ A, A, B ], but the current heuristic will
    instead group this as three iterations of two As separated by Bs.

    The goodness of a grouping is defined to be (iter_cnt - 1) * iter_len, 
    which is simplistic (because it pretends that all of the statements
    have the same length).

    TODO: make sure this comment is up-to-date as the heuristics evolve.
    """

    if compare is None:
        compare = with_qiter_eq

    n_stmnts = len(stmnts)

    # this is the longest possible iter length: we can't divide
    # the stmnts into pieces longer than this
    #
    max_len = int(n_stmnts / 2)


    # in order to prevent an O(n^2) term in the simple implementation,
    # we cap max_len to a small, magic number.  We expect this to suffice
    # in most cases, but this assertion is untested
    #
    # FIXME: this should be a parameter in some sense
    #
    if max_len > 5:
        max_len = 5

    # the best thing we've found so far, which is failure to find
    # anything.
    #
    best = (0, 1, n_stmnts)
    best_score = (best[1] - 1) * best[2]

    for base in range(0, n_stmnts - 1):
        for iter_len in range(1, max_len + 1):

            start1 = base
            start2 = base + iter_len
            end2 = start2 + iter_len

            print('- start1 %d start2 %d' % (start1, start2))

            print('base %d iter_len %d end2 %d' % (base, iter_len, end2))

            while end2 <= n_stmnts:
                cand = (start1, int((end2 - start1) / iter_len), iter_len)
                cand_score = (cand[1] - 1) * cand[2]

                print('    cand base %d cnt %d len %d' %
                        (cand[0], cand[1], cand[2]))

                success = True
                for t in range(iter_len):
                    if not compare(
                            stmnts[start1 + t], stmnts[start2 + t]):
                        print('  failed base %d cnt %d len %d' %
                                (best[0], best[1], best[2]))
                        success = False
                        break

                if success:
                    print('matched! %d %d ' % (best_score, cand_score))
                    if best_score < cand_score:
                        print('     old base %d cnt %d len %d' %
                                (best[0], best[1], best[2]))
                        print('     new base %d cnt %d len %d' %
                                (cand[0], cand[1], cand[2]))
                        best = cand
                        best_score = cand_score
                    else:
                        print('  not a new high score')
                    start2 += iter_len
                    end2 = start2 + iter_len
                else:
                    print('not a match')
                    break

        # We're not looking for the best score globally: we're looking
        # for the leftmost possible non-degenerate score.  For example,
        # if the input is [x, x, y, y, y, y], we'll take the [x, x]
        # segment as a good optimization even though the [y, y, y, y]
        # is better.  We'll get the scores to the right in later passes.

        if best_score > 0:
            break

    return best


if __name__ == '__main__':

    def simple_compare(a, b):
        return a == b

    def test_find_left_dup(arr):
        base, iter_cnt, iter_len = find_left_dup_qiters(arr, simple_compare)

        print('ARR = %s, base %d cnt %d len %d' %
                (str(arr), base, iter_cnt, iter_len))

        return base, iter_cnt, iter_len

    def main():
        assert (0, 4, 1) == test_find_left_dup([1, 1, 1, 1])
        assert (1, 3, 1) == test_find_left_dup([2, 1, 1, 1])
        assert (1, 2, 1) == test_find_left_dup([2, 1, 1, 2])
        assert (0, 2, 2) == test_find_left_dup([1, 2, 1, 2])
        assert (0, 4, 3) == test_find_left_dup(
                [1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3, 4])
        assert (0, 4, 1) == test_find_left_dup(
                [1, 1, 1, 1, 2, 2, 2, 3, 3, 4, 5])
        assert (2, 2, 2) == test_find_left_dup(
                [5, 4, 3, 2, 3, 2, 2, 3, 3, 4, 5])
        assert (2, 3, 2) == test_find_left_dup(
                [5, 4, 3, 2, 3, 2, 3, 2, 3, 4, 5])

        assert (0, 1, 9) == test_find_left_dup([1, 2, 3, 4, 5, 4, 3, 2, 1])
        assert (8, 2, 1) == test_find_left_dup([1, 2, 3, 4, 5, 4, 3, 2, 1, 1])

        # test that we take the leftmost match, not the longest.

        assert (0, 2, 1) == test_find_left_dup(
                [1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 4])
        assert (8, 2, 1) == test_find_left_dup(
                [1, 2, 3, 4, 5, 4, 3, 2, 1, 1, 2, 2, 2])

    main()
