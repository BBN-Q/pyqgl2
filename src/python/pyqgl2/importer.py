# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import ast
import os
import sys

from pyqgl2.ast_util import NodeError
from pyqgl2.ast_util import NodeTransformerWithFname
from pyqgl2.ast_util import NodeVisitorWithFname
from pyqgl2.check_symtab import CheckSymtab
from pyqgl2.check_waveforms import CheckWaveforms
from pyqgl2.lang import QGL2

class Importer(NodeTransformerWithFname):
    """
    Find imports and queue them up for later importing
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
        self.fname = module_name
        self.module_path = module_name

        self.level = 0

        self.current_index = 0

        self.import_queue = list()
        self.node_queue = list()
        self.ast_queue = list()

        self.schedule_import(None, module_name)
        self.process_imports()

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

    def schedule_import(self, node, path):

        if path not in self.import_queue:
            self.import_queue.append(path)
            self.node_queue.append(node)
        else:
            self.diag_msg(node, 'skipping redundant import of %s' % path)

        self.process_imports()

    def process_imports(self):

        while True:
            ind = self.current_index

            if ind >= len(self.import_queue):
                return

            path = self.import_queue[ind]
            node = self.node_queue[ind]
            self.current_index += 1

            # TODO: diagnostic
            print('reading file [%s]' % path)

            text = open(path, 'r').read()
            ptree = ast.parse(text, mode='exec')

            self.ast_queue.append(ptree)

            old_fname = self.fname
            self.fname = path
            self.visit(ptree)
            self.fname = old_fname

    def visit_Module(self, node):
        for stmnt in node.body:
            if type(stmnt) == ast.If:
                self.handle_if(stmnt)

        return node

    def handle_if(self, node):
        """
        We only import QGL2 files from a top-level
        block that looks like:

        if qgl2.qgl2import:
            import foo
            import bar

        """

        if type(node) != ast.If:
            return node
        if type(node.test) != ast.Attribute:
            return node
        if type(node.test.value) != ast.Name:
            return node
        if node.test.value.id != QGL2.QMODULE:
            return node
        if node.test.attr != QGL2.QIMPORT:
            return node

        for stmnt in node.body:
            if type(stmnt) == ast.Import:
                imports = stmnt.names
                for imp in imports:
                    path = self.resolve_path(imp.name)
                    if not path:
                        self.error_msg(stmnt,
                            'path to [%s] could not be found' % imp.name)
                    else:
                        self.schedule_import(stmnt, path)

            elif type(stmnt) == ast.ImportFrom:
                self.error_msg(stmnt, 'import-from unsupported')

        return node

if __name__ == '__main__':
    import sys

    def preprocess(fname):
        importer = Importer(fname)

        if importer.max_err_level >= NodeError.NODE_ERROR_ERROR:
            print('bailing out 1')
            sys.exit(1)

    preprocess(sys.argv[1])
