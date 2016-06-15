#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from collections import defaultdict

from common import *
from corpus import Corpus
from tree import Tree

logs = sys.stderr
FILE_PATH = os.path.dirname(os.path.abspath(__file__))


class Argument(object):
    def __init__(self):
        self.train_file = FILE_PATH + '/../data/conll.arg.train'
        self.train_vec_file = FILE_PATH + '/../data/conll.arg.train.vec'
        self.feat_map_file = FILE_PATH + '/../data/conll.arg.feat.map'
        self.test_file = FILE_PATH + '/../data/conll.arg.test'
        self.test_vec_file = FILE_PATH + '/../data/conll.arg.test.vec'
        self.model_file = FILE_PATH + '/../data/conll.arg.model'
        self.predicted_file = FILE_PATH + '/../data/conll.arg.test.predicted'

    def pruning(self, conn_node, relation, which):
        candidate = set()
        conn_leaves = relation.conn_leaves
        target = conn_node
        prune_level_limit = 7

        if which != 'test':
            relation.set_linker()
            prune_level_limit = 50000

        prune_level = 0
        while target is not None and prune_level < prune_level_limit:
            if target.parent_node is not None:
                siblings = target.parent_node.child_nodes
                candidate |= {(n, n.linker) for n in siblings if n != target}
            # target node doesn't cover conn leaves exactly
            exact_cover = len(target.get_leaves()) == len(conn_leaves)
            if not exact_cover:
                candidate |= {(n, n.linker) for n in target.child_nodes if n != conn_node}
            if which == 'test' and (target.value == 'IP' or target.value == 'S'):
                target = None
            else:
                target = target.parent_node
            prune_level += 1

        if which == 'train':
            # view previous root as a specifical constituent
            sid = conn_leaves[0].goto_tree().sent_id
            if sid > 0:
                prev_tree = relation.article.sentences[sid-1].tree
                if not prev_tree.is_null():
                    prev_root = prev_tree.root
                    if prev_root.linker == 'arg1' or prev_root.linker == 'arg2':
                        candidate.add( (prev_root, prev_root.linker) )
                    else:
                        candidate.add( (prev_root, 'None') )

        return candidate

    # N.B. In Chinese, if a connective is in the internal of an argument,
    # the annotation doesn't remove it from that argument. Strange!!
    def merge(self, relation, candidates, labels):
        conn_leaves = relation.conn_leaves
        arg_res = defaultdict(list)
        assert len(candidates) == len(labels), 'size not match'
        for node, label in zip(candidates, labels):
            if label != 'None':
                arg_res[label] += node.get_leaves()

        conn_set = set(conn_leaves)
        for label in arg_res:
            ltmp = list(set(arg_res[label]) - conn_set)
            ltmp = sorted(ltmp, key=lambda x:x.leaf_id)
            arg_res[label] = ltmp

        return arg_res

    # N.B. Assume all levaes are in the same sentence
    def recover_puncs(self, rel, arg_leaves):
        sid = arg_leaves[0].goto_tree().sent_id
        all_leaves = rel.article.sentences[sid].leaves
        res = []
        prev = None
        for leaf in all_leaves:
            if leaf in arg_leaves:
                prev = leaf
                res.append(leaf)
            elif is_punc(leaf.parent_node.value) and prev is not None:
                res.append(leaf)
            else:
                prev = None
        return res

    def print_features(self, relation, which, to_file, prev=None):
        conn_leaves = relation.conn_leaves
        conn_str = '_'.join(n.value for n in conn_leaves)
        conn_node = Tree.find_least_common_ancestor(conn_leaves, with_leaves=True)
        if conn_node is None:
            return []
        curr_root = conn_node.goto_tree().root
        if prev is not None:
            candidates = [(prev, 'None')]
        else:
            candidates = self.pruning(conn_node, relation, which)
        for node, label in candidates:
            to_file_line = ''
            to_file_line += 'conn:'+conn_str+' '
            to_file_line += 'nt_cat:'+node.value
            if node.parent_node is not None:
                to_file_line += '^nt_pt:' + node.parent_node.value
                curr_idx = node.parent_node.child_nodes.index(node)
                if curr_idx > 0:
                    to_file_line += '^nt_lsib:' + node.parent_node.child_nodes[curr_idx - 1].value
                else:
                    to_file_line += '^nt_lsib:NULL'

                if curr_idx < len(node.parent_node.child_nodes) - 1:
                    to_file_line += '^nt_rsib:' + node.parent_node.child_nodes[curr_idx + 1].value
                else:
                    to_file_line += '^nt_rsib:NULL'
            else:
                to_file_line += '^nt_pt:NULL'
            to_file_line += ' '
            node_root = node.goto_tree().root
            if curr_root != node_root:
                path, _ = Tree.find_constituent_path(conn_node, curr_root)
                path += '->_<cross>_->' + node_root.value
            else:
                path, _ = Tree.find_constituent_path(conn_node, node)
            relpos = Tree.relative_position(conn_node, node)
            to_file_line += 'conn_to_node:'+path+' '
            lsibs = conn_node.all_left_siblings()
            rsibs = conn_node.all_right_siblings()
            to_file_line += 'conn_node_lsib_size='+str(len(lsibs))+' '
            to_file_line += 'conn_node_rsib_size='+str(len(rsibs))+' '
            if len(lsibs) > 1 :
                to_file_line += 'conn_to_node:'+path+'^conn_node_lsib_size:>1 '

            to_file_line += 'conn_to_node_relpos:'+relpos+' '
            to_file.write('%s %s\n' % (to_file_line, ARG_LABEL_MAP[label]))

        return [c[0] for c in candidates]

    def need_extract(self, rel):
        """
        This function is used to filter some training instances,
        (e.g., cross sentence arguments, non IPS Arg1)
        """
        if len(rel.arg2_sid) > 1:
            return False
        if len(rel.arg1_sid) > 1:
            return False
        if len(rel.arg1_sid) == 0 or len(rel.arg2_sid) == 0:
            return True

        return True

        # arg1_sid = list(rel.arg1_sid)[0]
        # arg2_sid = list(rel.arg2_sid)[0]

        # if arg1_sid + 1 == arg2_sid or arg1_sid == arg2_sid:
        #     return True
        # else:
        #     return False

    def prepare_data(self, parse_path, rel_path, which, to_file):
        count = 0
        processed = []
        rel_dict = Corpus.read_relations(rel_path)
        for art in Corpus.read_parses(parse_path, rel_dict):
            for rel in art.relations:
                if rel.rel_type != 'Explicit':
                    continue
                rel.article = art
                rel.get_conn_leaves()
                rel.get_arg_leaves()

                # add a filter function (2015/9/29)
                if which == 'train' and not self.need_extract(rel):
                    continue
                count += 1

                processed.append(self.print_features(rel, which, to_file))

        print >> logs, "processed %d instances" % count
        return processed

    def train(self):
        to_file = open(self.train_file, 'w')
        self.prepare_data(TRAIN_PARSE_PATH, TRAIN_REL_PATH, 'train', to_file)
        to_file.close()
        Corpus.train_with_opennlp(self.train_file, self.model_file)
        # Corpus.train_with_svm(self.train_file, self.train_vec_file, self.feat_map_file, self.model_file)

    def test(self):
        to_file = open(self.test_file, 'w')
        self.prepare_data(DEV_PARSE_PATH, DEV_REL_PATH, 'test', to_file)
        to_file.close()
        Corpus.test_with_opennlp(self.test_file, self.model_file, self.predicted_file)
        # Corpus.test_with_svm(self.test_file, self.feat_map_file, self.test_vec_file, self.model_file, self.predicted_file)


if __name__ == '__main__':
    handler = Argument()
    handler.train()
    # handler.test()
