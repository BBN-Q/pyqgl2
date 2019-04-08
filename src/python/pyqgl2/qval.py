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
    ANON_COUNTER = 0

    # The next address available to allocate.  Each address
    # is 32 bits wide.  We don't start at 0 in order to set
    # aside some special locations.
    #
    NEXT_ADDR = 16

    # Don't permit anything larger than this address to be
    # allocated
    #
    # FIXME: this is a placeholder for the correct value,
    # which should be initialized at the start of each run
    #
    MAX_ADDR = 1023

    @staticmethod
    def alloc(node, size, name=None):
        """
        Allocate space of the given size, and bind it to the given
        name (if provided, or a nonce name, otherwise)

        The node is used only to create meaningful diagnostic
        messages if there is an error of any kind

        Return the base address of the space reserved for the value
        """

        # TODO: sanity check on size.
        #
        # FIXME: we're limiting things to single words for now.
        #
        if size < 1:
            NodeError.error_msg(
                    node, 'alloc size < 1 (= %d)' % size)
            return None, None, None
        elif size > 32:
            NodeError.error_msg(
                    node, 'alloc size > 32 (= %d)' % size)
            return None, None, None

        if not name:
            name = '%s%d' % (
                    QValueAllocator.ANON_PREFIX,
                    QValueAllocator.ANON_COUNTER)
            QValueAllocator.ANON_COUNTER += 1
        else:
            # make sure that the name is valid
            #
            if name.startswith(QValueAllocator.ANON_PREFIX):
                NodeError.error_msg(
                        node,
                        'name (%s) cannot start with anonymous prefix' % name)
                return None, None, None

            # if the name is already in use, make sure that
            # it matches.  Names cannot be redefined yet.

            bound_size, bound_addr = QValueAllocator.lookup(name)
            if bound_size == size:
                return (name, bound_size, bound_addr)
            elif bound_size:
                NodeError.error_msg(
                        node, 'cannot change size of (%s) from %d to %d' % (
                            name, bound_size, size))
                return None, None, None

        if QValueAllocator.NEXT_ADDR > QValueAllocator.MAX_ADDR:
            NodeError.error_msg(
                    node, 'no more space to allocate QValue')
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

    def __init__(self, *args, **kwargs):
        """
        """

        if 'name' in kwargs:
            pass

        if 'qreg' in kwargs:
            pass

        if 'size' in kwargs:
            pass

        if 'addr' in kwargs:
            pass

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

    test_main()
