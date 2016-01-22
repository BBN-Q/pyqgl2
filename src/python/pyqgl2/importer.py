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

import pyqgl2

def resolve_path(name):
    """
    Find the path to the file that would be imported for the
    given module name, if any.

    Note that paths are used as the keys for several data
    structures
    """

    # At most of one of these will resolve correctly; either
    # it's a directory or a file
    #
    name_to_fpath = os.sep.join(name.split('.')) + '.py'
    name_to_dpath = os.path.join(os.sep.join(name.split('.')), '__init__.py')

    for dirpath in sys.path:
        fpath = os.path.join(dirpath, name_to_fpath)
        dpath = os.path.join(dirpath, name_to_dpath)

        # We don't check whether we can read the file.  It's
        # not clear from the spec whether the Python interpreter
        # checks this before trying to use it.  TODO: test
        #
        if os.path.isfile(fpath):
            return os.path.relpath(fpath)
        elif os.path.isfile(dpath):
            return os.path.relpath(dpath)

    # if all else fails, try using the current directory
    # (I am ambivalent about this)

    fpath = os.path.join('.', name_to_fpath)
    dpath = os.path.join('.', name_to_dpath)

    if os.path.isfile(fpath):
        return os.path.relpath(fpath)
    elif os.path.isfile(dpath):
        return os.path.relpath(dpath)

    return None

def collapse_name(node):
    """
    Given the AST for a symbol reference, collapse it back into
    the original reference string

    Example, instead of the AST Attribute(Name(id='x'), addr='y')
    return 'x.y'
    """

    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return collapse_name(node.value) + '.' + node.attr
    else:
        # TODO: handle this more gracefully
        print('XX UNEXPECTED %s' % ast.dump(node))
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

        # In order to pretty-print things in a more intuitive
        # manner, we keep track of the order in which things were
        # added to this namespace, and print them out in the same
        # order.  Each item in this list is a tuple whose first
        # element is one of ['D', 'V', 'F', 'I'] (for definitions,
        # variables, from-as, and import-as statements), and whose
        # second element is a reference to the statement.
        #
        # Note: if an item is redefined, the order only depends on
        # where the item was FIRST defined, not the definition that
        # came last.
        #
        self.order_added = list()

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
        """

        if name in self.all_names:
            return False
        else:
            self.all_names.add(name)
            return True

    def add_local_var(self, name, ptree):
        if not self.check_dups(name, 'local-variable'):
            NodeError.warning_msg(
                    ptree, 'redefinition of variable [%s]' % name)
        else:
            self.order_added.append(('V', ptree))

        self.local_vars[name] = ptree

    def add_local_func(self, name, ptree):
        if not self.check_dups(name, 'local-function'):
            NodeError.warning_msg(
                    ptree, 'redefinition of function [%s]' % name)
        else:
            self.order_added.append(('D', ptree))

        self.local_defs[name] = ptree

    def add_from_as_stmnt(self, ptree):
        """
        Add a from-as statement to the list of statements seen.
        This DOES NOT update the namespace; use add_from_as()
        to do that
        """

        self.order_added.append(('F', ptree))

    def add_import_as_stmnt(self, ptree):
        """
        Add an import-as statement to the list of statements seen.
        This DOES NOT update the namespace; use add_import_as()
        to do that
        """

        self.order_added.append(('I', ptree))

    def add_from_as(self, module_name, sym_name, as_name=None):
        # print('SYM module [%s] name [%s]' % (module_name, sym_name))
        if not as_name:
            as_name = sym_name

        self.check_dups(as_name, 'from-as')

        path = resolve_path(module_name)
        if not path:
            raise ValueError('no module found for [%s]' % module_name)

        self.from_as[as_name] = (sym_name, path)

    def add_import_as(self, module_name, as_name=None, ptree=None):
        if not as_name:
            as_name = module_name

        self.check_dups(as_name, 'import-as')

        path = resolve_path(module_name)
        if not path:
            raise ValueError('no module found for [%s]' % module_name)

        self.import_as[as_name] = path

    def namespace2ast(self):
        """
        Create an AST representation of this namespace as
        a module, by making a list of the order_added AST
        elements and then constructing an ast.Module for
        them.

        NOTE: if the module is empty, then the qgl_fname
        of the root node of the module will not be assigned.
        TODO: it might be better to return None if the
        module is empty, rather than an empty module.
        """

        body = list()
        for stmnt_type, stmnt_value in self.order_added:
            body.append(stmnt_value)

        module = ast.Module(body=body)

        # if there are any elements at all, then set the modules
        # qgl_fname to the qgl_fname of the first element
        #
        if len(self.order_added) > 0:
            module.qgl_fname = self.order_added[0][1].qgl_fname

        return module

    def pretty_print(self):
        """
        Return a string representing the contents of this namespace,
        as Python3 code

        Doing this element by element (from order_added) adds
        an extra newline after each element, which looks better
        than converting the namespace back to a module (via
        namespace2ast) and then doing the pretty-printing on
        the entire module at once.
        """

        text = ''
        for item_type, item_value in self.order_added:
            if item_type in ['D', 'V', 'I', 'F']:
                text += pyqgl2.ast_util.ast2str(item_value)

        return text


class NameSpaces(object):

    # FIXME/TODO: this hardcoded path is bogus.  Need to find a
    # more general way to do this
    #
    IGNORE_MODULE_PATH_PREFIX = os.path.relpath(
            '/opt/local/Library/Frameworks/Python.framework')

    # maximum number of redirections per symbol.
    #
    # This number is guess; it seems reasonable.  Adjust as
    # appropriate.
    #
    MAX_DEPTH = 16

    def __init__(self, path, qglmain_name=None, text=None):

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

        if text:
            self.read_import_str(text, self.base_fname)
        else:
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

    def resolve_sym(self, path, name, depth=0):
        """
        Attempt to resolve the symbol with the given name within
        the namespace denoted by the given path
        """

        # keep a copy of the starting name and context,
        # before we start to chase it through other modules,
        # so we can print meaningful diagnostics
        #
        start_name = name
        start_path = path

        # This is a fairly awful loop, but it's not obvious how to
        # improve it.
        #
        # If depth is greater than self.MAX_DEPTH, assume that something
        # has gone wrong, and raise an error.  This probably means that
        # we're chasing our tail.
        #
        # If we can't find the matching namespace, something has
        # definitely gone wrong; raise an error.
        #
        # Try looking in the local namespace, with the following
        # precedence: local variables, local function defs, and
        # local aliases (created via from-as) for symbols that
        # may be elsewhere.  In the latter case, find the corresponding
        # namespace and search there.  This may require iteration
        # because the thing that's being aliased may itself be an alias,
        # ad nauseum.  (this could also be expressed recursively, but
        # then we'd lose start_name and start_path)
        #
        # If we can't find anything that matches in the local
        # namespace, then see if it's a reference to something
        # in another module (referenced by module name, not
        # "aliased" via from-as).  If so, recursively attempt
        # resolution relative to that namespace for each module
        # prefix.

        while True:
            # if the depth of the recursion is more than permitted,
            # assume that we have an infinite or goofy redirection loop
            #
            if depth > self.MAX_DEPTH:
                raise ValueError(
                        ('redirection loop detected for \'%s\' in \'%s\'' %
                            (start_name, start_path)))
                return None

            if path not in self.path2namespace:
                raise ValueError('cannot find namespace for \'%s\'' % path)

            namespace = self.path2namespace[path]

            if name in namespace.local_vars:
                return namespace.local_vars[name]
            elif name in namespace.local_defs:
                return namespace.local_defs[name]
            elif name in namespace.from_as:
                name, path = namespace.from_as[name]
                depth += 1
            else:
                # If it's not in any of the lists for this namespace
                # (not a local variable, not a local def, not something
                # imported via from-as) then maybe it's a reference
                # to a module element.  Bail out of this look to find
                # out.
                #
                break

        # If it's not a local symbol, or a symbol that's
        # imported to appear to be a local symbol, then
        # see if it appears to be a reference to a module.
        # If so, try finding it there, in that context
        # (possibly renamed with an import-as).

        name_components = name.split('.')

        for ind in range(len(name_components) - 1):
            prefix = '.'.join(name_components[:ind + 1])
            suffix = '.'.join(name_components[ind + 1:])

            if prefix in namespace.import_as:
                imported_module = namespace.import_as[prefix]
                return self.resolve_sym(imported_module, suffix, depth + 1)

        return None

    def returns_pulse(self, module_path, sym_name):
        sym = self.resolve_sym(module_path, sym_name)
        if not sym:
            return False
        else:
            return sym.qgl_return == QGL2.PULSE

    def read_import(self, path):
        """
        Recursively read the imports from the module at the given path
        """

        # TODO: error/warning/diagnostics

        if path in self.path2ast:
            print('NN Already in there [%s]' % path)
            return self.path2ast[path]

        if path.startswith(NameSpaces.IGNORE_MODULE_PATH_PREFIX):
            return None

        # TODO: this doesn't do anything graceful if the file
        # can't be opened, or doesn't exist, or anything else goes
        # wrong.  We just assume that Python will raise an exception
        # that includes a useful error message.  FIXME we should
        # be more proactive about making sure that the user
        # gets the info necessary to diagnose the problem.
        #
        text = open(path, 'r').read()

        return self.read_import_str(text, path)

    def read_import_str(self, text, path='<stdin>'):

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
                # print('NN ADDING import %s' % ast.dump(stmnt))
                self.add_import_as(namespace, stmnt)
            elif isinstance(stmnt, ast.ImportFrom):
                # print('NN ADDING import-from %s' % ast.dump(stmnt))
                self.add_from_as(namespace, stmnt.module, stmnt)
            # We're not doing module-level variables right now; no globals
            """
            elif isinstance(stmnt, ast.Assign):
                print('NN ASSIGN %s' % ast.dump(stmnt))
            """

        # print('NN NAMESPACE %s' % str(self.path2namespace))

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

        if not isinstance(node, ast.FunctionDef):
            print('NOT A FUNCTIONDEF %s' % ast.dump(node))
            return None

        if node.returns:
            ret = node.returns

            if isinstance(ret, ast.Name):
                if ret.id == QGL2.QBIT:
                    q_return = QGL2.QBIT
                elif ret.id == QGL2.CLASSICAL:
                    q_return = QGL2.CLASSICAL
                elif ret.id == QGL2.QBIT_LIST:
                    q_return = QGL2.QBIT_LIST
                elif ret.id == QGL2.PULSE:
                    q_return = QGL2.PULSE
                else:
                    NodeError.error_msg(node,
                            'unsupported return type [%s]' % ret.id)

        if node.args.args:
            for arg in node.args.args:
                # print('>> %s' % ast.dump(arg))

                name = arg.arg
                annotation = arg.annotation
                if not annotation:
                    q_args.append('%s:%s' % (name, QGL2.CLASSICAL))
                elif isinstance(annotation, ast.Name):
                    if annotation.id == QGL2.QBIT:
                        q_args.append('%s:%s' % (name, QGL2.QBIT))
                    elif annotation.id == QGL2.CLASSICAL:
                        q_args.append('%s:%s' % (name, QGL2.CLASSICAL))
                    elif annotation.id == QGL2.QBIT_LIST:
                        q_args.append('%s:%s' % (name, QGL2.QBIT_LIST))
                    elif annotation.id == QGL2.PULSE:
                        q_args.append('%s:%s' % (name, QGL2.PULSE))
                    else:
                        NodeError.error_msg(node,
                                ('unsupported parameter annotation [%s]' %
                                    annotation.id))
                else:
                    NodeError.error_msg(node,
                            'unsupported parameter annotation [%s]' %
                            ast.dump(annotation))

        # print('NN NAME %s (%s) -> %s' %
        #         (node.name, str(q_args), str(q_return)))

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

        # print('NNN module_name %s ofname %s' % (module_name, self.base_fname))

        qglmain = False
        qglfunc = False
        other_decorator = False

        if node.decorator_list:
            for dec in node.decorator_list:
                # print('NNN DECLIST %s %s' % (node.name, ast.dump(dec)))

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

        node.qgl_func = qglfunc
        node.qgl_main = qglmain

        # Only assign the qglmain at the root of the namespace
        # if we're in the base file
        #
        if qglmain and (module_name == self.base_fname):
            if self.qglmain:
                omain = self.qglmain

                # This is not an error; optimized versions of
                # the qglmain can be added without error
                #
                NodeError.diag_msg(
                        node, 'more than one %s function' % QGL2.QMAIN)
                NodeError.diag_msg(
                        node, 'previously defined %s:%d:%d' %
                        (omain.qgl_fname, omain.lineno, omain.col_offset))
            else:
                NodeError.diag_msg(
                        node, '%s declared as %s' % (node.name, QGL2.QMAIN))
                self.qglmain = node

    def add_import_as(self, namespace, stmnt):

        namespace.add_import_as_stmnt(stmnt)

        for imp in stmnt.names:
            subpath = resolve_path(imp.name)
            if subpath:
                namespace.add_import_as(imp.name, imp.asname)
                self.read_import(subpath)
            else:
                # print('NN IMPORTAS %s' % ast.dump(stmnt))
                NodeError.warning_msg(
                        stmnt, 'path to [%s] not found' % imp.name)

    def add_from_as(self, namespace, module_name, stmnt):

        namespace.add_from_as_stmnt(stmnt)

        subpath = resolve_path(module_name)
        if not subpath:
            NodeError.error_msg(
                    stmnt, 'path to [%s] not found' % module_name)
        else:
            self.read_import(subpath)

            for imp in stmnt.names:
                if imp.name == '*':
                    NodeError.warning_msg(stmnt,
                            ('deprecated wildcard import from [%s]' %
                                module_name))
                    self.add_from_wildcard(namespace, module_name, module_name)
                else:
                    namespace.add_from_as(module_name, imp.name, imp.asname)

    def add_from_wildcard(self, namespace, module_name, from_name):

        subpath = resolve_path(module_name)

        # TODO: check that subpath is there
        alt_namespace = self.path2namespace[subpath]

        for sym in alt_namespace.all_names:
            namespace.add_from_as(module_name, sym)

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
