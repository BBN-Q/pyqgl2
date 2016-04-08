# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved

"""
Names and descriptions of attributes that may be
added to AST nodes to represent information used
by the preprocessor.

Attribute names are typically used literally (except
when checking for the presence of an attribute by name)
so the purpose of this file is primarily documentation.
"""


class QGL2Ast(object):
    """
    Attribute names and their descriptions
    """

    # The name of the source file associated with this node
    #
    # All AST nodes that the preprocessor uses should have this
    # attribute.  When the preprocessor inserts new nodes, this
    # attribute should be added
    #
    qgl_fname = 'qgl_fname'

    # this attribute, if present, denotes the set of qbits
    # referenced by descendants of this node (or None if there
    # are no referenced qbits)
    #
    qgl_qbit_ref = 'qgl_qbit_ref'

    # An attribute present on FunctionDef nodes that are marked
    # as QGL2 functions
    #
    qgl_func = 'qgl_func'

    # An attribute present on FunctionDef nodes that are marked
    # as QGL2 stub functions.  Stub functions are defined elsewhere
    # (usually in QGL1) but the stub definition contains information
    # about the type signature of the function
    #
    qgl_stub = 'qgl_stub'

    # If a function call has been inlined, then the call node
    # in the original AST is given an attribute that refers to
    # the inlined version of the call
    #
    qgl_inlined = 'qgl_inlined'
