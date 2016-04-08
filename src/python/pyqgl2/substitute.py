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
from pyqgl2.debugmsg import DebugMsg
from pyqgl2.importer import NameSpaces
from pyqgl2.lang import QGL2

class SubstituteChannel(NodeTransformerWithFname):

#    # globally-defined qbits
#    #
#    GLOBAL_QBITS = {
#    }

#    BUILTIN_FUNCS = [
#            'X90', 'X180',
#            'Y90', 'Y180',
#            'Z90', 'Z180',
#            'UTheta'
#    ]

    def __init__(self, fname, qbit_bindings, func_defs, importer=None):
        super(SubstituteChannel, self).__init__()

        self.qbit_map = {name:chanLabel for (name, chanLabel) in qbit_bindings}
        self.func_defs = func_defs
        self.importer = importer

        DebugMsg.log('QBIT MAP %s' % self.qbit_map)

    def visit_Name(self, node):
        DebugMsg.log('VISITING NAME %s' % ast.dump(node))

        if hasattr(node, 'qgl_is_qbit') and node.qgl_is_qbit:
            # This name is already marked as being a reference
            # to a qbit, so no need to do anything else
            #
            pass

        elif node.id in self.qbit_map:
            new_id = self.qbit_map[node.id]
            DebugMsg.log('TST marking %s as qbit %s' % (node.id, new_id))
            node.id = new_id
            node.qgl_is_qbit = True
        else:
            DebugMsg.log('TST not marking %s as a qbit' % node.id)
            node.qgl_is_qbit = False

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
        DebugMsg.log('XX func_name %s' % func_name)
        func_def = self.importer.resolve_sym(node.qgl_fname, func_name)
        DebugMsg.log('XX func_def %s' % str(func_def))

        # If we don't have a definition for it, we must assume
        # that it's not Qbit definition.  We can't do anything
        # with it
        #
        if not func_def:
            return False
        elif func_def.name == QGL2.QBIT_ALLOC:
            return True
        else:
            return False

    def visit_Assign(self, node):
        DebugMsg.log('ASSIGN %s' % ast.dump(node))

        if self.is_qbit_creation(node.value):
            # OK, we got a Qbit.  But we're very fussy about what
            # parameters a Qbit declaration must have: the first
            # parameter must be plain-vanilla string.  Anything
            # else, and we can't guarantee its value at runtime.

            # First ensure there's a label.
            # If there are positional args, assume it is first
            # Otherwise, look for it among keyword args
            chanLabel = getChanLabel(node)
            if not chanLabel:
                self.error_msg(node, "Failed to find channel label")
                return node

            # Now look at targets

            if len(node.targets) != 1:
                self.error_msg(node,
                        'assignment of Qbit must be to a symbol')
                return node

            target = node.targets[0]
            if not isinstance(target, ast.Name):
                self.error_msg(node,
                        'assignment of Qbit must be to a symbol')
                return node

            target.qgl_is_qbit = True

            target_name = target.id

            if target_name in self.qbit_map:
                # We don't treat this as an error, but perhaps
                # we should
                #
                self.error_msg(node,
                        'reassignment of Qbit [%s] deprecated' % target_name)

            DebugMsg.log('GOT QBIT CHANNEL %s for symbol %s' %
                    (chanLabel, target.id))

            self.qbit_map[target_name] = 'QBIT_%s' % chanLabel
            # FIXME: Or just use the label as is?
            # self.qbit_map[target_name] = chanLabel

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

    def find_qbit(self, node):

        if not isinstance(node, ast.Name):
            DebugMsg.log('SUB %s not a Name. Is %s' % (node, type(node)))
            return None

        name = node.id

        if not name:
            DebugMsg.log('Find(%s): None' % name)
            return None

        elif node.qgl_is_qbit:
            DebugMsg.log('TST FOUND QBIT DECL %s' % name)
            return name

        elif name in self.qbit_map:
            DebugMsg.log('TST Find(%s): found in local qbit_map %s' %
                    (name, self.qbit_map[name]))
            return self.qbit_map[name]
#        elif name in self.GLOBAL_QBITS:
#            DebugMsg.log('TST Find(%s): found in global qbit_map %s' %
#                    (name, self.GLOBAL_QBITS[name]))
#            return self.GLOBAL_QBITS[name]

        DebugMsg.log('TST Find(%s): struck out' % name)
        return None

#    def handle_builtin(self, node):
#        literal_args = list()
#        for arg in node.args:
#            if isinstance(arg, ast.Name):
#                literal_args.append(arg.id)
#            elif isinstance(arg, ast.Str):
#                literal_args.append("'" + arg.s + "'")
#            elif isinstance(arg, ast.Num):
#                literal_args.append(str(arg.n))
#            elif isinstance(arg, ast.NameConstant):
#                literal_args.append(str(arg.value))

#        DebugMsg.log('LITERAL %s' % literal_args)

#        text = '%s(%s)' % (
#                pyqgl2.importer.collapse_name(node.func),
#                ', '.join(literal_args))

#        DebugMsg.log('BUILTIN %s' % text)
#        return node

    def visit_Call(self, orig_node):
        # Now we have to map our parameters to this call

        # DebugMsg.log('TT1 %s' % ast.dump(orig_node.func))

        # replace any references to qbits in the call with references
        # to the 'global' qbit names for those qbits.
        #
        node = deepcopy(orig_node)
        for arg in node.args:
            self.visit(arg)

        # Find the definition for the function, and see whether
        # it is a function that we can specialize.  If we can't
        # specialize it, then return the new node (with possibly
        # rewritten args)
        #
        funcname = pyqgl2.importer.collapse_name(node.func)
        func_ast = self.importer.resolve_sym(node.qgl_fname, funcname)
        if not func_ast:
            self.diag_msg(node, 'no definition found for %s' % funcname)
            return node
        if func_ast.name == QGL2.QBIT_ALLOC:
            self.error_msg(node,
                           ("%s() called as a Call. Only when called as an Assign is this treated as a qbit." % QGL2.QBIT_ALLOC))
        # Note we allow qgl_stub functions to pass through here,
        # so the arguments are error checked
        if not can_specialize(func_ast):
            return node
        # DebugMsg.log("Going to rewrite %s()" % funcname)
        # fparams represents all args other than *args or **kwargs
        fparams = func_ast.qgl_args
        # But that includes things with reasonable defaults
        # Here we produce counters of things without a default
        numFArgsNoDefaults = len(func_ast.args.args) - len(func_ast.args.defaults)
        numFKWArgsNoDefaults = len(func_ast.args.kwonlyargs) - len([default for default in func_ast.args.kw_defaults if default is not None])
        DebugMsg.log("For func %s got ArgsNoDefaults: %d, KWArgsNoDefaults: %d" % (funcname, numFArgsNoDefaults, numFKWArgsNoDefaults))

#        if funcname in self.BUILTIN_FUNCS:
#            DebugMsg.log('TT3 builtin %s' % ast.dump(node))
#            # return self.handle_builtin(node)
#            pass

        aparams = [arg if isinstance(arg, ast.Name) else None
                for arg in node.args]
        # aparams will include None in the list if there's a non qbit arg
        # if aparams == [None]:
        #     DebugMsg.log("%s() got aparams [None]: %s" % (funcname, str(node.args)))
        # DebugMsg.log('FOUND %s() formal params: %s' % (funcname, str(fparams)))

        # map our local bindings to the formal parameters of
        # this function, to create a signature

        # Now find the qbit argument and replace with one of the qbits from our map,
        # ensuring that the value supplied is a qbit where required
        # Note this code tries to support kwargs somewhat
        # However, it still doesn't deal well with a method signature that takes *args or **kwargs
        qbit_defs = list()
        if len(aparams) > len(fparams) or \
           len(aparams) < (numFArgsNoDefaults + numFKWArgsNoDefaults):
#        if len(fparams) != len(aparams):
            self.error_msg(node,
                    ('[%s] formal and actual param lists differ in length (%s != %s' %
                        (funcname, fparams, [arg.id if arg is not None else 'Not-a-variable-name' for arg in aparams])))
            return node

        DebugMsg.log('MY CONTEXT %s' % str(self.qbit_map))

        DebugMsg.log('APARAM %s' % aparams)

        for ind in range(len(fparams)):
            fparam = fparams[ind]
            if ind < len(aparams):
                aparam = aparams[ind]
            else:
                DebugMsg.log("Function param %d (%s) is not an actual argument - stop here doing qbit mapping" % (ind, fparam))
                break

            (fparam_name, fparam_type) = fparam.split(':')
            DebugMsg.log('fparam %s needs %s' % (fparam_name, fparam_type))

            qbit_ref = self.find_qbit(aparam)
            if (fparam_type == QGL2.QBIT) and not qbit_ref:
                self.error_msg(node,
                        ('[%s] assigned non-qbit to qbit param [%s]' %
                            (funcname, fparam_name)))
                return node
            elif (fparam_type != QGL2.QBIT) and qbit_ref:
                self.error_msg(node,
                        ('[%s] assigned qbit to non-qbit param [%s]' %
                            (funcname, fparam_name)))
                return node
            elif not qbit_ref:
                DebugMsg.log("OK: %s() param %d doesn't want a qbit and argument wasn't one" % (funcname, ind))
            else:
                DebugMsg.log("OK: %s() assigned %s to param %d(%s)" % (funcname, qbit_ref, ind, fparam))

            if qbit_ref:
                qbit_defs.append((fparam_name, qbit_ref))

        DebugMsg.log('MAPPING FOR QBITS %s' % str(qbit_defs))

        # TODO: see whether we already have a function that matches
        # the signature.  If we do, then get a reference to it, and
        # use it here.  If not, create one and add it to the
        # symbol table

        # Note we do not specialize qgl_stub functions
        if can_specialize(func_ast) and not func_ast.qgl_stub:
            func_copy = deepcopy(func_ast)
            specialized_func = specialize(
                    func_copy, qbit_defs, self.func_defs, self.importer,
                    context=orig_node)
            # DebugMsg.log('SPECIALIZED %s' % ast.dump(specialized_func))
            DebugMsg.log('WOULD CALL %s' % specialized_func.name)
            DebugMsg.log('CALL %s' % ast.dump(node))

            new_call = deepcopy(node)
            new_call.func.id = specialized_func.name

            return new_call
        else:
            return node

def can_specialize(func_node):
    """
    Determine whether this function definition can/should be
    specialized.  This is only true if the function has been
    marked as being QGL2.

    This attribute should have been determined by the importer.
    """

    if not hasattr(func_node, 'qgl_func') or not func_node.qgl_func:
        return False
    # Do not avoid qgl stubs here cause
    # it means we don't error check args
#    elif func_node.qgl_stub:
#        DebugMsg.log("Will not specialize a qgl_stub: %s" % func_node.name)
#        return False
    else:
        return True


def specialize(func_node, qbit_defs, func_defs, importer, context=None):
    """
    qbit_defs is a list of (fp_name, qref) mappings
    (where fp_name is the name of the formal parameter
    and qref is a reference to a physical qbit)

    func_node is presumed to be a function definition

    returns a new node that contains a function definition
    for a "specialized" version of the function that
    works with that qbit definition.

    context is the node that triggered the specialization
    (usually the Call node).  The result of the specialization is
    recorded in the namespace of that Call, so that it can be
    accessed again we we want to inline the function.
    """

    # needs more mangling?
    refs = '_'.join([str(phys_chan) for (fp_name, phys_chan) in qbit_defs])
    mangled_name = func_node.name + '___' + refs

    specialized_func_def = importer.resolve_sym(
            func_node.qgl_fname, mangled_name)
    if specialized_func_def:
        return specialized_func_def

    new_func_node = deepcopy(func_node)

    sub_chan = SubstituteChannel(
            new_func_node.qgl_fname, qbit_defs, func_defs, importer)
    new_func = sub_chan.visit(new_func_node)
    new_func.name = mangled_name

    for subnode in ast.walk(new_func_node):
        # If the new_func_node has any subnodes that came from
        # inlined calls that are referenced (via qgl2_orig_call),
        # then specialize the referenced calls as well.
        # The reason for this is that we want to keep track of
        # variables (such as qbits) that might be "optimized away"
        # if the specialized version of the code doesn't reference
        # them any more, so we can map things back to channels
        # at some point.
        #
        if hasattr(subnode, 'qgl2_orig_call'):
            new_subcall = sub_chan.visit(subnode.qgl2_orig_call)
            subnode.qgl2_orig_call = new_subcall

    # add the specialized version of the function to the namespace
    #
    # If context is present, add it to the namespace for that
    # context, rather than the namespace where it was originally
    # defined
    #
    if context:
        namespace = importer.path2namespace[context.qgl_fname]
    else:
        namespace = importer.path2namespace[new_func_node.qgl_fname]

    importer.add_function(namespace, mangled_name, new_func)

    DebugMsg.log('SPECIALIZED %s' % pyqgl2.ast_util.ast2str(new_func))

    return new_func

def preprocess(fname, main_name=None):

    importer = NameSpaces(fname, main_name)
    ptree = importer.path2ast[importer.base_fname]

    type_check = CheckType(importer.base_fname, importer)
    nptree = type_check.visit(ptree)

    # Find the main function
    qglmain = importer.qglmain
    if not qglmain:
        DebugMsg.log('no function declared to be main')
        sys.exit(1)

    DebugMsg.log('TYPE_CHECK DEFS %s' % str(type_check.func_defs))

    specialize(qglmain, list(), type_check.func_defs, importer, context=ptree)

    for func_def in sorted(type_check.func_defs.keys()):
        types, node = type_check.func_defs[func_def]
        call_list = node.qgl_call_list

    if NodeError.MAX_ERR_LEVEL >= NodeError.NODE_ERROR_ERROR:
        DebugMsg.log('bailing out 1')
        sys.exit(1)

    sym_check = CheckSymtab(fname, type_check.func_defs, importer)
    nptree2 = sym_check.visit(nptree)

    if NodeError.MAX_ERR_LEVEL >= NodeError.NODE_ERROR_ERROR:
        DebugMsg.log('bailing out 2')
        sys.exit(1)

    wav_check = CheckWaveforms(type_check.func_defs, importer)
    nptree3 = sym_check.visit(nptree2)

    if NodeError.MAX_ERR_LEVEL >= NodeError.NODE_ERROR_ERROR:
        DebugMsg.log('bailing out 3')
        sys.exit(1)

def getChanLabel(node):
    '''Given an Call to Qubit() or an Assign containing such, find the label of the qbit.
    Return None if can't find it.'''
    theNode = node
    if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
        theNode = node.value 
    if not isinstance(theNode, ast.Call):
        DebugMsg.log("Was not a call")
        return None

    # First ensure there's a label.
    # If there are positional args, assume it is first
    # Otherwise, look for it among keyword args
    chanLabel = None
    if len(theNode.args) > 0:
        arg0 = theNode.args[0]
        # FIXME:
        # This code requires that the label arg be an explicit string
        # Not a variable, function call, etc.
        # We need this to (a) error check the arg value is a string, and
        # (b) extract the value for labeling in the QBIT map
        # This is a sad, ugly restriction
        if not isinstance(arg0, ast.Str):
            DebugMsg.log('1st param to %s() must be a string - got %s' %
                    (QGL2.QBIT_ALLOC, arg0))
            return None

        if not isinstance(arg0.s, str):
            DebugMsg.log('1st param to %s() must be a str - got %s' %
                    (QGL2.QBIT_ALLOC, arg0.s))
            return None

        chanLabel = arg0.s
    if len(theNode.keywords) > 0:
        for kwarg in theNode.keywords:
            if kwarg.arg == 'label':
                if chanLabel is not None:
                    kwp = str(kwarg.value)
                    if isinstance(kwarg.value, ast.Str):
                        kwp = kwarg.value.s
                    DebugMsg.log("%s had a positional arg used as label='%s'. Cannot also have keyword argument label='%s'" % (QGL2.QBIT_ALLOC, chanLabel, kwp))
                labelArg = kwarg.value
                if not isinstance(labelArg, ast.Str):
                    DebugMsg.log('label param to %s() must be a string - got %s' % (QGL2.QBIT_ALLOC, labelArg))
                    return None

                if not isinstance(labelArg.s, str):
                    DebugMsg.log('label param to %s() must be a str - got %s' % (QGL2.QBIT_ALLOC, labelArg.s))
                    return None
                chanLabel = labelArg.s
                break
        if chanLabel is None:
            DebugMsg.log("%s() missing required label (string) argument: found no label kwarg and had no positional args" % QGL2.QBIT_ALLOC)
            return None
    elif chanLabel is None:
        DebugMsg.log('%s() missing required label (string) argument: call had 0 parameters' % QGL2.QBIT_ALLOC)
        return None
    return chanLabel

if __name__ == '__main__':
    preprocess(sys.argv[1])
