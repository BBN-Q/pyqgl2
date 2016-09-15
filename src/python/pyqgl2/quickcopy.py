# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.
import pickle

# copy.deepcopy is slow. This is _much_ faster.
# FIXME: Can we do even better?

def quickcopy(original):
    '''Quick equivalent of copy.deepcopy'''
    return pickle.loads(pickle.dumps(original))
