#!/usr/bin/env python3
#
# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import ast
import os
import sys

from copy import deepcopy

# Find the directory that this executable lives in;
# munge the path to look within the parent module
#
if __name__ == '__main__':
    DIRNAME = os.path.normpath(
            os.path.abspath(os.path.dirname(sys.argv[0]) or '.'))
    sys.path.append(os.path.normpath(os.path.join(DIRNAME, '..')))

import pyqgl2.importer

from pyqgl2.ast_util import NodeError
from pyqgl2.ast_util import NodeTransformerWithFname
from pyqgl2.ast_util import NodeVisitorWithFname
from pyqgl2.check_symtab import CheckSymtab
from pyqgl2.check_qbit import CheckType
from pyqgl2.check_waveforms import CheckWaveforms
from pyqgl2.importer import NameSpaces
from pyqgl2.lang import QGL2

class SubstituteChannel(NodeTransformerWithFname):

    # globally-defined qbits
    #
    GLOBAL_QBITS = {
    }

    BUILTIN_FUNCS = [
            'X90', 'X180',
            'Y90', 'Y180',
            'Z90', 'Z180',
            'UTheta'
    ]

    def __init__(self, fname, qbit_bindings, func_defs, importer=None):
        super(SubstituteChannel, self).__init__()

        self.qbit_map = {name:chan_no for (name, chan_no) in qbit_bindings}
        self.func_defs = func_defs
        self.importer = importer

        print('QBIT MAP %s' % self.qbit_map)

    def visit_Name(self, node):
        print('VISITING NAME %s' % ast.dump(node))

        if node.id in self.qbit_map:
            new_id = self.qbit_map[node.id]
            print('CHANGING %s to %s' % (node.id, new_id))
            node.id = new_id
        else:
            print('QBIT NOT CHANGING NAME %s' % node.id)

        return node

    def is_qbit_creation(self, node):
        """
        Return True if the node is a call to a Qbit creation
        method (QGL2.QBIT_ALLOC), False otherwise

        Because of the way the namespace is altered by
        imports, the only way to know whether the call is to
        a Qbit creation method is to completely resolve the
        name of the method being called: the name of the
        method that appears in the call is only the start of
        this process.
        """

        # If it's not a Call at all, then it's certainly
        # not a call to any method that binds a qbit to
        # a channel
        #
        if not isinstance(node, ast.Call):
            return False

        func_name = pyqgl2.importer.collapse_name(node.func)
        func_def = self.importer.resolve_sym(node.qgl_fname, func_name)

        if func_def.name == QGL2.QBIT_ALLOC:
            return True
        else:
            return False

    def visit_Assign(self, node):
        print('ASSIGN %s' % ast.dump(node))

        if self.is_qbit_creation(node.value):
            # OK, we got a Qbit.  But we're very fussy about what
            # parameters a Qbit declaration must have: the first
            # parameter must be plain-vanilla integer.  Anything
            # else, and we can't guarantee its value at runtime.

            if len(node.value.args) == 0:
                self.error_msg(node,
                        '%s does not have parameters' % QGL2.QBIT_ALLOC)
                return node

            arg0 = node.value.args[0]
            if not isinstance(arg0, ast.Num):
                self.error_msg(node,
                        '1st param to %s must be an int' % QGL2.QBIT_ALLOC)
                return node

            if not isinstance(arg0.n, int):
                self.error_msg(node,
                        '1st param to %s must be an int' % QGL2.QBIT_ALLOC)
                return node

            channo = arg0.n

            if len(node.targets) != 1:
                self.error_msg(node,
                        'assignment of Qbit must be to a symbol')
                return node

            target = node.targets[0]
            if not isinstance(target, ast.Name):
                self.error_msg(node,
                        'assignment of Qbit must be to a symbol')
                return node

            target_name = target.id

            if target_name in self.qbit_map:
                # We don't treat this as an error, but perhaps
                # we should
                #
                self.error_msg(node,
                        'reassignment of Qbit [%s] deprecated' % target_name)

            print('GOT QBIT CHANNEL %d for symbol %s' % (channo, target.id))

            self.qbit_map[target_name] = 'QBIT_%d' % channo

        return node

    def visit_FunctionDef(self, node):
        """
        This is a shortcut to leap to working on the
        statements of the function instead of doing
        substitution on the parameters and annotations
        of the function

        TODO:
        Eventually we'll have to deal with everything,
        not just the body
        """

        node.body = [self.visit(stmnt) for stmnt in node.body]
        return node

    def find_qbit(self, name):
        if not name:
            print('Find(%s): None' % name)
            return None
        elif name in self.qbit_map:
            print('Find(%s): found in local qbit_map %s' %
                    (name, self.qbit_map[name]))
            return self.qbit_map[name]
        elif name in self.GLOBAL_QBITS:
            print('Find(%s): found in global qbit_map %s' %
                    (name, self.GLOBAL_QBITS[name]))
            return self.GLOBAL_QBITS[name]

        # This is a hack: it should be in the global context, not
        # found lexically
        #
        elif name.startswith('QBIT_'):
            print('Find: found %s based on name' % name)
            return name

        print('Find(%s): struck out' % name)
        return None

    def handle_builtin(self, node):
        literal_args = list()
        for arg in node.args:
            if isinstance(arg, ast.Name):
                literal_args.append(arg.id)
            elif isinstance(arg, ast.Str):
                literal_args.append("'" + arg.s + "'")
            elif isinstance(arg, ast.Num):
                literal_args.append(str(arg.n))

        print('LITERAL %s' % literal_args)

        text = '%s(%s)' % (node.func.id, ', '.join(literal_args))

        print('BUILTIN %s' % text)
        return node

    def visit_Call(self, node):
        # Now we have to map our parameters to this call

        # Find the definition for the function
        #
        # TODO: we're only looking in the current file,
        # not using modules

        # fname is the full name, including module names
        #
        print('TT0 %s' % ast.dump(node.func))
        funcname = pyqgl2.importer.collapse_name(node.func)

        print('TT1 %s' % ast.dump(node.func))
        # deal with any arguments
        for arg in node.args:
            self.visit(arg)
        print('TT2 %s' % ast.dump(node))

        if funcname in self.BUILTIN_FUNCS:
            return self.handle_builtin(node)

        aparams = [arg.id if isinstance(arg, ast.Name) else None
                for arg in node.args]
        print('PARAMS %s actual params %s' % (funcname, str(aparams)))

        # FIXME: need to substitute the correct value for the QBITs

        print('DBG finding ast for %s' % funcname)

        symval = self.importer.resolve_sym(node.qgl_fname, funcname)
        if not symval:
            self.error_msg(node, 'no definition found for %s' % funcname)
            return node

        print('SYMVAL %s' % str(symval))

        # func_ast = symval[3][0]
        # fparams = self.importer._qbit_decl(func_ast)

        func_ast = symval
        fparams = func_ast.qgl_args

        print('FOUND %s formal params %s' % (funcname, str(fparams)))

        # map our local bindings to the formal parameters of
        # this function, to create a signature

        # It would be nice if we could do something with kwargs,
        # but we're not even making an attempt right now
        #
        qbit_defs = list()
        if len(fparams) != len(aparams):
            self.error_msg(node,
                    'formal and actual param lists differ in length')
            return node

        print('MY CONTEXT %s' % str(self.qbit_map))

        print('APARAM %s' % aparams)

        for ind in range(len(fparams)):
            fparam = fparams[ind]
            aparam = aparams[ind]

            (fparam_name, fparam_type) = fparam.split(':')
            print('fparam %s needs %s' % (fparam_name, fparam_type))

            qbit_ref = self.find_qbit(aparam)
            if (fparam_type == 'qbit') and not qbit_ref:
                self.error_msg(node,
                        'assigned non-qbit to qbit param %s' % fparam_name)
                return node
            elif (fparam_type != 'qbit') and qbit_ref:
                self.error_msg(node,
                        'assigned qbit to non-qbit param %s' % fparam_name)
                return node

            if qbit_ref:
                qbit_defs.append((fparam_name, qbit_ref))

        print('MAPPING FOR QBITS %s' % str(qbit_defs))

        # see whether we already have a function that matches
        # the signature.  If we do, then peel off a copy and use
        # it here.  If not, create one and add it to the
        # symbol table
        #
        # TODO: we don't keep track of the functions we've created,
        # but create new ones each time.

        func_copy = deepcopy(func_ast)
        specialized_func = specialize(func_copy, qbit_defs, self.func_defs,
                self.importer)
        # print('SPECIALIZED %s' % ast.dump(specialized_func))
        print('WOULD CALL %s' % specialized_func.name)
        print('CALL %s' % ast.dump(node))
        new_call = deepcopy(node)
        new_call.func.id = specialized_func.name

        # return the resulting node
        #
        return new_call

def specialize(func_node, qbit_defs, func_defs, importer):
    """
    qbit_defs is a list of (fp_name, qref) mappings
    (where fp_name is the name of the formal parameter
    and qref is a reference to a physical qbit)

    func_node is presumed to be a function definition

    returns a new node that contains a function definition
    for a "specialized" version of the function that
    works with that qbit definition.
    """

    print('SPECIALIZE %s' % qbit_defs)
    # print('INITIAL AST %s' % ast.dump(func_node))

    # needs more mangling?
    refs = '_'.join([str(phys_chan) for (fp_name, phys_chan) in qbit_defs])
    mangled_name = func_node.name + '___' + refs

    print('MANGLED NAME %s' % mangled_name)

    specialized_func_def = importer.resolve_sym(
            func_node.qgl_fname, mangled_name)
    if specialized_func_def:
        return specialized_func_def

    sub_chan = SubstituteChannel(func_node.qgl_fname, qbit_defs, func_defs,
            importer)
    new_func = sub_chan.visit(func_node)
    new_func.name = mangled_name

    # add the specialized version of the function to the namespace
    #
    namespace = importer.path2namespace[func_node.qgl_fname]
    importer.add_function(namespace, mangled_name, new_func)

    print('SPECIALIZED %s' % pyqgl2.ast_util.ast2str(new_func))

    return new_func

def preprocess(fname, main_name=None):

    importer = NameSpaces(fname, main_name)
    ptree = importer.path2ast[importer.base_fname]

    type_check = CheckType(importer.base_fname, importer)
    nptree = type_check.visit(ptree)

    # Find the main function
    qglmain = importer.qglmain
    if not qglmain:
        print('no function declared to be main')
        sys.exit(1)

    print('TYPE_CHECK DEFS %s' % str(type_check.func_defs))

    specialize(qglmain, list(), type_check.func_defs, importer)

    for func_def in sorted(type_check.func_defs.keys()):
        types, node = type_check.func_defs[func_def]
        call_list = node.qgl_call_list

    if NodeError.MAX_ERR_LEVEL >= NodeError.NODE_ERROR_ERROR:
        print('bailing out 1')
        sys.exit(1)

    sym_check = CheckSymtab(fname, type_check.func_defs, importer)
    nptree2 = sym_check.visit(nptree)

    if NodeError.MAX_ERR_LEVEL >= NodeError.NODE_ERROR_ERROR:
        print('bailing out 2')
        sys.exit(1)

    wav_check = CheckWaveforms(fname, type_check.func_defs)
    nptree3 = sym_check.visit(nptree2)

    if NodeError.MAX_ERR_LEVEL >= NodeError.NODE_ERROR_ERROR:
        print('bailing out 3')
        sys.exit(1)

if __name__ == '__main__':
    preprocess(sys.argv[1])
