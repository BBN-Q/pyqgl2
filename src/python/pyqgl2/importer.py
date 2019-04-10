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
import inspect
import os
import sys

from pyqgl2.ast_util import NodeError
from pyqgl2.lang import QGL2

import pyqgl2

SYS_PATH_PREFIX = None

def find_sys_path_prefix():
    """
    Find the prefix of the path to the "system" libraries,
    which we want to exclude from importing and searching
    for QGL stuff.

    Where these are located depends on where Python was
    installed on the local system (and which version of
    Python, etc).  The heuristic we use is to search through
    the include path for 'ast' and assume that the path
    we has the prefix we want to omit.

    This is a hack.  In Python3, modules can be loaded
    directly out of zip files, in which case they don't
    have a "file".  We use 'ast' because it typically does,
    but there's no guarantee that this will work in
    all cases.
    """

    global SYS_PATH_PREFIX

    if SYS_PATH_PREFIX:
        return SYS_PATH_PREFIX

    try:
        path = inspect.getfile(ast)
    except TypeError as exc:
        NodeError.fatal_msg(None, 'cannot find path to system modules')

    relpath = os.path.relpath(path)

    path_prefix = relpath.rpartition(os.sep)[0]

    SYS_PATH_PREFIX = path_prefix

    return path_prefix

def is_system_file(path):
    relpath = os.path.relpath(path)

    return relpath.startswith(find_sys_path_prefix())

def resolve_path(name):
    """
    Find the path to the file that would be imported for the
    given module name, if any.

    Note that paths are used as the keys for several data
    structures

    Returns the relative path to the file, if the file resolved,
    or None if the name cannot be resolved at all.
    """

    # At most of one of these will resolve correctly; either
    # it's a directory (package) or a file (module)
    #
    name_to_fpath = os.sep.join(name.split('.')) + '.py'
    name_to_dpath = os.path.join(os.sep.join(name.split('.')), '__init__.py')

    # loop through sys.path.
    #
    # if all else fails, try using the current directory
    # (I am ambivalent about this)
    #
    for dirpath in sys.path + ['.']:
        if not dirpath:
            continue
        dirpath = os.path.relpath(dirpath)

        fpath = os.path.join(dirpath, name_to_fpath)
        dpath = os.path.join(dirpath, name_to_dpath)

        # We don't check whether we can read the file.  It's
        # not clear from the spec whether the Python interpreter
        # checks this before trying to use it.  TODO: test
        #
        if os.path.isfile(fpath):
            candidate = fpath
        elif os.path.isfile(dpath):
            candidate = dpath
        else:
            candidate = None

        if candidate:
            return os.path.relpath(candidate)

    return None

def resolve_dpath(name):
    """
    Like resolve_path, but finds a directory with the given name.

    In recent versions of Python, it is legal to import a name
    from a directory (not a package) as long as the name is
    a package or module.  This function finds a directory that
    matches the given name, or None if there are none to find.

    Does not handle relative paths; these are handled elsewhere.
    """

    name_to_path = os.sep.join(name.split('.'))

    for dirpath in sys.path + ['.']:
        dirpath = os.path.relpath(dirpath)

        candidate = os.path.join(dirpath, name_to_path)

        if os.path.isdir(candidate):
            return os.path.relpath(candidate)

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
        NodeError.warning_msg(node,
                'unexpected failure to resolve [%s]' % ast.dump(node))
        return None

def add_import_from_as(importer, namespace_name, module_name,
        symbol_name, as_name=None):
    """
    Add a from-as import, as if it had appeared in the module with
    the given namespace_name, iff the apparent name (either the symbol_name,
    or the as_name if the the as_name is not None) is not already defined
    in the corresponding namespace.

    For example, if you wanted to add the equivalent of

        from foo.bar import qux as baz

    to the module with the namespace named 'fred.barney' then you
    could use

        add_import(importer, 'fred.barney', 'foo.bar', 'qux', 'baz')

    Returns True if the symbol already exists or is successfully imported,
    False otherwise
    """

    assert isinstance(importer, NameSpaces)
    assert isinstance(namespace_name, str)
    assert isinstance(module_name, str)
    assert isinstance(symbol_name, str)
    assert (as_name is None) or isinstance(as_name, str)

    if as_name:
        apparent_name = as_name
    else:
        apparent_name = symbol_name

    if not importer.resolve_sym(namespace_name, apparent_name):
        imp_stmnt = ast.ImportFrom(module=module_name,
                names=[ast.alias(name=symbol_name, asname=as_name)],
                level=0)

        importer.add_from_as(
                importer.path2namespace[namespace_name],
                module_name, imp_stmnt)

    if importer.resolve_sym(namespace_name, apparent_name):
        return True
    else:
        return False


class NameSpace(object):
    """
    Manage the namespace for a single file
    """

    def __init__(self, path, ptree=None):
        """
        path is the path to the Python source of the module

        ptree is the AST node that caused the NameSpace to be
        created (typically an import statement); it may be
        omitted.  It is currently used only to help create
        more meaningful diagnostic messages when something
        fails
        """

        # for diagnostics
        #
        self.path = path

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

        # We do a "real" import of the file, using exec, using
        # the native_globals as the globals().  This means that
        # we can capture the effect of doing an import on a real
        # Python processing, without muddying up our own namespace
        # with the results.  Then we keep the native_globals so
        # that if we later need to evaluate expressions or
        # statements in that context, we have it ready to go.
        #
        self.native_globals = dict()
        # don't treat this like a __main__
        self.native_globals['__name__'] = 'not_main'
        # make sure the __file__ is set properly
        # self.native_globals['__file__'] = path

        self.native_load(ptree)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return ('local %s from_as %s import_as %s' %
                (str(self.local_defs), str(self.from_as), str(self.import_as)))

    def native_load(self, node=None):
        """
        Exec the entire text of the file, so that the native_globals
        will be properly initialized
        """

        try:
            fin = open(self.path, 'r')
            text = fin.read()
            fin.close()
        except BaseException as exc:
            NodeError.error_msg(None,
                    'read of [%s] failed: %s' % (self.path, str(exc)))
            return False

        try:
            exec(text, self.native_globals)
            return True
        except BaseException as exc:
            NodeError.error_msg(None,
                    'import of [%s] failed: %s' % (self.path, str(exc)))
            return False
        return True

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

    def add_from_as_path(self, path, sym_name, as_name=None):
        # print('SYM module [%s] name [%s]' % (module_name, sym_name))
        if not as_name:
            as_name = sym_name

        self.check_dups(as_name, 'from-as')

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

        if not is_system_file(path):
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

    def native_import(self, text, node):
        """
        Do a "native import", updating self.native_globals
        with the results.

        This can be ugly if the import executes arbitrary code (i.e.
        prints things on the screen, or futzes with something else).

        The text must be an import statement, or sequence of
        import statements (ast2str turns a single statement with
        a list of symbol clauses into a list of statements)
        i.e. "from foo import bar as baz" or "from whatever import *"
        or "import something"

        The node is used to create meaningful diagnostic or
        error messages, and must be provided.

        Returns True if successful, False otherwise.
        """

        # A hack to avoid doing imports on "synthesized" imports
        # that don't have line numbers in the original source code
        #
        if (not node) or (not hasattr(node, 'lineno')):
            return

        try:
            exec(text, self.native_globals)
            return True
        except BaseException as exc:
            if node:
                caller_fname = node.qgl_fname
            else:
                caller_fname = '<unknown>'
            NodeError.error_msg(node,
                    'in %s [%s] failed: %s' % (caller_fname, text, str(exc)))
            return False

    def native_single(self, stmnt, local_variables=None):
        """
        Evaluate a single statement (such as an assignment statement)
        for effect, in the context of (and modifying) the local_variables)

        A wrapper around native_eval that permits assignment statements,
        which are not permitted in expressions.
        """

        success, _val = self.native_eval(stmnt,
                local_variables=local_variables, mode='single')
        return success

    def native_exec(self, stmnt, local_variables=None):

        success, _val = self.native_eval(stmnt,
                local_variables=local_variables, mode='exec')
        return success

    def native_eval(self, expr, local_variables=None, mode='eval'):
        """
        Evaluate the given expr, which may be an expression or a
        statement represented by an AST node or a text string.
        If mode is 'eval', then the expr must be an expression,
        but if it is 'exec' then it may be a statement.

        If local_variables is not None, it is assumed to reference
        a dictionary containing local bindings.  It should NOT
        be a reference to the global bindings (either for this
        namespace, or any other global bindings).

        Returns (success, value), where success indicates whether
        the evaluation succeeded or failed, and value is the value
        of the expression.  The process of evaluation the expression
        may also modify bindings in local_variables,

        Note that if the evaluation of the expr raises an
        exception, this exception will be caught and the result
        will be treated as failure (even if the intent of the
        expression was to raise an exception).  QGL2 doesn't
        understand exceptions.

        NOTE: this evaluation is not safe, and may damage the
        environment of the caller.  There is no safeguard against
        this right now.
        """

        if (not isinstance(expr, str)) and (not isinstance(expr, ast.AST)):
            print('INVALID EXPR type %s' % str(type(expr)))
            return False, None

        # If we get AST, then there are many variations on what
        # we could get (it could look like an Expr, or an Expression,
        # or a Module, etc.  By converting the AST to a text string,
        # this removes all of the ambiguity and lets us parse the
        # program again, in the local context.
        #
        # This is inefficient for the computer (to keep going back and
        # forth between text and parse trees) but efficient for the
        # implementer.
        #
        if isinstance(expr, ast.AST):
            expr_str = pyqgl2.ast_util.ast2str(expr)
        else:
            expr_str = expr

        try:
            final_expr = compile(expr_str, '<nofile>', mode=mode)
        except SyntaxError as exc:
            print('Syntax error in native_eval: %s' % str(exc))
            return False, None
        except BaseException as exc:
            print('Error in native_eval: %s' % str(exc))
            return False, None

        try:
            if local_variables is None:
                local_variables = dict()

            # global_variables = dict.copy(self.native_globals)

            # print('EXPR %s' % expr_str.strip())
            val = eval(final_expr, self.native_globals, local_variables)
            return True, val
        except BaseException as exc:
            # If the expr was AST and came from the preprocessor,
            # try to format the error message accordingly
            #
            # Otherwise just attempt to print something meaningful
            #
            if isinstance(expr, ast.AST) and hasattr(expr, 'qgl_fname'):
                NodeError.error_msg(expr,
                        ('ast eval failure [%s]: type %s %s' %
                            (expr_str.strip(), str(type(exc)), str(exc))))
            else:
                print('eval failure [%s]: %s' % (expr_str.strip(), str(exc)))
            return False, None


class NameSpaces(object):

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
        if not path or path == '<stdin>':
            self.base_fname = '<stdin>'
        else:
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
                NodeError.error_msg(None,
                        'no definition for qglmain [%s]' % qglmain_name)
            elif not qglmain_def.qgl_func:
                NodeError.error_msg(None,
                        'qglmain [%s] not declared QGL' % qglmain_name)
            else:
                self.qglmain = qglmain_def
                qglmain_def.qgl_main = True

        if self.qglmain:
            NodeError.diag_msg(None,
                    'using [%s] as qglmain' % self.qglmain.name)
        else:
            NodeError.warning_msg(None,
                    'warning: no qglmain declared or chosen')

        # This is a hack to make sure that the base file
        # is read in as a "native import".  Since there isn't
        # an explicit "import" of this file anywhere, we don't
        # have an AST node that contains the code for this import.
        # We can't use None, because this importer uses this as
        # a sentinel value, so we use self.qgl2main.  This is
        # bogus -- we should make a fake node for this purpose
        # FIXME

        fin = open(self.base_fname, 'r')
        text = fin.read()
        fin.close()

        namespace = self.path2namespace[self.base_fname]
        namespace.native_import(text, self.qglmain)

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
                # to a module element.  Bail out of this loop to find
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
            return self.path2ast[path]

        # TODO: this doesn't do anything graceful if the file
        # can't be opened, or doesn't exist, or anything else goes
        # wrong.  We just assume that Python will raise an exception
        # that includes a useful error message.  FIXME we should
        # be more proactive about making sure that the user
        # gets the info necessary to diagnose the problem.
        #

        try:
            fin = open(path, 'r')
            text = fin.read()
            fin.close()
        except BaseException as exc:
            NodeError.fatal_msg(
                    None, 'cannot open [%s]: %s' % (path, str(exc)))
            return None

        try:
            return self.read_import_str(text, path)
        except SyntaxError as exc:
            NodeError.fatal_msg(
                    None, 'failed to import [%s]: %s' % (path, str(exc)))
            return None


    def read_import_str(self, text, path='<stdin>', module_name='__main__'):

        ptree = ast.parse(text, mode='exec')

        self.path2ast[path] = ptree

        # label each node with the name of the input file;
        # this will make error messages that reference these
        # notes much more readable
        #
        for node in ast.walk(ptree):
            node.qgl_fname = path
            node.qgl_modname = module_name

        # The preprocessor will ignore any imports that are not
        # at the "top level" (imports that happen conditionally,
        # or when a function is executed for the first time, etc)
        # because it can't figure out if/when these imports would
        # occur, and it only understands imports that occur before
        # the execution of any other statements of the program.
        #
        # Therefore warn the programmer that any such detected
        # imports will be ignored.
        #
        # TODO: we don't make any attempt to find calls to
        # __import__() or importlib.import_module().  The
        # preprocessor always ignores these, without warning.
        #
        for node in ast.walk(ptree):
            if ((isinstance(node, ast.Import) or
                    isinstance(node, ast.ImportFrom)) and
                    (node.col_offset != 0)):
                NodeError.warning_msg(node,
                        ('conditional/runtime import [%s] ignored by pyqgl2' %
                            pyqgl2.ast_util.ast2str(node).strip()))

        # Populate the namespace
        #
        namespace = NameSpace(path, ptree=ptree)
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
            NodeError.warning_msg(node, 'unexpected None node')
            return None

        if not isinstance(node, ast.FunctionDef):
            NodeError.warning_msg(node,
                    'expected a FunctionDef, got [%s]' % ast.dump(node))
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
                elif ret.id == QGL2.CONTROL:
                    q_return = QGL2.CONTROL
                elif ret.id == QGL2.SEQUENCE:
                    q_return = QGL2.SEQUENCE
                else:
                    NodeError.error_msg(node,
                            'unsupported return type [%s]' % ret.id)

        # FIXME: What about kwonlyargs? or storing the defaults?
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
                    elif annotation.id == QGL2.CONTROL:
                        q_args.append('%s:%s' % (name, QGL2.CONTROL))
                    elif annotation.id == QGL2.SEQUENCE:
                        q_args.append('%s:%s' % (name, QGL2.SEQUENCE))
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

    def find_stub_import(self, decnode, funcname):
        """
        Find the import info encoded in a stub declaration

        TODO: doesn't do anything useful with errors/bad input
        """

        if not isinstance(decnode, ast.Call):
            NodeError.fatal_msg(decnode,
                    'bad use of find_stub_import [%s]' % ast.dump(decnode))

        args = decnode.args
        n_args = len(args)

        from_name = None
        orig_name = None

        if n_args == 0:
            # TODO: should complain
            pass

        if n_args > 0:
            if not isinstance(args[0], ast.Str):
                NodeError.error_msg(decnode,
                        'qgl2stub arg[0] must be str [%s]' % ast.dump(args[0]))
            else:
                from_name = args[0].s

        if n_args > 1:
            if not isinstance(args[1], ast.Str):
                NodeError.error_msg(decnode,
                        'qgl2stub arg[1] must be str [%s]' % ast.dump(args[1]))
            else:
                orig_name = args[1].s

        if n_args > 2:
            # TODO: should complain
            pass

        return (funcname, from_name, orig_name)

    def add_func_decorators(self, module_name, node):

        # print('NNN module_name %s ofname %s' % (module_name, self.base_fname))

        qglmain = False
        qglfunc = False
        other_decorator = False
        qglstub = False # A stub for a QGL1 function; check args but do not inline
        qglstub_import = False
        qglmeas = False # A QGL measurement

        if node.decorator_list:
            for dec in node.decorator_list:
                # qglmain implies qglfunc, but it's permitted to
                # have both
                #
                if isinstance(dec, ast.Name) and (dec.id == QGL2.QMAIN):
                    qglfunc = True
                    qglmain = True
                elif isinstance(dec, ast.Name) and (dec.id == QGL2.QSTUB):
                    # A stub for a QGL1 function; check args but do not inline
                    qglfunc = True
                    qglstub = True
                    NodeError.warning_msg(node,
                            ('old-style stub for [%s]: no import info' %
                                node.name))
                elif (isinstance(dec, ast.Call) and
                        isinstance(dec.func, ast.Name) and
                        dec.func.id == QGL2.QSTUB):
                    qglfunc = True
                    qglstub = True
                    qglstub_import = self.find_stub_import(dec, node.name)
                elif (isinstance(dec, ast.Call) and
                        isinstance(dec.func, ast.Name) and
                        dec.func.id == QGL2.QMEAS):
                    qglfunc = True
                    qglstub = True
                    qglmeas = True
                    qglstub_import = self.find_stub_import(dec, node.name)

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
        # A stub for a QGL1 function; check args but do not inline
        node.qgl_stub = qglstub
        node.qgl_meas = qglmeas
        node.qgl_main = qglmain
        node.qgl_stub_import = qglstub_import

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

        namespace.native_import(pyqgl2.ast_util.ast2str(stmnt), stmnt)

        namespace.add_import_as_stmnt(stmnt)

        for imp in stmnt.names:
            subpath = resolve_path(imp.name)
            if not subpath:
                NodeError.warning_msg(
                        stmnt, 'path to [%s] not found' % imp.name)
            elif is_system_file(subpath):
                continue
            else:
                namespace.add_import_as(imp.name, imp.asname)
                self.read_import(subpath)

    def add_from_as(self, namespace, module_name, stmnt):
        """
        Process a "from import as" statement (where the "as" is
        optional).

        The rules for how this works in Python are complicated,
        not particularly well specified (from the docs I can find),
        and more than we're attempting to do.  Here's what we do:

        Given a statement with one of the following forms:

            from X import A as Z
            from X import A, B
            from X import *

        X is referred to here as the module name, but it is not
        required (as of Python 3.4) to refer to a module; it may
        refer to a package, or (as of 3.4) a directory containing
        other packages or modules but is not itself a package.

        Note: it is not legal for A to be a compound thing, i.e.
        "from os import path.sep" is invalid syntax.

        After converting X from Python notation (including relative
        paths) into a file system path XP, we check to see whether
        it resolves to a module (with name XP + ".py"), or a package
        (with name XP + '/__init__.py') or a directory (with name XP).

        In Python 3.4/3.5, there is a new feature of being able
        to do a from-import of a module from a directory, i.e.

            from X import A

        where A is a module, rather than a symbol inside module or
        package X.  We DO NOT support this feature yet.

        """

        # setup the namespace for this module
        # NOTE: this is incomplete: it only sets up the specific
        # name, and may do so repeatedly.
        # TODO: We should only do this once
        # TODO: and we should import the entire namespace so that
        # local functions can access local definitions and
        # functions that are otherwise private
        #
        namespace.native_import(pyqgl2.ast_util.ast2str(stmnt), stmnt)

        namespace.add_from_as_stmnt(stmnt)

        # print('NX orig statement [%s]' % ast.dump(stmnt))
        # print('NX orig statement [%s]' %
        #         pyqgl2.ast_util.ast2str(stmnt).strip())

        # placeholder
        subpath = None

        if stmnt.level > 0:
            # Deal with relative imports: these have a level of 1
            # or higher
            #
            # Find the directory by peeling the last component off
            # of stmnt.qgl_fname and keeping the rest.
            #
            # Then append the right number of '..' components (level - 1)
            # to either look in the same directory, or a parent directory.
            # The resulting path is hideous and non-canonical, but we'll
            # fix that later.
            #
            # Finally, add the relative component (after translating it
            # from Python notation to path notation, and adding the
            # suffix).
            #
            dir_name = stmnt.qgl_fname.rpartition(os.sep)[0]

            # If the relative path is for a parent directory, add
            # the proper number of '..' components.  A single '.',
            # however, represents this directory.
            #
            if stmnt.level > 1:
                dir_name += os.sep + os.sep.join(['..'] * (stmnt.level - 1))

                # We're going to convert the entire path to a relative path
                # later, but doing it for the directory prefix makes things
                # more legible while debugging
                #
                dir_name = os.path.relpath(dir_name)

            # if there's a module name, prepare to test whether it's
            # a file or a directory.  If there's not then the dir_name
            # is the dpath, and there is no fpath
            #
            if module_name:
                mod_path = os.sep.join(module_name.split('.'))
                from_path = os.path.join(dir_name, mod_path)
            else:
                from_path = dir_name

            # Now figure out what kind of thing is at the end of that
            # path: a module, a package, or a directory:

            module_path = from_path + '.py'
            package_path = os.path.join(from_path, '__init__.py')
            dir_path = from_path

            if os.path.isfile(module_path):
                subpath = module_path
            elif os.path.isfile(package_path):
                subpath = package_path
            elif os.path.isdir(dir_path):
                subpath = from_path

            # Since we don't know what our own module name is,
            # we can't figure out the "full" name of the relatively
            # imported module.  FIXME
            #
            full_module_name = None
            NodeError.warning_msg(stmnt,
                    ('cannot evaluate exprs in a relative import [%s]' %
                        module_name))

        else:
            # use normal resolution to find the location of module
            #
            subpath = resolve_path(module_name)
            full_module_name = module_name

        # There are a lot of reasons why we might not be able
        # to resolve a module name; it could be in a binary file
        # or a zip file, or obscured in some other way, so that
        # the ordinary Python interpreter can find it but we cannot.
        # So we can't treat this as an error, even though it might
        # be one.
        #
        if subpath is None:
            NodeError.diag_msg(
                    stmnt, ('path to [%s%s] not found' %
                        ('.' * stmnt.level, module_name)))
        elif is_system_file(subpath):
            NodeError.diag_msg(
                    stmnt, ('import of [%s%s] ignored' %
                        ('.' * stmnt.level, module_name)))
        else:
            self.read_import(subpath)

            for imp in stmnt.names:
                if imp.name == '*':
                    NodeError.warning_msg(stmnt,
                            ('deprecated wildcard import from [%s]' %
                                module_name))
                    self.add_from_wildcard(namespace, subpath, module_name)

                    if full_module_name:
                        namespace.native_import(
                                ('from %s import *' % full_module_name), stmnt)
                else:
                    namespace.add_from_as_path(subpath, imp.name, imp.asname)

                    if full_module_name:
                        symname = imp.name
                        if imp.asname:
                            symname += ' %s' % imp.asname
                        namespace.native_import(
                                ('from %s import %s' %
                                    (full_module_name, symname)),
                                stmnt)

    def add_from_wildcard(self, namespace, path, from_name):

        alt_namespace = self.path2namespace[path]

        for sym in alt_namespace.all_names:
            namespace.add_from_as_path(path, sym)

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
