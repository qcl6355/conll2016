__author__ = 'Sheng Li'
import sys
from tree import Tree
from deptree import DepTree
import copy

from common import CONN_INTRA, CONN_GROUP, CLAUSE_PUNCS

class Sentence(object):
    __slots__ = ('leaves', 'id', 'tree', 'true_connectives', 'checked_connectives', 'depTree', 'words', 'word_ids',
            'begin_offset', 'end_offset', 'clauses')

    def __init__(self, sent_id, parse_tree, dep_tree, words):
        self.leaves = []
        self.id = sent_id
        self.tree = Tree(parse_tree, sent_id)
        self.get_leaves()
        self.words = words
        self.begin_offset = words[0][1]['CharacterOffsetBegin']
        self.end_offset = words[-1][1]['CharacterOffsetEnd']
        self.word_ids = []
        self.true_connectives = []
        self.checked_connectives = []
        self.depTree = DepTree(self, dep_tree)
        self.clauses = []
        self.break_clauses()

    def get_leaves(self):
        if not self.tree.is_null():
            self.leaves = self.tree.root.get_leaves()

    def _find_intra_conn(self, conn_parts, n, k, offset, checked, alls):
        if n == k:
            if len(checked) == n:
                alls.append(checked)
        else:
            length = len(self.leaves)
            conns = conn_parts[k].split()
            len_conns = len(conns)
            prev_checked = copy.copy(checked)

            for i in range(offset, length - len_conns + 1):
                ok = True
                curr = []
                for j in range(len_conns):
                    if conns[j] != self.leaves[i+j].value:
                        ok = False
                        break
                    else:
                        curr.append(self.leaves[i+j])
                if ok and len(curr) != 0:
                    checked.append(curr)
                    self._find_intra_conn(conn_parts, n, k+1, i+len_conns, checked, alls)
                    checked = prev_checked

    def check_intra_connectives(self):
        for a in CONN_INTRA:
            conn_parts = a.split('..')
            alls = []
            check = []
            self._find_intra_conn(conn_parts, len(conn_parts), 0, 0, check, alls)
            if len(alls) > 0:
                for can in alls:
                    print ' '.join(n.value for n in can), '||', a

    def check_connectives(self):
        length = len(self.leaves)
        for a in CONN_INTRA:
            conn_parts = a.split('..')
            alls = []
            check = []
            self._find_intra_conn(conn_parts, len(conn_parts), 0, 0, check, alls)
            if len(alls) > 0:
                for can in alls:
                    t = []
                    for c in can:
                        t += c
                    self.checked_connectives.append(t)

        for a in CONN_GROUP:
            conns = a.split()
            len_conns = len(conns)
            for i in range(length-len_conns+1):
                ok = True
                checked = []
                for j in range(len_conns):
                    if conns[j] != self.leaves[i+j].value:
                        ok = False
                        break
                    else:
                        checked.append(self.leaves[i+j])

                if ok:
                    self.checked_connectives.append(checked)
        return self.checked_connectives

    def get_syntactic_features(self, self_node, parent_node, left_sib_node, right_sib_node):
        curr = self_node
        self_to_root = curr.value
        self_to_root2 = curr.value
        while curr != self.tree.root:
            prev = curr
            curr = curr.parent_node
            self_to_root += '_>_'+curr.value
            if prev.value != curr.value:
                self_to_root2 += '_>_'+curr.value

        return [self_to_root, self_to_root2]

    def get_production_rules(self, conn_leaves, rules={}):
        if len(conn_leaves) == 1:
            curr = conn_leaves[0].parent_node
        else:
            tree = conn_leaves[0].goto_tree()
            curr = tree.find_least_common_ancestor(conn_leaves, with_leaves = True)
        curr.get_production_rules(rules, -1)

    def get_connective_categories(self, conn_leaves):
        self_cat = parent_cat = left_cat = right_cat = 'NONE'
        tree = conn_leaves[0].goto_tree()
        curr = tree.find_highest_common_ancestor(conn_leaves)
        parent = curr.parent_node

        self_cat = curr.value
        right_VP = False
        right_trace = False
        left_sib = None
        right_sib = None
        if parent != None:
            parent_cat = parent.value
            i = parent.child_nodes.index(curr)
            if i > 0:
                left_cat = parent.child_nodes[i-1].value
                left_sib = parent.child_nodes[i-1]

            if i < len(parent.child_nodes)-1 :
                right_cat = parent.child_nodes[i+1].value
                right_sib = parent.child_nodes[i+1]
                if right_sib.contains_node_with_value('VP'):
                    right_VP = True
                if right_sib.contains_trace():
                    right_trace = True

        return [self_cat, parent_cat, left_cat,right_cat, right_VP, right_trace,[curr, parent, left_sib, right_sib]]

    def break_clauses(self):
        # use puncs to separate sentence
        self.clauses = []
        curr_clause = []
        for leaf in self.leaves:
            curr_clause.append(leaf)
            if leaf.value in CLAUSE_PUNCS:
                self.clauses.append(curr_clause)
                curr_clause = []
        if len(curr_clause) > 0:
            self.clauses.append(curr_clause)


    def __str__(self):
        return "sid:%s %s; begin_offset:%s, end_offset:%s" % (self.id, str(self.tree), self.begin_offset, self.end_offset)

    __repr__ = __str__

    def print_clauses(self):
        arr = []
        for clause in self.clauses:
            arr.append('_'.join(l.value for l in clause))
        return  '|'.join(arr)
