#ifndef TREE_H_
#define TREE_H_


/* A Node is either an internal node or a leaf of a DCT tree.
 * long parent The position of the node's parent in the tree array.
 * long children[2] The position of the node's children in the tree array.
 * children[0] is the left child, children[1] is the right child. If the node
 * is a leaf node, the children are -1.
 * long time The time of the node. Each internal node is assigned a unique
 * time. All leaves have times of 0.
 */
typedef struct Node {
  long parent;
  long children[2];
  long time;
} Node;

/* A Tree is a set of nodes.
 * Node * trees The nodes of tree, stored in an array. The first n nodes are
 * leaves, followed by the internal nodes.
 * long num_leaves The amount of leaves in the tree.
 * long root_time The time of the root node.
 * long sos_d The sum of squared distances of the tree to each tree in a given
 *tree list. Used to summarize trees.
 */
typedef struct Tree{
  Node * tree;
  long num_leaves;
  long root_time;
  long sos_d;
} Tree;


/* A Tree List is a list of trees.
 * Tree * trees The list of trees, stored in an array.
 * int num_trees The number of trees in the list.
 */
typedef struct Tree_List{
  Tree * trees;
  long num_trees;
  long max_root_time;
} Tree_List;

/* A Path is a matrix representation of a list of moves to convert one tree
 * into another. Each row represents a move. Please read
 * data_structures.md for more explanation.
 * long ** moves The path matrix.
 * long length The length of the path.
 */
typedef struct Path{
  long ** moves;
  long length;
} Path;

extern Tree read_tree_from_string(int, char*);
extern Tree_List one_neighbourhood(Tree *t);
extern Tree_List one_suburb(Tree *t, long max_root_time);
extern Tree_List read_trees_from_file(char* filename);
extern char *tree_to_string(Tree *t);
extern void free_tree_list(Tree_List *tl);
extern Path findpath(Tree * start_tree, Tree * dest_tree);
extern long findpath_distance(Tree *start_tree, Tree *dest_tree);
extern Tree_List return_findpath(Tree_List tree_list);
extern Tree follow_path(Path * p, Tree * start_tree, long path_index);
extern int copy_tree(Tree *source_tree, Tree *dest_tree);
extern int get_num_digits(int);
extern void *emalloc(size_t);
extern void print_tree_info(Tree*);

#endif
