__author__ = 'Lena Collienne'
# Handling Tree input and output (to C)
# Written by Lena Collienne, modified by Jordan Kettles.

import sys
import math
import re
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
    #print("Updating the children of {}, node {} & node {}.").format(node, children_list[0], children_list[1])
    #print(children_list[0] + " " + children_list[1])

    if len(in1) > 0:
        inhdict = update_child(pdict, cdict, inhdict, int(in1[0]), pheight, dif)
    if len(in2) > 0:
        inhdict = update_child(pdict, cdict, inhdict, int(in2[0]), pheight, dif)
    return inhdict

# Read tree from string s in newick format -- assuming that the given tree is ultrametric!!
def read_newick(s, ranked = False):
    num_nodes = s.count(':') + 1 # number of nodes in input tree (internal nodes + leaves), root does not have ':'
    num_int_nodes = int((num_nodes - 1) / 2)
    num_leaves = int(num_nodes - num_int_nodes)


    tree_str = str(s) # copy input string -- we are going to manipulate it

    # While reading the newick string, we save the tree in the following way, converting it to C TREE afterwards
    int_node_index = 0 # index of current internal node -- NOT rank!
    parent_dict = dict() # for each node (leaves + internal) save index of parent (int_node_index)
    int_node_height = dict() # heights for all internal nodes (distance to leaves)

    child_dict = dict() #index of the two children of an internal node.


    #sets all leaf lengths to length 0.0.
    if (ranked == False):
        leaf_length = "\g<1>0.0"
        tree_str = re.sub(r'(\d+:)\d*.\d*', leaf_length, tree_str)
    # print(tree_str)


    while (len(tree_str) > 0): # recurses over tree and replace internal nodes with leaves labelled by
    #internal_nodei for int i and save information about internal node height and children

        if int_node_index < num_int_nodes - 1: # as long as we don't reach the root
            pattern = r'\(([^:\()]+):(\[[^\]]*\])?((\d+.\d+(?:e|E)?\-?\d*)|(\d+)),([^:\()]+):(\[[^\]]*\])?((\d+.\d+(?:e|E)?\-?\d*)|(\d+))\):(\[[^\]]*\])?((\d+.\d+(?:e|E)?\-?\d*)|(\d+))'
        else: # we reach the root -- string of form '(node1:x,node2:y)' left
            pattern = r'\(([^:\()]+):(\[[^\]]*\])?((\d+.\d+E?\-?\d?)|(\d+)),([^:\()]+):(\[[^\]]*\])?((\d+.\d+E?\-?\d?)|(\d+))\);?'

        print(tree_str)
        int_node_str = re.search(pattern, tree_str)

        #print("-- #{} --").format(int_node_index)
        #print(int_node_str.group())

        # Save new internal node as parent of its two children
        parent_dict[int_node_str.group(1)] = int_node_index
        parent_dict[int_node_str.group(6)] = int_node_index

        #Save new internal node as a parent of two children.
        child_dict[int_node_index] = [int_node_str.group(1), int_node_str.group(6)]

        left = float(int_node_str.group(3))
        right = float(int_node_str.group(8))

        if left > right:
            int_node_height[int_node_index] = left
        else: #right is greater or equal to leaf
            int_node_height[int_node_index] = right

        #re.findall finds the internal nodes of the new internal node.
        child_nums = re.findall(r"internal_node(\d*)", int_node_str.group())

        child_lengths = list() # List of the heights of the children of the
        #current node.

        #Adds the height of each internal node to a list.
        for num in child_nums:
            child_lengths.append(int_node_height[int(num)])

        #If there are two internal nodes, we must update the height of one of
        # them, and all of its children.
        if len(child_nums) == 2:
            #print("0 (L): {}, 1 (R): {}").format(child_lengths[0], child_lengths[1])
            if child_lengths[0] > child_lengths[1]:
                if left > right:
                    int_node_height[int(child_nums[1])] = left - right + child_lengths[1]
                    #print("1Set child {} to height {}.").format(child_nums[1], int_node_height[int(child_nums[1])])
                    int_node_height = update_children(parent_dict, child_dict, int_node_height, int(child_nums[1]), int_node_height[int(child_nums[1])], child_lengths[1])
                else:
                    int_node_height[int(child_nums[0])] = right - (left - child_lengths[0])
                    #print("2Set child {} to height {}.").format(child_nums[0], int_node_height[int(child_nums[0])])
                    int_node_height = update_children(parent_dict, child_dict, int_node_height, int(child_nums[0]), int_node_height[int(child_nums[0])], child_lengths[0])
            else:
                if right > left:
                    int_node_height[int(child_nums[0])] = right - left + child_lengths[0]
                    #print("3Set child {} to height {}.").format(child_nums[0], int_node_height[int(child_nums[0])])
                    int_node_height = update_children(parent_dict, child_dict, int_node_height, int(child_nums[0]), int_node_height[int(child_nums[0])], child_lengths[0])
                else:
                    int_node_height[int(child_nums[1])] = left - (right - child_lengths[1])
                    #print("4Set child {} to height {}.").format(child_nums[1], int_node_height[int(child_nums[1])])
                    int_node_height = update_children(parent_dict, child_dict, int_node_height, int(child_nums[1]), int_node_height[int(child_nums[1])], child_lengths[1])

        if int_node_index < num_int_nodes - 1: # excludes root; insert new leaf 'internal_nodei' replacing the found pattern (pair of leaves)
            #inserts internal node, with the branch length
            repl = "internal_node" + str(int_node_index) + ":" + str(float(int_node_str.group(12)) + int_node_height[int_node_index])
            tree_str = re.sub(pattern, repl, tree_str, count = 1)
            int_node_index += 1
        else: # If we consider root, replace tree_str with empty str
            tree_str = ''

    # Now we use parent_list and int_node_height to create tree in C TREE data structure
    node_list = (NODE * num_nodes)()
    node_name_list = [] # Save the names of leaves in a list, such that entry i corresponds to leaf at position i in node list of tree structure

    #empty child array for initialising the node_list.
    empty_children = (c_long * 2)()
    empty_children[0] = -1
    empty_children[1] = -1

    # Initialise Node list
    for i in range(0, num_nodes):
        node_list[i] = NODE(-1, empty_children, 0)
        node_name_list.append('')

    # sort internal nodes according to rank/times (increasing) -- output: list of keys (indices of internal nodes)
    int_node_list = [key for key, val in sorted(int_node_height.items(), key=lambda item:item[1])]
    # sort internal times according to time. -- output: List of times.
    int_node_times = [key for key, key in sorted(int_node_height.items(), key=lambda item:item[1])]
    #print(int_node_times)

    #jordan version
    #Find the shortest branch between two times.

    # Use the shortest branch as the base measure of time for the tree.
    # For this version, when comparing two trees their shortest branch may
    # be different, so a length move on one tree may not be equal to a length
    # move on another tree.

    shortest_branch = int_node_times[1];
    for i in range(1,num_int_nodes-1):
        if(shortest_branch == 0):
            shortest_branch = int_node_times[i]
        if((int_node_times[i+1] - int_node_times[i]) < shortest_branch):
            shortest_branch = (int_node_times[i+1] - int_node_times[i])


    #Lars version (incomplete)
    # shortest_branch = 21.1494 / (num_leaves - 1);


    # print("The shortest branch is: " + str(shortest_branch))




    # Makes the height of the first internal node 1, then discretizes all
    # following nodes as natural numbers using the shortest branch.
    for i in range(0,num_int_nodes):
        int_node_times[i] = int(round(int_node_times[i] / shortest_branch)) + 1
        if ranked == False:
            int_node_times[i] -= 1
        if(int_node_times[i] == int_node_times[i-1]):
            sys.exit("Times are not discrete! Decrease the shortest branch!")
        # int_node_times[i] = i+1
        # print(int_node_times[i])

    leaf_index = 0 # Index for leaves, they are ordered alphabetical! (To make sure that two trees on same leaf set have same mapping of position in NODE array to label)
    #sort parent_dict alphabetically.
    parent_dict = OrderedDict(sorted(parent_dict.items(), key=lambda item: item[0]))

    for node in parent_dict:
        int_node_str = re.search(r'internal_node(\d*)', node)
        if int_node_str != None: # Consider internal node

            child_rank = num_leaves + int_node_list.index(int(int_node_str.group(1)))
            parent_rank = num_leaves + int_node_list.index(int(parent_dict[int_node_str.group()]))
            node_name_list[parent_rank] = str(node)
            # Set parent
            node_list[child_rank].parent = parent_rank
            node_list[child_rank].time = int_node_times[child_rank - num_leaves]
            # Set children (only one, make sure to use the slot children[0] ot children[1] that is not used already)
            if (node_list[parent_rank].children[0] == -1):
                node_list[parent_rank].children[0] = child_rank
            else:
                node_list[parent_rank].children[1] = child_rank
        else: # Consider leaf
            parent_rank = num_leaves + int_node_list.index(int(parent_dict[node]))
            node_int = leaf_index
            # Set parent
            node_list[node_int].parent = parent_rank
            # set time of every leaf to 0.
            node_list[node_int].time = 0
            # Set children (only one, make sure to use the slot children[0] ot children[1] that is not used already)
            if (node_list[parent_rank].children[0] == -1):
                node_list[parent_rank].children[0] = node_int
            else:
                node_list[parent_rank].children[1] = node_int
            node_name_list[node_int] = str(node)
            leaf_index += 1

    node_list[num_nodes-1].time = int_node_times[num_int_nodes-1]

    output_tree = TREE(node_list, num_leaves, node_list[num_nodes-1].time, -1)
    return(output_tree)

# Read trees from nexus file and save leaf labels as dict and trees as TREE_LIST
def read_nexus(file_handle):

    # To get the number of trees in the given file, we find the first and last line in the file that contain a tree (Line starts with tree)
    # Count number of lines in file
    number_of_lines = len(open(file_handle).readlines())
    last_line = number_of_lines

    # Find last line containing a tree
    for line in reversed(list(open(file_handle))):
        re_tree = re.search(r'^TREE |^tree', line)
        if re_tree == None:
            last_line -= 1
        else: break

    # Find first line containing a tree
    first_line = 1
    for line in list(open(file_handle)):
        re_tree = re.search(r'^TREE|^tree', line)
        if re_tree == None:
            first_line += 1
        else: break

    num_trees = last_line - first_line + 1 # Number of trees in nexus file


    # running variables for reading trees and displaying progress
    index = 0
    progress = 10

    #num_trees = 2
    # ^^for debugging

    name_dict = dict() # Save tree label names in dict
    trees = (TREE * num_trees)() # Save trees in an array to give to output TREE_LIST


    f = open(file_handle, 'r')
    # leaf_labels = False
    # # Save leaf labels -- returns empty dict if no abbreviation for leaf labels is used
    # for line in f:
    #     if re.search(r'translate', line, re.I) != None:
    #         leaf_labels = True
    #     # Start reading leaf labels after 'translate' (signals start of this sequence)
    #     if leaf_labels == True:
    #         re_label = re.search(r'\s*(.+)\s(.+),', line)
    #         re_stop = re.search(r';', line)
    #         if re_stop != None:
    #             break
    #         elif re_label != None:
    #             name_dict[re_label.group(1)] = re_label.group(2)

    # Read trees
    for line in f:
        if num_trees > index:
            # re_tree = re.search(r'(?:TREE|tree) .* (\(.*\);)', line)
            re_tree = re.search(r'(?:tree|TREE) .* (\(.*\))(?:\:0\.0)?;', line)
            if re_tree != None:
                current_tree = read_newick(re_tree.group(1))
                trees[index] = current_tree
                index += 1
                if int(100*index/num_trees) == progress:
                    print(str(progress) + '% of trees are read')
                    progress += 10

    tree_list = TREE_LIST(trees, num_trees)
    f.close()

    return(tree_list, name_dict);