# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
Utilities to do an initial parse of the file
and recursively parse any imports in that file
"""

import ast
import os
import sys

from pyqgl2.ast_util import NodeError
from pyqgl2.find_pulse import FindPulseMethods
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
    """

    # Names of "Pulse" types.  Note that these are currently
    # given without scope or context; they are treated like
    # built-in types rather than classes.  This may change
    # in the future (i.e. it might be something like
    # qgl.pulse.Pulse)
    #
    PULSE_TYPES = set(['Pulse'])

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

        # path2context is a mapping for the namespace internal
        # to each module.  For example, if the module xxx contains
        # the line "import foo as bar" then a search for bar.qux
        # inside xxx will be done within module bar.
        #
        # Note that the context is for the entire file, which is
        # not completely correct, because it can be changed by
        # executable statements in the file.  We're glossing over
        # that right now, and assuming it's file-wide and constant.
        #
        # The format of each entry is path:(imported_path, name)
        #
        self.path2context = dict()

        # The format of each entry is path:{def_name, typename}
        #
        self.path2func_defs = dict()

        self.context_stack = list()
        self.context_stack.append(list())

        self.do_import(None, module_name, '<main>', None)

        path = os.path.relpath(module_name)

        self.base_fname = path
        self.base_ptree = self.path2ast[path]

    @staticmethod
    def resolve_path(name):
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

    def resolve_sym(self, context_name, sym_name):
        """
        Resolve a symbol in a given context.

        The context is currently the path to the module from which
        the symbol named sym_name is referenced.

        TODO: this function is incomplete.  It only finds the
        path to the module that would contain the symbol, but
        doesn't pull out the reference OR check whether
        the reference even exists.

        Returns None if resolution fails.  Otherwise, returns tuple
        (path, sym_prefix, sym_suffix, (ast, return_type)), where

        path - the name of the file containing the symbol (used as
            the key to some of the data structures)

        sym_prefix - the name of the module containing the symbol

        sym_suffix - the sym_name, unless the symbol is imported with
            a different name (not supported yet)

        ast - the AST for the definiton of the symbol

        return_type - the declared return type of the symbol, or None
            if there is no return annotation

        """

        sym_components = sym_name.split('.')
        sym_prefix = '.'.join(sym_components[:-1])
        sym_suffix = sym_components[-1]

        context = self.path2context[context_name]
        for path, name in context:
            if name == sym_prefix:
                if self.path2func_defs[path][sym_suffix]:
                    return (path, sym_prefix, sym_suffix,
                            self.path2func_defs[path][sym_suffix])
                else:
                    break

        return None

    def is_pulse(self, context_name, sym_name):
        lookup = self.resolve_sym(context_name, sym_name)

        if not lookup:
            return None
        else:
            print('GOT %s' % lookup[3][1])
            return lookup[3][1] in self.PULSE_TYPES

    def do_import(self, parent, path, import_name, as_name):
        """
        Process an import
        """

        # Convert all paths to be relative to pwd, to the extent possible
        #
        # TODO: this will fail to identify multiple links to the same
        # file
        #
        path = os.path.relpath(path)

        if not as_name:
            as_name = import_name

        context = self.context_stack[-1]

        # check that the as_name isn't already in use
        #
        # Even though it's fatal if we reuse a namespace,
        # we don't halt immediately, so we can do additional
        # checking before giving up
        #
        for (old_path, old_as_name) in context:
            if old_path == path:
                if old_as_name == as_name:
                    self.warning_msg(parent,
                            'repeated import of [%s]' % old_path)
                else:
                    self.warning_msg(parent,
                            'multiple imports of [%s]' % old_path)
            elif old_as_name == as_name:
                self.error_msg(parent,
                        'reusing import as-name [%s]' % as_name)
                break

        # even if we don't import the file again, we add it to
        # the current context if it's not already there
        #
        if (path, as_name) not in context:
            context.append((path, as_name))

        if path not in self.path2ast:
            # Put in a placeholder value into path2ast to prevent
            # recursively visiting this path again.  We'll put in
            # the real value later.
            #
            self.path2ast[path] = None

            if len(self.context_stack) > 1:
                level = len(self.context_stack) - 2
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

            print('CREATING FUNC DEFS %s' % path)
            self.path2func_defs[path] = dict()

            ptree = self.visit(ptree)

            self.path2ast[path] = ptree
            self.context_stack.pop()

            curr_context = self.context_stack[-1]
            context_head = curr_context[0]
            context_tail = curr_context[1:]

            # deal with the base case of the recursion in a clunky
            # manner.  There's probably a cleaner way
            #
            if context_head[1] != '<main>':
                self.path2context[context_head[0]] = context_tail

            return ptree
        else:
            if len(self.context_stack) > 1:
                level = len(self.context_stack) - 2
                self.diag_msg(parent,
                        '%sskipping redundant import of [%s] from [%s]' %
                        ('    ' * level, path, parent.qgl_fname))
            # Probably should return something meaningful
            return None

    def visit_Module(self, node):
        """
        Walk through the body of the module, looking for QGL imports
        (which begin as "if" statements
        """

        for stmnt in node.body:
            # label each node within the statement with the
            # current context (which may change after each
            # statement) of imports within this file.
            #
            # The context determines how symbols referenced
            # by name within that node should be interpreted
            # (i.e., if it's a reference to a.b.c, how should
            # we find where 'a.b.c' is defined?)
            #
            # Most nodes don't need this information, but
            # it's easier to blindly label all of them than
            # to pick and choose
            #
            qgl_context = self.context_stack[-1]
            print('CONTEXT %s' % qgl_context)
            for subnode in ast.walk(stmnt):
                subnode.qgl_context = qgl_context

            if isinstance(stmnt, ast.If):
                self.handle_if(stmnt)

        # A special case for debugging: put the last context
        # for the module as the context of the root node
        #
        node.qgl_context = qgl_context

        self.generic_visit(node)

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

    def visit_FunctionDef(self, node):
        """
        Save references to top-level methods, indexed by local
        name.

        Find methods that are declared to return any type
        listed in self.PULSE_TYPES, and make note of them
        """

        # NOTE: we don't inspect nested functions, because
        # if their parents don't return Pulses, we don't care
        # whether or not they do.  We need Pulses to be returned
        # at the surface.
        #
        # We also don't care about lambdas (although I'm not
        # certain whether lambdas can carry annotations anyway).
        # A method has to be defined with a name, by an ordinary
        # def statement, before we're interested.
        #
        # Final note: if someone uses a decorator to change the
        # type returned by a method so that it doesn't match the
        # annotation, we won't detect this.  We ignore decorators
        # in this test.

        if not node.name:
            return node

        defname = node.name
        fname = node.qgl_fname

        # If a method is redefined, treat this as an error
        #
        # Alternatively, we could let the last definiton win,
        # if the two definitions have different signatures the
        # behavior will be difficult to explain.
        #
        if defname in self.path2func_defs[fname]:
            self.error_msg(node, 'redefinition of %s' % defname)
            return node

        if node.returns:
            ret_type = node.returns
        else:
            ret_type = None

        # XXX TODO: This is a bit of a hack.  If the return type is an
        # ast.Name, and has an id that's in self.PULSE_TYPES, then return
        # the id string.  Otherwise, return and AST.
        #
        # We should boil the AST down to a meaningful string, not return
        # the raw AST.
        #
        if (type(ret_type) == ast.Name) and (ret_type.id in self.PULSE_TYPES):
            ret_type = ret_type.id

        self.path2func_defs[fname][defname] = (node, ret_type)

        return node


if __name__ == '__main__':

    def preprocess(fname):
        """
        An example of how to use the Importer

        Create an Importer instance with the base file name

        After creation, check whether max_err_level indicates
        that an error occured during parsing/importing

        If everything succeeded, look through the importer.path2ast
        dictionary to find the AST for each file imported,
        including the base file.  The base file is identified 
        as importer.module_fname (which might not be the same
        as the base file name, because the paths are normalized
        and/or expressed relatively).
        """

        importer = Importer(fname)
        if importer.max_err_level >= NodeError.NODE_ERROR_ERROR:
            print('bailing out 1')
            sys.exit(1)

        pulser = FindPulseMethods(fname)
        for path in importer.path2ast.keys():
            node = importer.path2ast[path]
            pulser.visit(node)

        for path in importer.path2ast.keys():
            node = importer.path2ast[path]
            print('GOT NAME %s -> %s' % (path, str(node.qgl_context)))
            print(ast.dump(node))

        print('BASENAME %s' % importer.base_fname)
        print('FUNC_DEF %s' % importer.path2func_defs)

        print('X a.foo %s' % str(importer.resolve_sym('x.py', 'a.foo')))
        print('X b.bbb %s' % str(importer.resolve_sym('x.py', 'B.bbb')))

        print('Y a.foo %s' % str(importer.is_pulse('x.py', 'a.foo')))
        print('Y b.bbb %s' % str(importer.is_pulse('x.py', 'B.bbb')))

    preprocess(sys.argv[1])
