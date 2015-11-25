# Copyright 2015 by Raytheon BBN Technologies.  All Rights Reserved.

"""
Utility class for "deferred calls".

There's probably a better name for this, but the idea is to
evaluate all of the parameters to a function (in preparation
for calling the function later) and then save a copy of the
actual parameters and a reference to the function so the
function can be applied to the parameters at some later time,
possibly in a different context.

It's not a closure, because it doesn't capture anything from
the current execution environment (unless the actual parameters
do something to grab a copy).  Part of the motivation, however,
is that closures in Python can be difficult to work with.

The motivation is to enable some simple forms of metaprogramming.

Example:

    def foo(val):
        print('%s' % str(val))

    def print_before_and_after(deferred):
        print('BEFORE')
        deferred()
        print('AFTER')

    # Make a list of deferred calls, and then pass each
    # to print_before_and_after
    #
    deferred_list = [DeferredCall(foo, ind) for ind in range(10)]
    for deferred in deferred_list:
        print_before_and_after(deferred)

"""

class DeferredCall(object):
    """
    Create a deferred call, which can be executed later
    """

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        """
        Apply the function to the args (and keyword args)
        and return the result
        """

        return(self.func(*self.args, **self.kwargs))
