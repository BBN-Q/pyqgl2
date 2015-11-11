# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
Utilities to do an initial parse of the file
and recursively parse any imports in that file

Builds up the data structures needed to navigate
the namespace of each file, which in Python is done
on a file-by-file basis (i.e. resolving the name
'x.y.z' depends on the namespace of x and the namespace
of y.

Only attempts to handle a static, semi-functional
subset of Python3.  Does NOT deal with conditional
imports, or programatic imports, or any of the other
mechanisms for futzing with the namespace.

For the purpose of resolution, treats all imports as
if the happened at the beginning of the file, prior
to all other statements, and does not attempt to
detect or handle dynamic redefinitions of the namespace,
such as on-the-fly changes to the load path.

Only tracks function definitions at the top-level
of the module namespace; does not handle methods
within functions, or nested functions of any kind.
"""

import ast
import os
import sys

from pyqgl2.ast_util import NodeError
from pyqgl2.lang import QGL2

def resolve_path(name):
    """
    Find the path to the file that would be imported for the
    given module name, if any.

    Note that paths are used as the keys for several data
    structures
    """

    name_to_path = os.sep.join(name.split('.')) + '.py'

    for dirpath in sys.path:
        path = os.path.join(dirpath, name_to_path)

        # We don't check whether we can read the file.  It's
        # not clear from the spec whether the Python interpreter
        # checks this before trying to use it.  TODO: test
        #
        if os.path.isfile(path):
            return os.path.relpath(path)

    return None

def collapse_name(node):
    """
    Given the AST for a symbol reference, collapse it back into
    the original reference string

    Example, instead of the AST Attribute(Name(id='x'), addr='y')
    return 'x.y'
    """

    if type(node) == ast.Name:
        return node.id
    elif type(node) == ast.Attribute:
        return collapse_name(node.value) + '.' + node.attr
    else:
        # TODO: handle this more gracefully
        print('UNEXPECTED')
        return None


class NameSpace(object):
    """
    Manage the namespace for a single file
    """

    def __init__(self):

        # functions and variables defined locally
        #
        self.local_defs = dict()
        self.local_vars = dict()

        # symbols (which may be functions or variable) defined
        # elsewhere, but brought into this namespace via a
        # "from" or "from-as" import
        #
        self.from_as = dict()

        # prefixes added to the namespace via an "import"
        # or "import-as"
        #
        self.import_as = dict()

        # For diagnostic purposes, keep track of all of the
        # names known in the namespace.  We use this to detect
        # potential conflicts (often a programmer error)
        #
        self.all_names = set()

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return ('local %s from_as %s import_as %s' %
                (str(self.local_defs), str(self.from_as), str(self.import_as)))

    def check_dups(self, name, def_type='unknown'):
        """
        check whether a symbol by the given name is already
        defined in the namespace (and add it to the namespace
        if it is not)

        Raises a ValueError if already defined
        """

        if name in self.all_names:
            raise ValueError(
                    ('symbol [%s] multiply defined (%s) in namespace' %
                        (name, def_type)))
        else:
            self.all_names.add(name)

    def add_local_var(self, name, ptree):
        self.check_dups(name, 'local-variable')
        self.local_vars[name] = ptree

    def add_local_func(self, name, ptree):
        self.check_dups(name, 'local-function')
        self.local_defs[name] = ptree

    def add_from_as(self, module_name, sym_name, as_name=None):
        if not as_name:
            as_name = sym_name

        self.check_dups(as_name, 'from-as')

        path = resolve_path(module_name)
        if not path:
            raise ValueError('no module found for [%s]' % module_name)

        self.from_as[as_name] = (sym_name, path)

    def add_import_as(self, module_name, as_name=None):
        if not as_name:
            as_name = module_name

        self.check_dups(as_name, 'import-as')

        path = resolve_path(module_name)
        if not path:
            raise ValueError('no module found for [%s]' % module_name)

        self.import_as[as_name] = path


class NameSpaces(object):

    def __init__(self, path, qglmain_name=None):

        # map from path to AST
        #
        self.path2ast = dict()

        # map from path to NameSpace
        #
        self.path2namespace = dict()

        # The error/warning messages are clearer if we always
        # use the relpath
        #
        self.base_fname = os.path.relpath(path)

        # Reference to the main function; initially None because
        # we haven't read it in yet
        #
        self.qglmain = None

        self.read_import(self.base_fname)

        # TODO: if the user asks for a specific main, then go
        # back and use it.  Don't gripe if the user has already defined
        # one.  Resolve the name with respect to the namespace
        # of base_fname

        if qglmain_name:
            qglmain_def = self.resolve_sym(self.base_fname, qglmain_name)

            if not qglmain_def:
                print('error: no definition for qglmain [%s]' % qglmain_name)
                sys.exit(1)
            elif not qglmain_def.qgl_func:
                print('error: qglmain [%s] not declared QGL' % qglmain_name)
                sys.exit(1)
            else:
                self.qglmain = qglmain_def
                qglmain_def.qgl_main = True

        if self.qglmain:
            print('info: using [%s] as qglmain' % self.qglmain.name)
        else:
            print('warning: no qglmain declared or chosen')

    def resolve_sym(self, path, name):
        print('NNN TRYING TO RESOLVE %s in %s' % (name, path))

        if path not in self.path2namespace:
            raise ValueError('cannot find namespace for [%s]' % path)

        namespace = self.path2namespace[path]

        if name in namespace.local_vars:
            print('NNN resolve success (local)')
            return namespace.local_vars[name]
        elif name in namespace.local_defs:
            print('NNN resolve success (local)')
            return namespace.local_defs[name]
        elif name in namespace.from_as:
            orig_name, from_namespace = namespace.from_as[name]
            # Note: this recursion might never bottom out.
            # TODO: detect a reference loop without blowing up
            return self.resolve_sym(from_namespace, orig_name)

        # If it's not a local symbol, or a symbol that's
        # imported to appear to be a local symbol, then
        # see if it appears to be a reference to a module.
        # If so, try finding it there, in that context
        # (possibly renamed with an import-as).

        name_components = name.split('.')
        print('NNN trying to resolve import-as %s' % name_components)

        for ind in range(len(name_components) - 1):
            prefix = '.'.join(name_components[:ind + 1])
            suffix = '.'.join(name_components[ind + 1:])
            print('NNN ind %d prefix %s suffix %s' % (ind, prefix, suffix))

            if prefix in namespace.import_as:
                imported_module = namespace.import_as[prefix]
                print('NNN TRYING prefix %s suffix %s in %s' %
                        (prefix, suffix, imported_module))

                return self.resolve_sym(imported_module, suffix)

        return None

    def returns_pulse(self, module_path, sym_name):
        sym = self.resolve_sym(module_path, sym_name)
        if not sym:
            return False
        else:
            return sym.qgl_return == 'pulse'

    def read_import(self, path):
        """
        Recursively read the imports from the module at the given path
        """

        # TODO: error/warning/diagnostics

        if path in self.path2ast:
            print('NN Already in there [%s]' % path)
            return self.path2ast[path]

        text = open(path, 'r').read()
        ptree = ast.parse(text, mode='exec')
        self.path2ast[path] = ptree

        # label each node with the name of the input file;
        # this will make error messages that reference these
        # notes much more readable
        #
        for node in ast.walk(ptree):
            node.qgl_fname = path

        # Populate the namespace
        #
        namespace = NameSpace()
        self.path2namespace[path] = namespace

        for stmnt in ptree.body:
            if isinstance(stmnt, ast.FunctionDef):
                self.add_function(namespace, stmnt.name, stmnt)
            elif isinstance(stmnt, ast.Import):
                print('NN ADDING import %s' % ast.dump(stmnt))
                self.add_import_as(namespace, stmnt)
            elif isinstance(stmnt, ast.ImportFrom):
                print('NN ADDING import-from %s' % ast.dump(stmnt))
                self.add_from_as(namespace, stmnt.module, stmnt)
            # We're not doing module-level variables right now; no globals
            """
            elif isinstance(stmnt, ast.Assign):
                print('NN ASSIGN %s' % ast.dump(stmnt))
            """

        print('NN NAMESPACE %s' % str(self.path2namespace))

        return self.path2ast[path]

    def find_type_decl(self, node):
        """
        Copied from check_qbit.

        Both need to be refactored.
        """

        q_args = list()
        q_return = None

        if node is None:
            print('NODE IS NONE')

        if type(node) != ast.FunctionDef:
            print('NOT A FUNCTIONDEF %s' % ast.dump(node))
            return None

        if node.returns:
            ret = node.returns

            if type(ret) == ast.Name:
                if ret.id == 'qbit':
                    q_return = 'qbit'
                elif ret.id == 'classical':
                    q_return = 'classical'
                elif ret.id == 'qbit_list':
                    q_return = 'qbit_list'
                elif ret.id == 'pulse':
                    q_return = 'pulse'
                else:
                    print('unsupported return type [%s]' % ast.dump(ret))

        if node.args.args:
            for arg in node.args.args:
                # print('>> %s' % ast.dump(arg))

                name = arg.arg
                annotation = arg.annotation
                if not annotation:
                    q_args.append('%s:classical' % name)
                elif type(annotation) == ast.Name:
                    if annotation.id == 'qbit':
                        q_args.append('%s:qbit' % name)
                    elif annotation.id == 'classical':
                        q_args.append('%s:classical' % name)
                    elif annotation.id == 'qbit_list':
                        q_args.append('%s:qbit_list' % name)
                    else:
                        NodeError.error_msg(node,
                                ('unsupported parameter annotation [%s]' %
                                    annotation.id))
                else:
                    NodeError.error_msg(node,
                            'unsupported parameter annotation [%s]' %
                            ast.dump(annotation))

        print('NN NAME %s (%s) -> %s' %
                (node.name, str(q_args), str(q_return)))

        return (q_args, q_return)

    def add_variable(self, namespace, name, ptree):
        namespace.add_local_var(name, ptree)

    def add_function(self, namespace, name, ptree):
        """
        Add a locally-defined function to the local namespace
        """

        # Parse the decorators for this function.
        # Even if the function is not declared to be QGL,
        # we add it to the symbol table because it's useful
        # later to be able to distinguish between functions
        # that were defined, but not declared to be QGL
        # versus functions that were never defined.
        #
        self.add_func_decorators(ptree.qgl_fname, ptree)

        arg_types, return_type = self.find_type_decl(ptree)
        ptree.qgl_args = arg_types
        ptree.qgl_return = return_type

        namespace.add_local_func(ptree.name, ptree)

    def add_func_decorators(self, module_name, node):

        print('NNN module_name %s ofname %s' % (module_name, self.base_fname))

        qglmain = False
        qglfunc = False
        other_decorator = False

        if node.decorator_list:
            for dec in node.decorator_list:
                print('NNN DECLIST %s %s' % (node.name, ast.dump(dec)))

                # qglmain implies qglfunc, but it's permitted to
                # have both
                #
                if isinstance(dec, ast.Name) and (dec.id == QGL2.QMAIN):
                    qglfunc = True
                    qglmain = True
                elif isinstance(dec, ast.Name) and (dec.id == QGL2.QDECL):
                    qglfunc = True
                else:
                    other_decorator = True

            if qglmain and other_decorator:
                NodeError.warning_msg(node,
                        'unrecognized decorator with %s' % QGL2.QMAIN)
            elif qglfunc and other_decorator:
                NodeError.warning_msg(node,
                        'unrecognized decorator with %s' % QGL2.QDECL)

        print('NNN result %s %s %s' % (node.name, qglfunc, qglmain))
        node.qgl_func = qglfunc
        node.qgl_main = qglmain

        # Only assign the qglmain at the root of the namespace
        # if we're in the base file
        #
        if qglmain and (module_name == self.base_fname):
            if self.qglmain:
                omain = self.qglmain
                NodeError.error_msg(
                        node, 'more than one %s function' % QGL2.QMAIN)
                NodeError.error_msg(
                        node, 'previously defined %s:%d:%d' %
                        (omain.qgl_fname, omain.lineno, omain.col_offset))
            else:
                NodeError.diag_msg(
                        node, '%s declared as %s' % (node.name, QGL2.QMAIN))
                self.qglmain = node

    def add_import_as(self, namespace, stmnt):

        for imp in stmnt.names:
            subpath = resolve_path(imp.name)
            if subpath:
                namespace.add_import_as(imp.name, imp.asname)
                self.read_import(subpath)
            else:
                print('NN IMPORTAS %s' % ast.dump(stmnt))
                NodeError.error_msg(
                        stmnt, 'path to [%s] could not be found' % imp.name)

    def add_from_as(self, namespace, module_name, stmnt):

        subpath = resolve_path(module_name)
        if not subpath:
            NodeError.error_msg(
                    stmnt, 'path to [%s] could not be found' % module_name)
        else:
            self.read_import(subpath)

            for imp in stmnt.names:
                namespace.add_from_as(module_name, imp.name, imp.asname)


if __name__ == '__main__':

    def preprocess(fname):
        """
        An example of how to use the Importer

        Create an Importer instance with the base file name

        After creation, check whether max_err_level indicates
        that an error occured during parsing/importing
        """

        # namespaces = NameSpaces(fname, qglmain_name='xxx')
        namespaces = NameSpaces(fname)
        if NodeError.MAX_ERR_LEVEL >= NodeError.NODE_ERROR_ERROR:
            print('bailing out 1')
            sys.exit(1)

        print('BASENAME %s' % namespaces.base_fname)

        print('PULSE_CHECK %s' % namespaces.returns_pulse('x.py', 'pulser'))
        print('PULSE_CHECK %s' % namespaces.returns_pulse('x.py', 'xxx'))
        print('PULSE_CHECK %s' % namespaces.returns_pulse('x.py', 'xx'))

    # ff = NameSpaces(sys.argv[1])
    # print('Find B.bbb %s' % ast.dump(ff.resolve_sym(sys.argv[1], 'B.bbb')))
    # print('Find cc %s' % ast.dump(ff.resolve_sym(sys.argv[1], 'cc')))

    preprocess(sys.argv[1])
