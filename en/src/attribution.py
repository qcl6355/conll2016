#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Sheng Li'

import sys
import os

logs = sys.stderr
FILE_PATH = os.path.dirname(os.path.abspath(__file__))

from common import *
from corpus import Corpus
from tree import Tree

from collections import defaultdict


class Attribution(object):
    def __init__(self):
        self.train_file = FILE_PATH + '/../data/conll.attr.train'
        self.test_file = FILE_PATH + '/../data/conll.attr.test'
        self.model_file = FILE_PATH + '/../data/conll.attr.model'
        self.predicted_file = FILE_PATH + '/../data/conll.attr.test.predicted'

        self.attr_verbs = aset("say accord note add believe think argue contend recall tell")

    def prepare_data(self, parse_path, rel_path, which, to_file):
        rel_dict = Corpus.read_relations(rel_path)
        for art in Corpus.read_parses(parse_path, rel_dict):
            for rel in art.relations:
                if rel.rel_type == 'EntRel':
                    continue
                rel.article = art
                rel.get_conn_leaves()
                rel.get_arg_leaves()

                if len(rel.arg1_sid) == 1 and len(rel.arg2_sid) == 1:
                    arg1_sid = list(rel.arg1_sid)[0]
                    arg2_sid = list(rel.arg2_sid)[0]
                    s1_clauses = art.sentences[arg1_sid].clauses
                    s2_clauses = art.sentences[arg2_sid].clauses

                    # for argument 1
                    for idx, clause in enumerate(s1_clauses):
                        prev_clause = s1_clauses[idx-1] if idx > 0 else None
                        next_clause = s1_clauses[idx+1] if idx < len(s1_clauses) -1 else None
                        self.print_features(clause, prev_clause, next_clause, rel.arg1_leaves, which, to_file)

                    # for argument 2
                    for idx, clause in enumerate(s2_clauses):
                        prev_clause = s2_clauses[idx-1] if idx > 0 else None
                        next_clause = s2_clauses[idx+1] if idx < len(s2_clauses) -1 else None
                        self.print_features(clause, prev_clause, next_clause, rel.arg2_leaves, which, to_file)

    # return 0-all, 1-partial, 2-none
    def is_gold_clause(self, curr_clause, argument):
        for leaf in curr_clause:
            if leaf in argument:
                return '0' # current clause belongs to part of argument
        return '1'  # current clause is an attribution

        # has_one_exist = False
        # has_one_nonexist = False
        # for leaf in curr_clause:
        #     if leaf in argument:
        #         has_one_exist = True
        #     else:
        #         has_one_nonexist = True
        # if has_one_exist and has_one_nonexist:
        #     return 'all_in'
        # elif has_one_exist and not has_one_nonexist:
        #     return 'all_in'
        # elif not has_one_exist and has_one_nonexist:
        #     return 'none_in'
        # else: # this is case is always impossible (think about it)
        #     print >> logs, 'impossible case'
        #     return '-1'

    def print_features(self, curr_clause, prev_clause, next_clause, argument, which, to_file):
        to_file_line = ''

        # current clause verbs
        for l in curr_clause:
            if l.parent_node.value in verb_tags:
                to_file_line += 'dc_verb:%s ' % l.lowercased
                to_file_line += 'stem_verb:%s ' % l.stem
        # first term
        to_file_line += 'curr_1st:%s ' % curr_clause[0].lowercased

        # last term
        to_file_line += 'curr_last:%s ' % curr_clause[-1].lowercased

        # prev clause last term
        if prev_clause is not None:
            to_file_line += 'prev_last:%s ' % prev_clause[-1].lowercased
            # combine prev & curr
            to_file_line += 'prev_last_curr_1st:%s_%s ' % (prev_clause[-1].lowercased, curr_clause[0].lowercased)

        # next clause first term
        if next_clause is not None:
            to_file_line += 'next_1st:%s ' % next_clause[0].lowercased
            # combine next & curr
            to_file_line += 'curr_last_next_1st:%s_%s ' % (curr_clause[-1].lowercased, next_clause[0].lowercased)

        # current clause length
        to_file_line += 'curr_length:%d ' % len(curr_clause)

        # current clause position
        if prev_clause is None and next_clause is None:
            to_file_line += 'whole_pos '
        elif prev_clause is None:
            to_file_line += 'start_pos '
        elif next_clause is None:
            to_file_line += 'end_pos '
        else:
            to_file_line += 'middle_pos '

        # production rules
        lca = Tree.find_least_common_ancestor(curr_clause, with_leaves=True)
        rules = defaultdict(int)
        if lca is not None:
            lca.get_production_rules(rules, -1, False)

        for r in rules:
            to_file_line += '%s ' % r

        # curr[0] -> prev[-1] path
        if prev_clause is not None:
            curr_1st_to_prev_last = Tree.find_constituent_path(curr_clause[0].parent_node, prev_clause[-1].parent_node)
            to_file_line += 'curr_1st_to_prev_last_path:%s ' % curr_1st_to_prev_last[0]

        # curr[-1] -> next[0] path
        if next_clause is not None:
            curr_last_to_next_1st = Tree.find_constituent_path(curr_clause[-1].parent_node, next_clause[0].parent_node)
            to_file_line += 'curr_last_to_next_1st_path:%s ' % curr_last_to_next_1st[0]

        if which == 'train':
            label = self.is_gold_clause(curr_clause, argument)
        else:
            label = 'None'
        to_file.write('%s %s\n' % (to_file_line, label))

    def train(self):
        to_file = open(self.train_file, 'w')
        self.prepare_data(TRAIN_PARSE_PATH, TRAIN_REL_PATH, 'train', to_file)
        to_file.close()
        Corpus.train_with_opennlp(self.train_file, self.model_file)

    def test(self):
        to_file = open(self.test_file, 'w')
        self.prepare_data(DEV_PARSE_PATH, DEV_REL_PATH, 'test', to_file)
        to_file.close()
        Corpus.test_with_opennlp(self.test_file, self.model_file, self.predicted_file)


if __name__ == '__main__':
    handler = Attribution()
    handler.train()
