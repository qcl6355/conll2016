#! /usr/bin/python
# -*- coding: utf-8 -*-
import os
import random
import sys
import argparse
import json

from collections import defaultdict

from corpus import Corpus
from common import *
from relation import Relation
from feature import Feature

logs = sys.stderr

FILE_PATH = os.path.dirname(os.path.abspath(__file__))


class NonExplicit:
    def __init__(self):
        self.train_file = FILE_PATH + '/../data/conll.nonexp.train'
        self.test_file = FILE_PATH + '/../data/conll.nonexp.test'
        self.model_file = FILE_PATH + '/../data/conll.nonexp.model'
        self.predicted_file = FILE_PATH + '/../data/conll.nonexp.test.predicted'

        self.feat_handle = Feature()

    def print_features(self, relation, labels, to_file):
        feat_vec = []
        feat_vec += self.feat_handle.extract_arg2_first3(relation)
        feat_vec += self.feat_handle.extract_dependency_rules(relation)
        feat_vec += self.feat_handle.extract_production_rules(relation)
        # feat_vec += self.feat_handle.extract_polarity(relation)
        feat_vec += self.feat_handle.extract_word_pair(relation)
        feat_vec += self.feat_handle.extract_brown_cluster(relation)
        to_line = ' '.join(feat_vec)
        for label in labels:
            to_file.write('%s %s\n' % (to_line, label))

    def prepare_data(self, parse_path, rel_path, raw_home, which, to_file):
        rel_dict = Corpus.read_relations(rel_path)
        dist = defaultdict(int)
        for art in Corpus.read_parses(parse_path, rel_dict):
            for rel in art.relations:
                if rel.rel_type == 'Explicit':
                    continue
                rel.article = art
                rel.get_arg_leaves()
                labels = {s.replace(' ','_') for s in rel.sense}
                labels = {s for s in labels if s in NONEXP_SENSES}
                for l in labels:
                    dist[l] += 1
                if which == 'test':
                    labels = ['|'.join(labels)]

                self.print_features(rel, labels, to_file)

            if which=='train':
                art.read_raw_text(raw_home+'/'+art.id)
                self.generate_nonexp_relations(art)
                for rel in art.nonexp_relations:
                    labels = ['NoRel']
                    self.print_features(rel, labels, to_file)

        print >> logs, dist

    def generate_nonexp_relations(self, article):
        for para in article.paragraphs:
            for s1, s2 in zip(para.sentences[:-1], para.sentences[1:]):
                if not article.has_annotated_relation(s1.id):
                    # TODO: Add detail implementation
                    rel = Relation()
                    rel.article = article
                    rel.doc_id = article.id
                    rel.arg1s['parsed'] = [s1.tree.root] if not s1.tree.is_null() else []
                    rel.arg1_leaves = self.remove_leading_tailing_punc(s1.leaves)
                    rel.arg1_addr = [n.leaf_id for n in rel.arg1_leaves]
                    rel.arg1_sid = rel.arg1_leaves[-1].goto_tree().sent_id if len(rel.arg1_leaves) > 0 else -1
                    rel.arg1_text = ' '.join(n.value for n in rel.arg1_leaves)

                    rel.arg2s['parsed'] = [s2.tree.root] if not s2.tree.is_null() else []
                    rel.arg2_leaves = self.remove_leading_tailing_punc(s2.leaves)
                    rel.arg2_addr = [n.leaf_id for n in rel.arg2_leaves]
                    rel.arg2_sid = rel.arg2_leaves[0].goto_tree().sent_id if len(rel.arg2_leaves) > 0 else -1
                    rel.arg2_text = ' '.join(n.value for n in rel.arg2_leaves)

                    article.nonexp_relations.append(rel)


    def remove_leading_tailing_punc(self, leaves):
        if len(leaves) > 0:
            start = 0
            end = len(leaves)
            if is_punc(leaves[0].parent_node.value):
                start = 1
            if is_punc(leaves[-1].parent_node.value):
                end -= 1
            return leaves[start:end]
        else:
            return leaves

    def predict(self, test_file, predicted_file):
        Corpus.test_with_opennlp(test_file, self.model_file, predicted_file)

    def test(self):
        to_file = open(self.test_file, 'w')
        self.prepare_data(DEV_PARSE_PATH, DEV_REL_PATH, DEV_RAW_PATH, 'test', to_file)
        to_file.close()
        Corpus.test_with_opennlp(self.test_file, self.model_file, self.predicted_file)

    def train(self):
        to_file = open(self.train_file, 'w')
        # self.prepare_data(DEV_PARSE_PATH, DEV_REL_PATH, DEV_RAW_PATH, 'train', to_file)
        self.prepare_data(TRAIN_PARSE_PATH, TRAIN_REL_PATH, TRAIN_RAW_PATH, 'train', to_file)
        to_file.close()
        Corpus.train_with_opennlp(self.train_file, self.model_file)

    def print_performance(self):
        gold = [it.strip().split()[-1].split('|') for it in open(self.test_file)]
        pred = [it.strip().split()[-1] for it in open(self.predicted_file)]
        evaluate(gold, pred)

    def output_json_format(self, parse_path, rel_path):
        preds = [it.strip().split()[-1] for it in open(self.predicted_file)]
        rel_dict = Corpus.read_relations(rel_path)
        idx = 0
        for art in Corpus.read_parses(parse_path, rel_dict):
            for rel in art.relations:
                if rel.rel_type == 'Explicit':
                    continue
                pred_sense = preds[idx]
                json_dict = {}
                json_dict['DocID'] = rel.doc_id
                if pred_sense == 'EntRel':
                    r_type = 'EntRel'
                elif pred_sense == 'NoRel':
                    r_type = 'NoRel'
                else:
                    r_type = 'Implicit'

                json_dict['Type'] = r_type
                json_dict['Sense'] = [pred_sense.replace('_', ' ')]
                json_dict['Connective'] = {}
                json_dict['Connective']['TokenList'] = []
                json_dict['Arg1'] = {}
                json_dict['Arg1']['TokenList'] = []
                json_dict['Arg2'] = {}
                json_dict['Arg2']['TokenList'] = []
                print json.dumps(json_dict)
                idx += 1


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser("Implicit Discourse Parsing")
    arg_parser.add_argument('-t', '--relation_type', help='choose candidate relations to train model. 0 -- None;'
                                                          '1 -- only implicit relations; 2 -- non explicit relations; '
                                                          '3 -- inter relations (containing part explicit relations)',
                            type=int, choices=[0, 1, 2, 3], default=3)
    arg_parser.add_argument('-l', '--Lin', help='Training Lin\'NonExp Model', action='store_true')
    args = arg_parser.parse_args()
    param = vars(args)
    print >> sys.stderr, 'Configs of Implicit Parser:', json.dumps(param, indent=2)
    handler = NonExplicit()
    handler.train()
    # handler.test()
    # handler.print_performance()
    # handler.output_json_format(DEV_PARSE_PATH, DEV_REL_PATH)
