__author__ = 'Lena Collienne, Jordan Kettles'

# Handling Tree input and output (to C)
# Written by Lena Collienne, modified by Jordan Kettles.

import sys
import re
import math
from tree_structs import *
from collections import OrderedDict


# Update the height of the node child by the height of the parent - difference.
def update_child(pdict, cdict, inhdict, child, pheight, dif):
    prevheight = inhdict[child]
    inhdict[child] = prevheight + (pheight - dif)
    inhdict = update_children(pdict, cdict, inhdict, child, inhdict[child], prevheight)
    # print("inhdict[child] = " + str(prevheight) + " + " + str(pheight - dif))
    # print(str(prevheight) + " ---> " + str(inhdict[child]))
    return inhdict


# Update children finds the internal nodes of node and updates their heights.
def update_children(pdict, cdict, inhdict, node, pheight, dif):
    children_list = [key for (key, value) in pdict.items() if value == node]
    in1 = re.findall(r"internal_node(\d+)", children_list[0])
    in2 = re.findall(r"internal_node(\d+)", children_list[1])
    # print("Updating the children of {}, node {} & node {}.").format(node, children_list[0], children_list[1])
    # print(children_list[0] + " " + children_list[1])

    if len(in1) > 0:
        inhdict = update_child(pdict, cdict, inhdict, int(in1[0]), pheight, dif)
    if len(in2) > 0:
        inhdict = update_child(pdict, cdict, inhdict, int(in2[0]), pheight, dif)
    return inhdict


# alternative for reading newick string iteratively by once looping through string s instead of recursion.
def read_newick(s, factor = 0):
    # factor is the factor by which the times of internal nodes are multiplied to receive integer-valued times. Default: 0 -- ranked tree (we don't multiply be zero for ranked trees, instead we take the order of internal nodes if factor == 0)
    factor = float(factor)

    children = dict() # contains children for all internal nodes (as sets)
    int_node_index = 1 # index of next internal node (they get names intX)
    next_parent = list() # stack of added internal node that do not have two children yet. Next read node will get the last element in this list (i.e. on top of stack) as parent
    edges = dict() # length of edges above every node (internal and leaf)
    prev_node = str() # name of the previously considered node
    leaves = list() # list of leaf names

    # We ignore the first part of the sting up to the first bracket '(' which signals the beginning of the newick string.
    i = 0
    while s[i] != '(':
        i += 1
    i += 1 # Add one as we add a node for the bracket before starting the iteration:
    # Add node for root (for the first opening bracket '('):
    children['int0'] = set()
    next_parent.append('int0')

    while i < len(s) - 1: # We assume that first character is an opening bracket corresponding to the root.
        if s[i] == '(':
            new_node = 'int' + str(int_node_index)
            children[new_node] = set() # Empty set of children
            children[next_parent[len(next_parent) - 1]].add(new_node)
            int_node_index += 1
            prev_node = new_node
            next_parent.append(new_node) # Parent of new_node is the node on top of the next_parent stack
            i += 1
        elif s[i] == ')':
            prev_node = next_parent.pop(len(next_parent) - 1)
            i += 1
        elif s[i] == ',': # Commas can be ignored. We use parentheses to identify nodes
            i += 1
        elif s[i] == ':': # The next element after this is the edge length of the last considered node (which can be internal node or a leaf)
            # Read the numbers following the colon, this is the edge length of the edge leading to prev_node
            i += 1
            edge_length = str()
            while s[i].isnumeric() or s[i] == '.' or s[i] == 'E' or s[i] == 'e' or s[i] == '-':
                edge_length = edge_length + s[i]
                i += 1
            edges[prev_node] = float(edge_length)
        elif s[i] == ';': # We are at the end of the string
            break
        elif s[i] != '[':
            # We are at a leaf label
            name = str()
            while s[i] != ':':
                name = name + s[i]
                i += 1
            leaves.append(name)
            # Add leaf as child of node on top of next_parent
            children[next_parent[len(next_parent) - 1]].add(name)
            prev_node = name
        elif s[i] == '[':
            # There is some information behind a node in square brackets. We do not need this information, so we ignore it.
            while s[i] != ']':
                i += 1

    # We now need to convert our dicts 'children' and 'edge_lengths' into a TREE (as in C code)
    # First convert edge_list into an array times of times of internal nodes.
    # We can use the numbering of internal nodes here. Iterating backwards through their names means we go from leaf to root and can assign times to internal nodes
    times = dict()
    for i in range(len(children)-1, -1, -1):
        current_node = 'int' + str(i)
        child = children[current_node].pop() # Take an arbitrary child (and put back into set)
        children[current_node].add(child)
        if 'int' in child:
            times[current_node] = times[child] + edges[child]
        else:
            times[current_node] = edges[child]

    # We are now ready to use our information to create a tree in the C data structure
    num_nodes = 2*len(children)+1
    node_list = (NODE * num_nodes)()

    # empty child array for initialising the node_list.
    empty_children = (c_long * 2)()
    empty_children[0] = -1
    empty_children[1] = -1

    # Initialise Node list
    for i in range(0, num_nodes):
        node_list[i] = NODE(-1, empty_children, 0)

    leaves.sort() # Sort leaves alphabetical to save them in node_list

    # Create tree
    position = list(times.values()) # Times of internal nodes ordered in a list
    position.sort()
    if len(position) != len(set(position)):
        print('Error. There are internal nodes with equal times.')
        return(1)
    prev_node_time = -1
    for i in range(num_nodes-1, len(leaves)-1, -1):
        # We fill the node list from top to bottom
        current_node = max(times, key=times.get)

        # Get the integer-valued node time
        if factor > 0: # In practice we expect factor to be much larger than 1!
            node_time = int(math.ceil(times.pop(current_node)*factor)) # We multiply times by factor and round them up to next integer
        else: # In this case we return a ranked tree
            times.pop(current_node)
            node_time = i - len(leaves) + 1
        if prev_node_time > -1 and node_time >= prev_node_time:
            # If there is already a node with this time we need to pick the next lower time that is not taken yet
            # This is prev_node_time - 1
            node_time = prev_node_time - 1
            prev_node_time = node_time
        if node_time == 0:
            print('The factor for discretising trees needs to be bigger')
            return(1)
        # Set node time in C data structure
        node_list[i].time = node_time

        # Find children and add data to C data structure
        child_1 = children[current_node].pop()
        child_2 = children[current_node].pop()
        # Distinguish whether child is leaf or not to get correct index in node_list
        if 'int' in child_1:
            child_rank = position.index(times[child_1])
            node_list[i].children[0] = child_rank + len(leaves)
            node_list[child_rank + len(leaves)].parent = i
        else:
            node_list[i].children[0] = leaves.index(child_1)
            node_list[leaves.index(child_1)].parent = i
        if 'int' in child_2:
            child_rank = position.index(times[child_2])
            node_list[i].children[1] = child_rank + len(leaves)
            node_list[child_rank + len(leaves)].parent = i
        else:
            node_list[i].children[1] = leaves.index(child_2)
            node_list[leaves.index(child_2)].parent = i
        # We keep the node time for the next iteration to make sure no two nodes get the same time
        prev_node_time = node_time
    # Check if we got the correct tree
    # for i in range(0, num_nodes):
    #     print('current node: ', i)
    #     print('parents: ', node_list[i].parent)
    #     print('children:', node_list[i].children[0], node_list[i].children[1])
        # print('times: ', node_list[i].time)

    # Create and return output tree:
    num_leaves = len(leaves)
    output_tree = TREE(node_list, num_leaves, node_list[num_nodes - 1].time, -1)
    return output_tree


# Read trees from nexus file and save leaf labels as dict and trees as TREE_LIST
def read_nexus(file_handle, factor=0): # factor is the factor for discretising trees -- see read_newick. If 0, we read trees as ranked trees.
    # Precompiled Regex for a line containing a tree
    re_tree = re.compile("\t?tree .*=? (.*);$", flags=re.I | re.MULTILINE)
    # Used to delete the ; and a potential branchlength of the root

    # Count the number of lines fitting the tree regex
    num_trees = len(re_tree.findall(open(file_handle).read()))
    # running variables for reading trees
    index = 0

    trees = (TREE * num_trees)()  # Save trees in an array to give to output TREE_LIST
    max_root_time = 0 # Maximum root time of the trees in the given file

    # If leaf label dict is needed, see the dtt-package or Summarizing-ran... repository!

    # Regex to delete additional data in []
    brackets = re.compile(r'\[[^\]]*\]')

    with open(file_handle, 'r') as f:
        # Read trees
        for line in f:
            if re_tree.match(line):
                # First extract the newick string and then delete everything after the last occurence of ')'
                tree_string = f'{re.split(re_tree, line)[1][:re.split(re_tree, line)[1].rfind(")")+1]};'
                t = read_newick(re.sub(brackets, "", tree_string), factor)
                if t != 1:
                    trees[index] = t
                    max_root_time = max(max_root_time,t.tree[2*t.num_leaves-2].time) # update root time (if necessary)
                else:
                    print("Couldn't read all trees in file, choose higher value for 'factor'.")
                    return(1)
                index += 1

    return TREE_LIST(trees, num_trees, max_root_time)


def read_from_cluster(s):
    # Note that we assume that leafs are labelled by integers
    # Read a tree from a string s that is the cluster representation of the tree (with times)
    clusters = s.split("{")
    leaf_pattern = re.compile(r'([^,^}^:]*)[,}\]]')
    num_leaves = len(clusters)
    highest_ancestor=[] # save highest ancestor for leaf i that we already found at position i

    # We are now ready to use our information to create a tree in the C data structure
    num_nodes = 2*num_leaves-1
    node_list = (NODE * num_nodes)()

    # empty child array for initialising the node_list.
    empty_children = (c_long * 2)()
    empty_children[0] = -1
    empty_children[1] = -1

    # Initialise Node list
    for i in range(0, num_nodes):
        node_list[i] = NODE(-1, empty_children, 0)
        if i >= num_leaves:
            node_list[i].time = i - (num_leaves-1)

    for i in range(0,num_leaves):
        highest_ancestor.append(i)
    for i in range(1,num_leaves):
        # print('cluster:', clusters[i])
        # print('highest_ancestor:', highest_ancestor)
        m = leaf_pattern.findall(clusters[i])
        # print('m:', m)
        child1 = -1
        child2 = -1
        for k in range(0,len(m)-1): # loop through elements in clusters (last element in m is time of cluster)
            leaf = m[k]
            # print('leaf:', leaf)
            leaf_index = int(leaf)-1
            if child1 == -1:
                child1 = highest_ancestor[leaf_index]
            elif child1 != highest_ancestor[leaf_index]:
                child2 = highest_ancestor[leaf_index]
            # print('children:', child1, child2)
            highest_ancestor[leaf_index]=i+num_leaves-1
        node_list[i+num_leaves-1].children[0]=child1
        node_list[i+num_leaves-1].children[1]=child2
        node_list[child1].parent = i+num_leaves-1
        node_list[child2].parent = i+num_leaves-1
        node_list[i+num_leaves-1].time = int(m[-1])

    # # Check if we got the correct tree
    # for i in range(0, num_nodes):
    #     print('current node: ', i)
    #     print('parents: ', node_list[i].parent)
    #     print('children:', node_list[i].children[0], node_list[i].children[1])
    #     print('time: ', node_list[i].time)

    output_tree = TREE(node_list, num_leaves, node_list[num_nodes - 1].time, -1)
    return output_tree