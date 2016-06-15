# -*- coding: utf-8 -*-
__author__ = 'Sheng Li'
import os
import sys
import json
from collections import defaultdict

from tree import Tree
from deptree import DepTree
from conn_head_mapper import ConnHeadMapper

logs = sys.stderr
header = ConnHeadMapper()


class Relation(object):
    """ represents a discourse relation """
    def __init__(self):
        self.doc_id = -1
        self.rel_type = ''
        self.sense = ['Expansion.Conjunction']
        self.conn_str = ''
        self.conn_addr = []
        self.conn_leaves = []
        self.arg1_addr = []
        self.arg1_text = ''
        self.arg2_addr = []
        self.arg2_text = ''
        self.article = None
        self.arg1_leaves = []
        self.arg2_leaves = []
        self.arg1s = {}
        self.arg2s = {}

    def init_with_annotation(self, json_str):
        self.doc_id = json_str['DocID']
        self.rel_id = json_str['ID']
        self.rel_type = json_str['Type']
        self.sense = json_str['Sense']
        self.conn_str = json_str['Connective']['RawText']
        if self.rel_type == 'Explicit':
            self.conn_addr = json_str['Connective']['TokenList']
        else:
            self.conn_addr = None
        self.conn_leaves = []
        self.arg1_addr = json_str['Arg1']['TokenList']
        self.arg1_text = json_str['Arg1']['RawText']
        self.arg2_addr = json_str['Arg2']['TokenList']
        self.arg2_text = json_str['Arg2']['RawText']

        self.article = None
        self.arg1_leaves = []
        self.arg2_leaves = []
        self.arg1s = {}
        self.arg2s = {}

    def __str__(self):
        return "doc:%s rel:%s" % (self.doc_id, self.rel_id)

    __repr__ = __str__

    def get_arg_leaves(self):
        self.arg1_sid, self.arg1_leaves, self.arg1s['parsed'] = \
                self._resolve_leaves(self.arg1_addr)

        self.arg2_sid, self.arg2_leaves, self.arg2s['parsed'] = \
                self._resolve_leaves(self.arg2_addr)

    def _resolve_leaves(self, addrs):
        args = defaultdict(list)
        leaves =[]
        sids = set()
        for addr in addrs:
            sent_id = int(addr[-2])
            leaf_id = int(addr[-1])
            sen = self.article.sentences[sent_id]
            if len(sen.leaves) == 0:
                print >> logs, sen.tree
                continue
            node = sen.leaves[leaf_id]
            sids.add(sent_id)
            leaves.append(node)
            args[sent_id].append(node)

        # resolve subtree in parse tree
        subtrees = []
        for sid in args:
            tree = self.article.sentences[sid].tree
            subt = tree.find_subtrees(args[sid])
            subtrees += subt

        return sids, leaves, subtrees

    def get_conn_leaves(self):
        if self.rel_type == 'Explicit':
            head_conn, indices = header.map_raw_connective(self.conn_str.strip())
            for index in indices:
                addr = self.conn_addr[index]
                sid = int(addr[-2])
                lid = int(addr[-1])
                sen = self.article.sentences[sid]
                if len(sen.leaves) == 0:
                    print >> logs, sen.tree
                    continue
                self.conn_leaves.append(sen.leaves[lid])
            if head_conn != ' '.join(n.value for n in self.conn_leaves).lower() and head_conn != 'afterward':
                print >> logs, head_conn, ' '.join(n.value for n in self.conn_leaves).lower(), self.conn_str

            self.article.disc_connectives.append(self.conn_leaves)

    def get_production_rule(self, rule_cnts, unary=True, with_leaf=True):
        for n in self.arg1s['parsed'] + self.arg2s['parsed']:
            if unary:
                n.get_unary_production_rules(rule_cnts, with_leaf)
            else:
                n.get_production_rules(rule_cnts, -1, with_leaf)

    def get_dependency_rule(self, rule_dict, with_leaf=False, with_label=True):
        DepTree.get_dependency_rules(rule_dict, self.arg1_leaves, with_leaf, with_label)
        DepTree.get_dependency_rules(rule_dict, self.arg2_leaves, with_leaf, with_label)

    def set_linker(self):
        for n in self.arg1s['parsed']:
            n.recursive_set_linker('arg1')

        for n in self.arg2s['parsed']:
            n.recursive_set_linker('arg2')

    def output_json_format(self):
        """
        output each relation corresponding to conll format
        """
        json_dict = {}
        json_dict['DocID'] = self.doc_id
        json_dict['Type'] = self.rel_type
        json_dict['Sense'] = [s.replace('_', ' ') for s in self.sense]
        json_dict['Connective'] = {}
        json_dict['Connective']['TokenList'] = self.conn_addr
        json_dict['Connective']['RawText'] = ' '.join(n.value for n in self.conn_leaves)
        json_dict['Arg1'] = {}
        json_dict['Arg1']['TokenList'] = self.arg1_addr
        json_dict['Arg1']['RawText'] = self.arg1_text
        json_dict['Arg2'] = {}
        json_dict['Arg2']['TokenList'] = self.arg2_addr
        json_dict['Arg2']['RawText'] = self.arg2_text
        return json.dumps(json_dict)

