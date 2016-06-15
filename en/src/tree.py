import sys
import re

from common import is_punc
logs = sys.stderr

class Tree(object):
    __slots__ = ('sent_id', 'tree_text', 'root')

    def __init__(self, tree_text, sent_id):
        self.sent_id = sent_id
        self.tree_text = tree_text.strip()
        if self.tree_text == "(())":
            return None
        self.tree_text = re.sub(r'\(ROOT\n*', '( ', self.tree_text)
        self.tree_text = re.sub(r'\(S1 ', '( ', self.tree_text)
        self.tree_text = re.sub(r'\(TOP ', '( ', self.tree_text)
        self.tree_text = re.sub(r'\s+', ' ', self.tree_text)
        self.tree_text = re.sub(r'^\(\s*\(\s*', '', self.tree_text)
        self.tree_text = re.sub(r'\s*\)\s*\)$', '', self.tree_text)
        self.tree_text = re.sub(r'\(', ' ( ', self.tree_text)
        self.tree_text = re.sub(r'\)', ' ) ', self.tree_text)

        tokens = self.tree_text.split()
        stack = []
        for token in tokens:
            if token != ')':
                stack.append(token)
            else:
                nodes = []
                while True:
                    popped = stack.pop()
                    if popped == '(':
                        break
                    nodes.insert(0, popped)
                node = Node(nodes.pop(0), nodes)
                node.tree = self
                stack.append(node)
        self.root = Node(stack.pop(0), stack)
        self.root.is_root = True
        self.root.tree = self

    def __str__(self):
        return self.tree_text

    __repr__ = __str__

    def is_null(self):
        return self.tree_text == "(())"

    def find_subtrees(self, leaves):
        if len(leaves) == 0:
            return []

        if len(self.root.get_leaves()) - len(leaves) <= 4:
            return [self.root]

        # bottom-top mark
        for n in leaves:
            n.recursive_up_mark()

        # up-down remove
        res = []
        Q = [self.root]
        while len(Q) != 0:
            node = Q.pop(0)
            flag = True
            for c in node.child_nodes:
                if not c.is_recursive_included():
                    flag = False
                    break
            if flag:
                res.append(node)
            else:
                for c in node.child_nodes:
                    if c.included:
                        Q.append(c)

        # unmark
        for n in leaves:
            n.recursive_up_unmark()
        return res

    def find_highest_common_ancestor(self, nodes):
        if len(nodes) == 0:
            print >> logs, "error: empty nodes"
            return
        else:
            lca = None
            queue = [self.root]
            while len(queue) != 0:
                curr = queue.pop(0)
                leaves = curr.get_leaves()
                if len(leaves) != 0 and len(set(leaves)-set(nodes)) == 0:
                    lca = curr
                    break
                else:
                    for ch in curr.child_nodes:
                        queue.append(ch)
            return lca

    @staticmethod
    def find_least_common_ancestor(nodes, with_leaves=False):
        if len(nodes) == 0:
            return None
        elif len(nodes) == 1:
            lca = nodes[0]
            if lca.is_leaf:
                lca = lca.parent_node
            return lca
        else:
            lca = None
            queue = [nodes[0].goto_tree().root]
            while len(queue) != 0:
                curr = queue.pop(0)
                if len(set(curr.get_all_nodes(with_leaves)) & (set(nodes))) == len(nodes):
                    lca = curr
                    for ch in curr.child_nodes:
                        queue.append(ch)
            return lca


    @staticmethod
    def relative_position(node1, node2):
        root = node1.goto_tree().root
        if node1 == node2 or node2 == root:
            return '0'
        curr = node1
        rsibs = []
        lsibs = []
        while curr != root:
            rsibs += curr.all_right_siblings()
            lsibs += curr.all_left_siblings()
            curr = curr.parent_node
            if curr == node2:
                return '0'
        for rsib in rsibs:
            if node2 in rsib.get_all_nodes():
                return '1'

        for lsib in lsibs:
            if node2 in lsib.get_all_nodes():
                return '2'

        return '0'

    @staticmethod
    def find_constituent_path(node1, node2, with_leaves=False):
        lca = Tree.find_least_common_ancestor([node1, node2], with_leaves)
        n1_to_lca = Tree.find_upward_path(node1, lca)
        n2_to_lca = Tree.find_upward_path(node2, lca)

        path = ''
        if len(n1_to_lca) > 0 :
            path += ('->').join(n1_to_lca)
        if len(n2_to_lca) > 0:
            n2_to_lca.pop()
            if len(n2_to_lca) > 0:
                n2_to_lca.reverse()
                path += '<-'+('<-').join(n2_to_lca)

        n1_to_lca2 = []
        prev = None
        for a in n1_to_lca:
            if a != prev :
                n1_to_lca2.append(a)
                prev = a

        n2_to_lca2 = []
        prev = None
        for a in n2_to_lca:
            if a != prev :
                n2_to_lca2.append(a)
                prev = a

        path2 = ''
        if len(n1_to_lca2) > 0 :
            path2 += ('->').join(n1_to_lca2)
        if len(n2_to_lca2) > 0:
            n2_to_lca2.reverse()
            path2 += '<-' + ('<-').join(n2_to_lca2)

        return path, path2

    @staticmethod
    def find_upward_path(node1, node2):
        if node1 == node2:
            return []
        curr = node1
        path = []
        while curr != node2 and curr is not None:
            path.append(curr.value)
            curr = curr.parent_node
        if curr == node2 and curr is not None:
            path.append(curr.value)
        if curr == None:
            return []
        else:
            return path

class Node(object):
    __slots__ = ('value', 'lowercased', 'child_nodes', 'parent_node', 'is_root', 'is_pos',
                 'leaf_node', 'fun_tag', 'is_leaf', 'size', 'tree',
                 'is_NONE_leaf', 'included', 'dep', 'lemmatized', 'stem', 'is_conn', 'linker', 'leaf_id', 'sbar_1st_leaf')

    def __init__(self, value, child_nodes):
        self.value = value
        self.lowercased = self.value.lower()
        self.stem = ''
        self.child_nodes = child_nodes
        self.parent_node = None
        self.is_root = False
        self.is_pos = False
        self.is_leaf = False
        self.is_conn = False
        self.linker = 'None'
        self.size = 0
        self.tree = None
        self.is_NONE_leaf = False
        self.included = False
        self.dep = None
        self.leaf_id = -1  # document level
        self.sbar_1st_leaf = False

        if len(self.child_nodes) == 1 and not isinstance(self.child_nodes[0], Node):
            self.is_pos = True
            leaf_node = self.child_nodes[0] = Node(child_nodes[0], [])
            leaf_node.is_leaf = True
            leaf_node.value = re.sub(r'_', '-', leaf_node.value)
            self.leaf_node = self.child_nodes[0]
            if re.search(r'-NONE-', self.value):
                self.leaf_node.is_NONE_leaf = True

        if not self.is_pos and len(self.child_nodes) > 0:
            self.value = re.sub(r'=\d+', '', self.value)
            if re.search(r'|', self.value):
                tokens = self.value.split('|')
                self.value = tokens[0]

            if re.search(r'.-.', self.value):
                fun_tag = self.value[self.value.index('-') + 1:-1]
                fun_tag = re.sub(r'--+', '-', re.sub(r'\b\d+\b', '', fun_tag))
                self.fun_tag = fun_tag
                if self.fun_tag == '':
                    self.fun_tag = None
                self.value = self.value[0:self.value.index('-')]

        if not self.is_leaf:
            for node in child_nodes:
                node.parent_node = self

    def __str__(self):
        return '%s:%s' % (self.value, ' '.join(n.value for n in self.get_leaves()))

    def get_all_nodes(self, with_leaves=False):
        all_nodes = []
        self.get_all_nodes_rec(all_nodes, with_leaves)
        return all_nodes

    def get_all_nodes_rec(self, nodes, with_leaves=False):
        if self.is_leaf:
            if with_leaves:
                nodes.append(self)
        else:
            nodes.append(self)
        for c in self.child_nodes:
            c.get_all_nodes_rec(nodes, with_leaves)

    def contains_trace(self):
        if self.is_NONE_leaf and re.search(r'^\*T\*-', self.value):
            return True
        else:
            for ch in self.child_nodes:
                if ch.contains_trace():
                    return True
            return False

    def contains_node_with_value(self, v):
        if self.value == v:
            return True
        else:
            for ch in self.child_nodes:
                if ch.contains_node_with_value(v):
                    return True
            return False

    def get_leaves(self):
        arr = []
        self.get_leaves_rec(arr)
        return arr

    def get_leaves_rec(self, arr):
        if self.is_leaf and not self.is_NONE_leaf:
            arr.append(self)
        else:
            for ch in self.child_nodes:
                ch.get_leaves_rec(arr)

    def goto_tree(self):
        if not self.is_root:
            return self.parent_node.goto_tree()
        else:
            return self.tree

    def label_node_size(self):
        if self.is_leaf and self.is_NONE_leaf:
            self.size = 0
        elif self.is_leaf and not self.is_NONE_leaf:
            self.size = 1
        else:
            tmp = 0
            for ch in self.child_nodes:
                tmp += ch.label_node_size()
            self.size = tmp

        return self.size

    def mark_subtree_included(self):
        self.included = True
        for ch in self.child_nodes:
            ch.mark_subtree_included()

    def unmark_subtree_included(self):
        self.included = False
        for ch in self.child_nodes:
            ch.unmark_subtree_included()

    def pre_order(self):
        """ print ptb style tree"""
        if self.is_leaf:
            to_line = "%s" % self.value
        else:
            to_line = "(%s " % self.value

        for n in self.child_nodes:
            to_line += n.pre_order()
        if not self.is_leaf:
            to_line += ") "
        return to_line

    def pre_order_included(self, with_leaf=False):
        """
        pre order print parse tree (designed for tree kernel)
        """
        if not self.included:
            to_line = ''
        elif self.is_leaf:
            to_line = "%s" % self.value
        else:
            if with_leaf and self.value == '-NONE-':
                return ''
            else:
                to_line = "(%s " % self.value

        sub_line = ''
        for n in self.child_nodes:
            sub_line += n.pre_order_included(with_leaf)
        if to_line != '' and not self.is_leaf and sub_line == '':
            sub_line = 'null'

        to_line += sub_line
        if not self.is_leaf and self.included:
            to_line += ")"
        return to_line

    def get_len_of_verb_phrases(self, arr=[]):
        """ get verb phrases length
        """
        if self.value == 'VP':
            arr.append(len(self.get_leaves()))

        for ch in self.child_nodes:
            ch.get_len_of_verb_phrases(arr)

    def get_production_rules(self, rule_cnts, nary=2, with_leaf=True):
        if not self.is_pos:
            if re.search(r'.-.', self.value):
                rule = self.value[:self.value.index('-') + 1] + '->'
            else:
                rule = self.value + '->'
            child_ptr = [n for n in self.child_nodes
                         if n.value.find('-NONE-') == -1]
            if nary != -1 and len(child_ptr) > nary:
                for i in range(len(child_ptr) - nary):
                    rule2 = rule + '_'.join(n.value for n in child_ptr[i:i + nary])
                    rule_cnts[rule2] += 1
            else:
                rule += '_'.join(n.value for n in child_ptr)
                if not re.search('->$', rule):  # rule has child values
                    rule_cnts[rule] += 1
            for n in child_ptr:
                n.get_production_rules(rule_cnts, nary, with_leaf)
        elif with_leaf and self.value.find('-NONE-') == -1:
            rule_cnts[self.value + '->' + self.leaf_node.value] += 1

    def get_unary_production_rules(self, rule_cnts, with_leaf=True):
        """decompose production rules as unary rule, e.g. S->VP NP,
        we will get S->VP, S->NP two production rules
        """
        if not self.is_pos:
            if re.search(r'.-.', self.value):
                rule = self.value[:self.value.index('-') + 1] + '->'
            else:
                rule = self.value + '->'
            child_ptr = [n for n in self.child_nodes
                         if n.value.find('-NONE-') == -1]
            for n in child_ptr:
                t = rule + n.value
                if not re.search('->$', t):
                    rule_cnts[t] += 1
                n.get_unary_production_rules(rule_cnts, with_leaf)
        elif with_leaf and self.value.find('-NONE-') == -1:
            rule_cnts[self.value + '->' + self.leaf_node.value] += 1

    def recursive_up_mark(self):
        p = self
        while p is not None:
            p.included = True
            p = p.parent_node

    def recursive_up_unmark(self):
        p = self
        while p is not None:
            p.included = False
            p = p.parent_node

    def is_recursive_included(self):
        if self.is_leaf:
            return self.included
        else:
            for c in self.child_nodes:
                if not c.is_recursive_included():
                    return False
            return True

    def all_left_siblings(self, remove_punc=False):
        if self.parent_node is not None:
            i = self.parent_node.child_nodes.index(self)
            if i > 0 :
                if remove_punc:
                    return [n for n in self.parent_node.child_nodes[0:i]
                            if not is_punc(n.value)]
                else:
                    return self.parent_node.child_nodes[0:i]
        return []

    def all_right_siblings(self, remove_punc=False):
        if self.parent_node is not None:
            i = self.parent_node.child_nodes.index(self)
            if i < len(self.parent_node.child_nodes)-1 :
                if remove_punc:
                    return [n for n in self.parent_node.child_nodes[i+1:len(self.parent_node.child_nodes)]
                            if not is_punc(n.value)]
                else:
                    return self.parent_node.child_nodes[i+1:len(self.parent_node.child_nodes)]
        return []

    def recursive_set_linker(self, v):
        self.linker = v
        for n in self.child_nodes:
            n.recursive_set_linker(v)

    def mark_edge_1st_leaves(self, all_leavs):
        if len(all_leavs) <= 0:
            return

        if (self.value == 'SBAR' and self.parent_node is not None and self.parent_node.value == 'VP') or \
            (self.value == 'SINV' and self.parent_node is not None and self.parent_node.value == 'S') or \
            (self.value == 'S' and self.parent_node is not None and self.parent_node.value == 'S') or \
            (self.value == 'S' and self.parent_node is not None and self.parent_node.value == 'SINV') or \
            (self.value == 'SBAR' and self.parent_node is not None and self.parent_node.value == 'S'):
                arr = self.get_leaves()
                last_idx = all_leavs.index(arr[-1])
                if len(arr) > 0:
                    arr[0].sbar_1st_leaf = True
                    if last_idx < len(all_leavs) - 1:
                        all_leavs[last_idx+1].sbar_1st_leaf = True
                arr = []

        for child in self.child_nodes:
            child.mark_edge_1st_leaves(all_leavs)

