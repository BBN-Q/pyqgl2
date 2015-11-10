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
from pyqgl2.ast_util import NodeError
from pyqgl2.ast_util import NodeTransformerWithFname
from pyqgl2.lang import QGL2

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

    def __init__(self):
        self.local_defs = dict()
        self.from_as = dict()
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
        if name in self.all_names:
            raise ValueError(
                    ('symbol [%s] multiply defined (%s)in namespace' %
                        (name, def_type)))
        else:
            self.all_names.add(name)

    def add_local(self, name, ptree):
        self.check_dups(name, 'local')
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

class SymbolDefinition(object):
    """
    A way to find the definition of a symbol (typically a function
    definition) that may be defined locally or defined elsewhere and
    imported into the local module (possibly via several levels of
    indirection)
    """

    """
    Examples:

        import x

            for each symbol y in x:
                orig_name = y
                ptree = parse tree of x.y
                module_prefix = x
                local_name = x.y

        import x as z

            for each symbol y in x:
                orig_name = y
                ptree = parse tree of x.y
                module_prefix = x
                local_name = z.y

        from x import y

            orig_name = y
            ptree = parse tree of x.y
            module_prefix = x
            local_name = y

        from x import y as z

            orig_name = y
            ptree = parse tree of x.y
            module_prefix = x
            local_name = z
    """

    def __init__(self, orig_name, ptree, is_local,
            module_prefix=None, local_name=None):

        self.orig_name = orig_name
        self.ptree = ptree
        self.module_prefix = module_prefix
        self.local_name = orig_name
        self.is_local = is_local


    @staticmethod
    def local_sym(name, ptree):
        """
        Factory method for a locally-defined symbol
        """

        return SymbolDefinition(name, ptree, True, None, name)

    @staticmethod
    def do_import(orig_name, ptree, module_prefix):
        """
        Factory method for a symbol imported with a bare "import"
        """

        return SymbolDefinition(orig_name, ptree, False, module_prefix,
                '%s.%s' % (module_prefix, orig_name))

    @staticmethod
    def do_import_as(orig_name, ptree, module_prefix, as_name):
        """
        Factory method for a symbol imported with an "import-as"
        """

        return SymbolDefinition(orig_name, ptree, False, module_prefix,
                '%s.%s' % (as_name, orig_name))

    @staticmethod
    def do_from(orig_name, ptree, module_prefix):
        """
        Factory method for a symbol imported with a "from" statement
        """

        return SymbolDefinition(orig_name, ptree, False,
                module_prefix, orig_name)

    @staticmethod
    def do_from_as(orig_name, ptree, module_prefix, as_name):
        """
        Factory method for a symbol imported with a "from-as" statement
        """

        return SymbolDefinition(orig_name, ptree, False,
                module_prefix, as_name)


class NameSpaces(object):

    def __init__(self, path):

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

        self.read_import(self.base_fname)

    def resolve_sym(self, path, name):
        print('NNN TRYING TO RESOLVE %s in %s' % (name, path))

        if path not in self.path2namespace:
            raise ValueError('cannot find namespace for [%s]' % path)

        namespace = self.path2namespace[path]

        if name in namespace.local_defs:
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
                self.add_import_as(namespace, stmnt.names)
            elif isinstance(stmnt, ast.ImportFrom):
                print('NN ADDING import-from %s' % ast.dump(stmnt))
                self.add_from_as(namespace, stmnt.module, stmnt.names)

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
                    print(
                            'unsupported return type [%s]' % ast.dump(ret))

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

        # node.qgl2_args = q_args
        # node.qgl2_return = q_return

        print('NN NAME %s (%s) -> %s' %
                (node.name, str(q_args), str(q_return)))

        return (q_args, q_return)

    def add_function(self, namespace, name, ptree):
        """
        Add a locally-defined function to the local namespace
        """

        # TODO; check whether the name is already defined.
        # Chide the user about multiple definitions

        namespace.add_local(ptree.name, ptree)
        print('NN TODO: Annotate the function')
        print('NN ADDING function %s' % ast.dump(ptree))

        arg_types, return_type = self.find_type_decl(ptree)

        print('NN %s arg_types %s' % (ptree.name, arg_types))
        print('NN %s return_type %s' % (ptree.name, return_type))

        ptree.qgl_args = arg_types
        ptree.qgl_return = return_type

    def add_import_as(self, namespace, names):

        for imp in names:
            subpath = resolve_path(imp.name)
            if subpath:
                namespace.add_import_as(imp.name, imp.asname)
                self.read_import(subpath)
            else:
                NodeError.error_msg(stmnt,
                        ('path to [%s] could not be found' %
                                imp.name))

    def add_from_as(self, namespace, module_name, names):

        subpath = resolve_path(module_name)
        if not subpath:
            NodeError.error_msg(stmnt,
                    ('path to [%s] could not be found' % module_name))
        else:
            self.read_import(subpath)

            for imp in names:
                namespace.add_from_as(module_name, imp.name, imp.asname)


    def add_import_from(self, namespace, ):

        # namespace[name] = SymbolDefinition.do_import_from(name, ptree)
        pass



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
        super(Importer, self).__init__()

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

        # maps strings (names in the local namespace) to
        # ImportedSymbol instances
        #
        self.name2def = dict()

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

        if sym_prefix == '':
            if self.path2func_defs[context_name][sym_suffix]:
                return (context_name, sym_prefix, sym_suffix,
                        self.path2func_defs[context_name][sym_suffix])

        print('SEARCHING CONTEXT_NAME [%s] %s' %
                (context_name, str(self.path2context)))

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

        # If the as_name isn't None, then check that it's
        # not already in use in this context
        #
        # Even though it's fatal if we reuse a namespace,
        # we don't halt immediately, so we can do additional
        # checking before giving up
        #
        # If as_name is None, then this isn't an ordinary
        # import; it's an import-from.  In this case, we
        # don't update the namespace with the module symbol;
        # we update the namespace later with the names of
        # the specified symbols.
        #
        if as_name:
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

            print('AST MOD %s' % ast.dump(ptree))
            for x in ptree.body:
                print('AST MOD X %s' % ast.dump(x))

            # label each node with the name of the input file;
            # this will make error messages that reference these
            # notes much more readable
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

    def _qbit_decl(self, node):
        """ Copied from check_qbit.  Both need to be refactored. """

        q_args = list()
        q_return = None

        if node is None:
            print('NODE IS NONE')

        if type(node) != ast.FunctionDef:
            print('NOT A FUNCTIONDEF %s' % ast.dump(node))
            return None

        if node.returns:
            ret = node.returns

            # It would be nice to be able to return a qbit
            # tuple, maybe.
            #
            if (type(ret) == ast.Str) and (ret.s == 'qbit'):
                q_return = 'qbit'
            elif (type(ret) == ast.Str) and (ret.s == 'classical'):
                q_return = 'classical'
            elif (type(ret) == ast.Name) and (ret.id == 'qbit'):
                self.warning_msg(node,
                        'use of \'qbit\' symbol is deprecated')
                q_return = 'qbit'
            elif (type(ret) == ast.Name) and (ret.id == 'classical'):
                self.warning_msg(node,
                        'use of \'classical\' symbol is deprecated')
                q_return = 'classical'
            else:
                self.error_msg(node,
                        'unsupported return annotation [%s]' % ast.dump(ret))

        if node.args.args:
            for arg in node.args.args:
                # print('>> %s' % ast.dump(arg))

                name = arg.arg
                annotation = arg.annotation
                if not annotation:
                    q_args.append('%s:classical' % name)
                    continue

                if type(annotation) == ast.Name:
                    if annotation.id == 'qbit':
                        q_args.append('%s:qbit' % name)
                    elif annotation.id == 'classical':
                        q_args.append('%s:classical' % name)
                    else:
                        self.error_msg(node,
                                'unsupported parameter annotation [%s]' %
                                annotation.id)
                elif type(annotation) == ast.Str:
                    if annotation.s == 'qbit':
                        q_args.append('%s:qbit' % name)
                    elif annotation.s == 'classical':
                        q_args.append('%s:classical' % name)
                    else:
                        self.error_msg(node,
                                'unsupported parameter annotation [%s]' %
                                annotation.s)
                else:
                    self.error_msg(node,
                            'unsupported parameter annotation [%s]' %
                            ast.dump(annotation))

        node.q_args = q_args
        node.q_return = q_return

        return q_args

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
                print('HYE')
                path = self.resolve_path(stmnt.module)
                if not path:
                    self.error_msg(stmnt,
                            'path to [%s] could not be found' % stmnt.module)
                    continue

                relpath = os.path.relpath(path)
                # Give it a bogus asname to mask it from the namespace?
                #
                # self.do_import(stmnt, path, imp.name, imp.asname)
                self.do_import(stmnt, relpath, None, None)
                print('>> PATH2FUNC_DEFS %s %s' %
                        (relpath, str(self.path2func_defs)))
                func_defs = self.path2func_defs[relpath]

                for imp in stmnt.names:
                    if not imp.asname:
                        imp.asname = imp.name

                    print('>> ImportFrom: from %s import %s as %s' %
                            (str(relpath), imp.name, str(imp.asname)))

                    if imp.name not in func_defs:
                        self.error_msg(stmnt,
                                ('function [%s] not found in %s' %
                                    imp.name, stmnt.module))
                        continue

                    print('>> FOUND %s as %s' %
                            (imp.name, str(func_defs[imp.name])))

                    thispath = stmnt.qgl_fname
                    self.path2func_defs[thispath][imp.asname] = \
                            func_defs[imp.name]

                    print('>> DONE %s' % self.path2func_defs)

                # self.error_msg(stmnt, 'import-from unsupported')
                print('DEFS: %s' % self.path2func_defs)

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
            print('RETURN %s' % ast.dump(ret_type))
        else:
            ret_type = None

        #
        # This is a bit of a hack.  If the return type is an
        # ast.Name, and has an id that's in self.PULSE_TYPES, then return
        # the id string.  Otherwise, return an AST.
        #
        if (type(ret_type) == ast.Str) and (ret_type.s in self.PULSE_TYPES):
            ret_type = ret_type.s

        # In order to be compatible with ordinary python3, we can't
        # use arbitrary symbols; we need to use literals.  Therefore
        # this is commented out until we decide how much of Python3
        # compatibility we want to preserve.
        #
        # if (type(ret_type) == ast.Name) and (ret_type.id in self.PULSE_TYPES):
        #     ret_type = ret_type.id

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
        if NodeError.MAX_ERR_LEVEL >= NodeError.NODE_ERROR_ERROR:
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

        # print('X a.foo %s' % str(importer.resolve_sym('x.py', 'a.foo')))
        # print('X b.bbb %s' % str(importer.resolve_sym('x.py', 'B.bbb')))

        # print('Y a.foo %s' % str(importer.is_pulse('x.py', 'a.foo')))
        # print('Y b.bbb %s' % str(importer.is_pulse('x.py', 'B.bbb')))

    ff = NameSpaces(sys.argv[1])
    print('Find B.bbb %s' % ast.dump(ff.resolve_sym(sys.argv[1], 'B.bbb')))
    print('Find cc %s' % ast.dump(ff.resolve_sym(sys.argv[1], 'cc')))

    preprocess(sys.argv[1])
