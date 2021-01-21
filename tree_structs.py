__author__ = 'Lena Collienne'

import os
from ctypes import *

lib = CDLL(f'{os.path.dirname(os.path.realpath(__file__))}/tree.so')

class NODE(Structure):
    _fields_ = [('parent', c_long), ('children', c_long * 2), ('time', c_long)] # The order of arguments here matters! Needs to be the same as in C code!
    def __init_(self, parent, children, time):
        self.parent = parent
        self.children = children
        self.time = time


class TREE(Structure):
    _fields_ =  [('tree', POINTER(NODE)), ('num_leaves', c_long), ('root_time', c_long), ('sos_d', c_long)] # Everything from struct definition in C
    def __init_(self, tree, num_leaves, root_time, sos_d):
        self.tree = tree
        self.num_leaves = num_leaves
        self.root_time = root_time
        self.sos_d = sos_d


class TREE_LIST(Structure):
    _fields_ = [('trees', POINTER(TREE)), ('num_trees', c_int)]
    def __init_(self, trees, num_trees):
        self.trees = trees
        self.num_trees = num_trees
