
if __name__ == '__main__':

    basic_tests = [
            [ """ Basic test """,
"""
with concur:
    for x in [QBIT_1, QBIT_2, QBIT_3]:
        foo(x)
""",
"""
with concur:
    foo(QBIT_1)
    foo(QBIT_2)
    foo(QBIT_3)
"""
            ],

            [ """ Double Nested loops """,
"""
with concur:
    for x in [QBIT_1, QBIT_2, QBIT_3]:
        for y in [4, 5, 6]:
            foo(x, y)
""",
"""
with concur:
    foo(QBIT_1, 4)
    foo(QBIT_1, 5)
    foo(QBIT_1, 6)
    foo(QBIT_2, 4)
    foo(QBIT_2, 5)
    foo(QBIT_2, 6)
    foo(QBIT_3, 4)
    foo(QBIT_3, 5)
    foo(QBIT_3, 6)
"""
            ],

            [ """ Triple Nested loops """,
"""
with concur:
    for x in [QBIT_1, QBIT_2]:
        for y in [QBIT_3, QBIT_4]:
            for z in [5, 6]:
                foo(x, y, z)
""",
"""
with concur:
    foo(QBIT_1, QBIT_3, 5)
    foo(QBIT_1, QBIT_3, 6)
    foo(QBIT_1, QBIT_4, 5)
    foo(QBIT_1, QBIT_4, 6)
    foo(QBIT_2, QBIT_3, 5)
    foo(QBIT_2, QBIT_3, 6)
    foo(QBIT_2, QBIT_4, 5)
    foo(QBIT_2, QBIT_4, 6)
"""
            ],
            [ """ Basic compound test """,
"""
with concur:
    for x in [QBIT_1, QBIT_2, QBIT_3]:
        foo(x)
        bar(x)
""",
"""
with concur:
    foo(QBIT_1)
    bar(QBIT_1)
    foo(QBIT_2)
    bar(QBIT_2)
    foo(QBIT_3)
    bar(QBIT_3)
"""
            ],
            [ """ Nested compound test """,
"""
with concur:
    for x in [1, 2]:
        for y in [3, 4]:
            foo(x)
            bar(y)
""",
"""
with concur:
    foo(1)
    bar(3)
    foo(1)
    bar(4)
    foo(2)
    bar(3)
    foo(2)
    bar(4)
"""
            ],
            [ """ Simple tuple test """,
"""
with concur:
    for x, y in [(1, 2), (3, 4)]:
        foo(x, y)
""",
"""
with concur:
    foo(1, 2)
    foo(3, 4)
"""
            ],
            [ """ Simple tuple test 2 """,
"""
with concur:
    for x, y in [(QBIT_1, QBIT_2), (QBIT_3, QBIT_4)]:
        foo(x)
        foo(y)
""",
"""
with concur:
    foo(QBIT_1)
    foo(QBIT_2)
    foo(QBIT_3)
    foo(QBIT_4)
"""
            ],
            [ """ Compound test 2 """,
"""
with concur:
    for x in [QBIT_1, QBIT_2]:
        for y in [3, 4]:
            foo(x, y)

            for z in [5, 6]:
                bar(x, y, z)
""",
"""
with concur:
    foo(QBIT_1, 3)
    bar(QBIT_1, 3, 5)
    bar(QBIT_1, 3, 6)
    foo(QBIT_1, 4)
    bar(QBIT_1, 4, 5)
    bar(QBIT_1, 4, 6)
    foo(QBIT_2, 3)
    bar(QBIT_2, 3, 5)
    bar(QBIT_2, 3, 6)
    foo(QBIT_2, 4)
    bar(QBIT_2, 4, 5)
    bar(QBIT_2, 4, 6)
"""
            ],

            [ """ expression test """,
"""
with concur:
    for x in [1, 2]:
        for y in [3, 4]:
            foo(x + y)
""",
# extra level of parens needed for the pretty-printer
"""
with concur:
    foo((1 + 3))
    foo((1 + 4))
    foo((2 + 3))
    foo((2 + 4))
"""
            ],

        ]


    def test_case(description, in_txt, out_txt):
        ptree = ast.parse(in_txt, mode='exec')
        unroller = ConcurUnroller()
        new_ptree = unroller.visit(ptree)
        new_txt = pyqgl2.ast_util.ast2str(new_ptree)

        body = new_ptree.body[0].body
        # print('body %s' % ast.dump(body))

        grouper = QbitGrouper()
        redo = grouper.visit(new_ptree)

        partitions = grouper.group_stmnts(body)
        print('partitions: %s' % str(partitions))
        # for pid in partitions:
        #     print('[%s]\n%s' %
        #             (pid, pyqgl2.ast_util.ast2str(partitions[pid]).strip()))


        if out_txt.strip() != new_txt.strip():
            print('FAILURE: %s\n:[%s]\n----\n[%s]' %
                    (description, out_txt, new_txt))
            return False
        else:
            print('SUCCESS: %s' % description)
            return True

    def preprocess(fname):
        text = open(fname, 'r').read()
        ptree = ast.parse(text, mode='exec')

        print('INITIAL PTREE:\n%s' % pyqgl2.ast_util.ast2str(ptree))

        unroller = ConcurUnroller()
        new_ptree = unroller.visit(ptree)

        print('NEW PTREE:\n%s' % pyqgl2.ast_util.ast2str(new_ptree))

        # Now do the transformation

    def test_grouping1():

        def simple_find_qbits(stmnt):
            """
            debugging impl of find_qbits, for simple quasi-statements.

            Assumes that the stmnt is a tuple consisting of a list
            (of qbit numbers) and a string (the description of the statement)
            So finding the qbits is done by returning the first element
            of the tuple.

            See simple_stmnt_list below for an example.
            """

            return stmnt[0]

        simple_stmnt_list = [
                ( [1], 'one-1' ),
                ( [1], 'one-2' ),
                ( [2], 'two-1' ),
                ( [1], 'one-3' ),
                ( [2], 'two-2' ),
                ( [3], 'three-1' ),
                ( [4], 'four-1' ),
                ( [3, 4], 'threefour-1' )
                ]

        res = QbitGrouper.group_stmnts(simple_stmnt_list,
                find_qbits_func=simple_find_qbits)

        for stmnt_list in res:
            print('STMNT_LIST %s' % str(stmnt_list))

    def main():

        test_grouping1()

        for (description, in_txt, out_txt) in basic_tests:
            test_case(description, in_txt, out_txt)

        if len(sys.argv) > 1:
            for fname in sys.argv[1:]:
                preprocess(fname)

    main()
