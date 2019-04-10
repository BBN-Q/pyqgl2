'''
Copyright 2019 Raytheon BBN Technologies

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import ast

from pyqgl2.ast_util import NodeError, ast2str
from pyqgl2.debugmsg import DebugMsg
from pyqgl2.lang import QGL2


class QValueAllocator(object):
    """
    Manages the state for QValue allocation

    TODO: when a name falls out of scope, it should
    be freed, but we don't provide a way to do that yet
    """

    # map from name to QValue (size, base_addr)
    #
    # "Anonymous" values are given a unique nonce for a name
    #
    ALLOCATED = dict()

    # to prevent collisions between named qvalues and unnamed
    # qvalues, we prefix the name of anonymous qvalues with
    # an otherwise inaccessible prefix
    #
    ANON_PREFIX = '__qv_'

    _INITIAL_ANON_COUNTER = 0
    ANON_COUNTER = _INITIAL_ANON_COUNTER

    # The next address available to allocate.  Each address
    # is 32 bits wide.  We don't start at 0 in order to set
    # aside some special locations.
    #
    _INITIAL_NEXT_ADDR = 16
    NEXT_ADDR = _INITIAL_NEXT_ADDR

    # Don't permit anything larger than this address to be
    # allocated
    #
    # FIXME: this is a placeholder for the correct value,
    # which should be initialized at the start of each run
    #
    _INITIAL_MAX_ADDR = 1023
    MAX_ADDR = _INITIAL_MAX_ADDR

    @staticmethod
    def _reset():
        """
        Reset the state of the QValue allocator

        Primarily intended for use in unit tests; destructive
        if used during the scope of allocated QValues
        """

        QValueAllocator.ANON_COUNTER = QValueAllocator._INITIAL_ANON_COUNTER
        QValueAllocator.NEXT_ADDR = QValueAllocator._INITIAL_NEXT_ADDR
        QValueAllocator.MAX_ADDR = QValueAllocator._INITIAL_MAX_ADDR

        QValueAllocator.ALLOCATED = dict()

    @staticmethod
    def alloc(size, name=None):
        """
        Allocate space of the given size, and bind it to the given
        name (if provided, or a nonce name, otherwise)

        Return the base address of the space reserved for the value
        """

        # TODO: sanity check on size.
        #
        # FIXME: we're limiting things to single words for now.
        #
        if size < 1:
            raise NameError('alloc size < 1 (= %d)' % size)
        elif size > 32:
            raise NameError('alloc size > 32 (= %d)' % size)

        if not name:
            name = '%s%d' % (
                    QValueAllocator.ANON_PREFIX,
                    QValueAllocator.ANON_COUNTER)
            QValueAllocator.ANON_COUNTER += 1
        else:
            # make sure that the name is valid
            #
            if name.startswith(QValueAllocator.ANON_PREFIX):
                raise NameError(
                        'name (%s) cannot start with anonymous prefix' % name)

            # if the name is already in use, make sure that
            # it matches.  Names cannot be redefined yet.

            bound_size, bound_addr = QValueAllocator.lookup(name)
            if bound_size == size:
                return (name, bound_size, bound_addr)
            elif bound_size:
                raise NameError(
                        'cannot change size of QValue (%s) from %d to %d' % (
                            name, bound_size, size))

        if QValueAllocator.NEXT_ADDR > QValueAllocator.MAX_ADDR:
            raise NameError('no more space to allocate QValue')

        addr = QValueAllocator.NEXT_ADDR

        # FIXME: to be able to handle multi-word qvalues, we
        # will need to allocate multiple words
        #
        QValueAllocator.NEXT_ADDR += 1

        QValueAllocator.ALLOCATED[name] = (size, addr)

        return name, size, addr

    @staticmethod
    def lookup(name):
        if name in QValueAllocator.ALLOCATED:
            return QValueAllocator.ALLOCATED[name]
        else:
            return None, None 

    @staticmethod
    def __str__():
        """
        This is incomplete, but it's a start
        """

        return str(QValueAllocator.ALLOCATED)


class QValue(object):
    """
    A variable that can be bound to the result of the measurement
    of a QRegister.

    Use QValue.factory() to create instances from AST nodes.
    """

    def __init__(self, name=None, qreg=None, size=None, **kwargs):
        """
        """

        if name is not None:
            if not isinstance(name, str):
                raise NameError('name must be an int')

        if qreg is not None and size is not None:
            raise NameError('cannot specify both qreg and size')
        elif qreg is not None:
            # TODO: get the size from the QRegister
            pass
        elif size is not None:
            if not isinstance(size, int):
                raise NameError('size must be an int')
        else:
            size = 32

        self.name, self.size, self.addr = QValueAllocator.alloc(
                size=size, name=name)

    @staticmethod
    def factory(node, local_vars):

        call_params = dict()

        for kwarg in node.value.keywords:
            if kwarg.arg not in ['name', 'qreg', 'size']:
                NodeError.error_msg(
                        node, 'unexpected parameter [%s]' % kwarg.arg)
                continue

            # This shouldn't happen, because the AST parser checks for
            # repeated keyword parameters... But just in case.
            #
            if kwarg.arg in call_params:
                NodeError.error_msg(
                        node, 'parameter seen more than once [%s]' % kwarg.arg)
                continue

            call_params[kwarg.arg] = eval(
                    ast2str(kwarg.value), None, local_vars)

        if NodeError.error_detected():
            return None

        try:
            return QValue(**call_params)
        except NameError as exc:
            NodeError.error_msg(node, str(exc))
            return None


def is_qval_create(node):
    """
    Returns True if node represents a QValue creation and assignment.

    There are several sloppy assumptions here.
    """

    if not isinstance(node, ast.Assign):
        return False

    # Only handles simple assignments; not tuples
    # TODO: handle tuples
    if len(node.targets) != 1:
        return False

    if not isinstance(node.value, ast.Call):
        return False

    if not isinstance(node.value.func, ast.Name):
        return False

    if node.value.func.id != QGL2.QVAL_ALLOC:
        return False

    return True


if __name__ == '__main__':

    def test_main():
        a = QValueAllocator.alloc(None, 3, 'foo')
        b = QValueAllocator.alloc(None, 4, 'bar')
        c = QValueAllocator.alloc(None, 5)
        d = QValueAllocator.alloc(None, 6)

        print(a)
        print(b)
        print(c)
        print(d)

        a = QValueAllocator.alloc(None, 31, 'foo')
        b = QValueAllocator.alloc(None, 4, 'bar')
        print(a)
        print(b)

        QValueAllocator._reset()
        a = QValueAllocator.alloc(None, 31, 'foo')
        b = QValueAllocator.alloc(None, 4, 'bar')
        print(a)
        print(b)

    test_main()
