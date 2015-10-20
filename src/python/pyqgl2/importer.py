# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
Utilities to do an initial parse of the file
and recursively parse any imports in that file
"""

import ast
import os
import sys

from pyqgl2.ast_util import NodeError
from pyqgl2.ast_util import NodeTransformerWithFname
from pyqgl2.lang import QGL2

class Importer(NodeTransformerWithFname):
    """
    Parse a Python file and recursively parse
    any QGL2 imports referenced by that file

    If successful, the path2ast dictionary is
    initialized with the AST corresponding to
    each file (both the initial file and any
    files imported by this file or any file it
    imports), base_fname is initialized to the
    name of the initial file, and base_ptree
    is initialized to the AST for that file

    Each node in the ASTs created through this
    process will be given two extra annotations:

    qgl_fname: the relative path to the file
        that was imported

    qgl_context: the context needed to dereference
        names within that file, which is defined
        by the imports

    NOTE that the qgl_context is not strictly identical
    to the context Python would use to evaluate the
    same code.  The qgl_context for each node in
    a file contains all of the imports for that
    file, even imports that are after the node.
    The qgl_context behaves as if all of the imports
    happened at the beginning of the file, prior to
    any other statements.

    For example, this is legal in QGL2 but not legal
    in Python, because "bar" is used before defined: 

        bar.something()
        import bar

    This "works" in QGL2 because the processor handles
    all of the imports before handles anything else.
    """

    def __init__(self, module_name):
        super(Importer, self).__init__(module_name)

        # The argument passed to the constructor must
        # be the path to the file that we parsed
        # initially, which is also used as the faux
        # module name for the root file.
        #
        # For files that are imported later, we have
        # to use resolve_path to find the path to each
        # module.
        #

        self.path2ast = dict()

        self.context_stack = list()
        self.context_stack.append(list())

        self.do_import(None, module_name, '<main>', None)

        self.base_fname = module_name
        self.base_ptree = self.path2ast[module_name]

    def resolve_path(self, name):
        """
        Find the path to the file that would be imported for the
        given module name, if any.
        """

        name_to_path = os.sep.join(name.split('.')) + '.py'

        for dirpath in sys.path:
            path = os.path.join(dirpath, name_to_path)

            # We don't check whether we can read the file.  It's
            # not clear from the spec whether the Python interpreter
            # checks this before trying to use it.  TODO: test
            #
            if os.path.isfile(path):
                return path

        return None

    def do_import(self, parent, path, import_name, as_name):

        # Convert all paths to be relative to pwd, to the extent possible
        #
        # TODO: this will fail to identify multiple links to the same
        # file
        #
        path = os.path.relpath(path)

        if not as_name:
            as_name = import_name

        # even if we don't import the file again, we add it to
        # the current context if it's not already there
        #
        # TODO: this doesn't address what happens if the same
        # file is imported as multiple different names.  Oof.
        #
        context = self.context_stack[-1]
        if (path, as_name) not in context:
            context.append((path, as_name))

        if path not in self.path2ast:
            # Put in a placeholder value into path2ast to prevent
            # recursively visiting this path again.  We'll put in
            # the real value later.
            #
            self.path2ast[path] = None

            if len(self.context_stack) > 1:
                level = len(self.context_stack) - 1
                self.diag_msg(parent,
                        '%simporting path [%s] from [%s]' %
                            ('    ' * level, path, parent.qgl_fname))

            text = open(path, 'r').read()
            ptree = ast.parse(text, mode='exec')

            # label each node with the name of the input file;
            # this will make error messages much more readable
            #
            for node in ast.walk(ptree):
                node.qgl_fname = path

            self.context_stack.append(list())
            self.context_stack[-1].append((path, None))
            self.visit(ptree)
            qgl_context = self.context_stack.pop()

            # now that we have the complete namespace defined by the
            # imports within this file, label each node with the
            # context in which any symbols referenced by name in
            # that node should be interpreted (i.e., if it's a
            # reference to a.b.c, how should we find where 'a.b.c'
            # is defined?)
            #
            # Most nodes don't need this information, but
            # it's easier to blindly label all of them than
            # to pick and choose
            #
            for node in ast.walk(ptree):
                if not hasattr(node, 'qgl_context'):
                    node.qgl_context = qgl_context

            self.path2ast[path] = ptree
            return ptree
        else:
            if len(self.context_stack) > 1:
                level = len(self.context_stack) - 1
                self.diag_msg(parent,
                        '%sskipping redundant import of [%s] from [%s]' %
                        ('    ' * level, path, parent.qgl_fname))
            # Probably should return something meaningful
            return None

    def visit_Module(self, node):
        for stmnt in node.body:
            if isinstance(stmnt, ast.If):
                self.handle_if(stmnt)

        return node

    def handle_if(self, node):
        """
        We only import QGL2 files from a top-level
        block that looks like:

        if qgl2.qgl2import:
            import foo
            import bar as something

        """

        if not isinstance(node, ast.If):
            return node
        if not isinstance(node.test, ast.Attribute):
            return node
        if not isinstance(node.test.value, ast.Name):
            return node
        if node.test.value.id != QGL2.QMODULE:
            return node
        if node.test.attr != QGL2.QIMPORT:
            return node

        for stmnt in node.body:
            if isinstance(stmnt, ast.Import):
                for imp in stmnt.names:
                    path = self.resolve_path(imp.name)
                    if path:
                        self.do_import(stmnt, path, imp.name, imp.asname)
                    else:
                        self.error_msg(stmnt,
                            'path to [%s] could not be found' % imp.name)
            elif isinstance(stmnt, ast.ImportFrom):
                self.error_msg(stmnt, 'import-from unsupported')

        return node


if __name__ == '__main__':

    def preprocess(fname):
        importer = Importer(fname)

        for path in importer.path2ast.keys():
            print('GOT NAME %s -> %s' %
                    (path, str(importer.path2ast[path].qgl_context)))
            print(ast.dump(importer.path2ast[path]))

        if importer.max_err_level >= NodeError.NODE_ERROR_ERROR:
            print('bailing out 1')
            sys.exit(1)

    preprocess(sys.argv[1])
