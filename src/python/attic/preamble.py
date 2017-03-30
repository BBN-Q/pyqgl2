
import ast

from copy import deepcopy

from pyqgl2.ast_util import ast2str
from pyqgl2.inline import TempVarManager

class LocalNameRewriter(ast.NodeTransformer):
    """
    Replace Name ids that represent variables in the current
    namespace with the given mappings.  Note that variables
    that are accessed via Attributes are assumed to be non-local
    and thus visit_Attribute prevents names within Attributes
    from being modified by this transformation
    """

    def __init__(self, name_mappings):

        assert isinstance(name_mappings, dict), \
                'expected name_mappings to be a dict'

        self.name_mappings = name_mappings

    def visit_Name(self, node):
        """
        Change the node.id to its mapping, if any.

        Destructively modifies the node in-place.
        (make a copy if you need the unmodified version)
        """

        if node.id in self.name_mappings:
            node.id = self.name_mappings[node.id]

        return node

    def visit_Attribute(self, node):
        return node


class LocalNameFinder(ast.NodeVisitor):
    """
    """

    def __init__(self):

        self.names = set()

    def find_names(self, node):
        """
        Find all of the "local" names referenced by the given node

        Ignores names that only appear within Attribute nodes
        """

        self.names = set()

        self.visit(node)

        return self.names

    def visit_Name(self, node):
        """
        Change the node.id to its mapping, if any.

        Destructively modifies the node in-place.
        (make a copy if you need the unmodified version)
        """

        self.names.add(node.id)

    def visit_Attribute(self, node):
        print('WARNING: LocalNameFinder attributes not handled correctly yet')

        return

    def visit_Subscript(self, node):
        print('WARNING: LocalNameFinder arrays not handled yet')



class Preamble(object):

    def __init__(self):

        self.name_mappings = dict()
        self.name_remapper = TempVarManager.create_temp_var_manager(
                name_prefix='___p_tmp')

        self.preamble = list()
        self.preamble_module = ast.Module()

    def apply_name_mappings(self, node):

        node = LocalNameRewriter(self.name_mappings).visit(node)

    def create_name_mappings(self, node):

        names_to_map = LocalNameFinder().find_names(node)

        for name in names_to_map:
            self.name_mappings[name] = self.name_remapper.create_tmp_name(
                    name)

    def separate(self, orig_node):
        """
        Separate a sequence of statements into things that
        are done in the preamble (executed prior to compliation)
        vs done in hardware

        This assumes that the program has been completely
        inlined and unrolled, and is ready to flatten.

        The actual work is done by separate_worker, but that
        function should not be called directly except via seperate()
        (or recursively, from itself).
        """

        # assert isinstance(orig_node, ast.FunctionDef), \
        #         ('expected ast.FunctionDef, got %s' % type(orig_node))

        self.preamble = list()

        node = deepcopy(orig_node)

        self.preamble_module = ast.Module(body=self.preamble)

        return self.separate_worker(node)

    def separate_worker(self, node):

        new_body = list()

        for stmnt_index in range(len(node.body)):
            stmnt = node.body[stmnt_index]

            # TODO: these shouldn't happen, so we should
            # inform the user if we see them.  It means something
            # unexpected happened, probably an error
            #
            if isinstance(stmnt, ast.Pass):
                continue
            elif (isinstance(stmnt, ast.Expr) and
                    isinstance(stmnt.value, ast.Str)):
                continue

            elif isinstance(stmnt, ast.Assign):
                # update all of the names on the right side of
                # of the assignment, and then create new names
                # for the left side of the assignment, and then
                # update the left side of the assignment

                self.apply_name_mappings(stmnt.value)

                for target in stmnt.targets:
                    self.create_name_mappings(target)
                    self.apply_name_mappings(target)

                self.preamble.append(stmnt)

            else:
                self.apply_name_mappings(stmnt)
                new_body.append(stmnt)

        node.body = new_body

        return node


if __name__ == '__main__':

    text = """
a = foo(1, 2)
X(a)
b = bar(a)
b = bar(b)
a = bar(a)
X90(a)
"""

    ptree = ast.parse(text, mode='exec')

    pre = Preamble()
    post = pre.separate(ptree)

    print('    %s' % ast2str(pre.preamble_module))
    print('POST\n%s' % ast2str(post))

