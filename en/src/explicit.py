# -*- coding: utf-8 -*-

__author__ = "Sheng Li"
import os
import sys

from common import *
from corpus import Corpus

logs = sys.stderr

FILE_PATH = os.path.dirname(os.path.abspath(__file__))


class Explicit(object):
    """
    Explicit Sense Classifier
    """
    def __init__(self):
        self.train_file = FILE_PATH + '/../data/conll.exp.train'
        self.test_file = FILE_PATH + '/../data/conll.exp.test'
        self.model_file = FILE_PATH + '/../data/conll.exp.model'
        self.predicted_file = FILE_PATH + '/../data/conll.exp.test.predicted'

    def print_features(self, relation, labels, which, to_file):
        to_line = ''
        conn_leaves = relation.conn_leaves
        if len(conn_leaves) == 0:
            return

        conn_str = '_'.join(n.value for n in conn_leaves)
        to_line += 'conn:%s ' % conn_str

        conn_lc = conn_str.lower()
        to_line += 'conn_lc:%s ' % conn_lc

        conn_pos = '_'.join(n.parent_node.value for n in conn_leaves)
        to_line += 'conn_pos:%s ' % conn_pos

        prev = Corpus.get_other_leaf(conn_leaves[0], -1, relation.article)
        if prev is not None:
            to_line += 'prev_full:%s_%s ' % (prev.value, conn_str)

        for label in labels:
            to_file.write('%s %s\n' % (to_line, label))

    def prepare_data(self, parse_path, rel_path, which, to_file):
        rel_dict = Corpus.read_relations(rel_path)
        for art in Corpus.read_parses(parse_path, rel_dict):
            for rel in art.relations:
                if rel.rel_type != 'Explicit':
                    continue
                rel.article = art
                rel.get_conn_leaves()
                labels = {s.replace(' ','_') for s in rel.sense}
                # conll only evaluates 15 possible senses
                labels = {s for s in labels if s in SENSES}
                if which == 'test':
                    labels = ['|'.join(labels)]

                self.print_features(rel, labels, which, to_file)

    def test(self):
        to_file = open(self.test_file, 'w')
        self.prepare_data(DEV_PARSE_PATH, DEV_REL_PATH, 'test', to_file)
        to_file.close()
        Corpus.test_with_opennlp(self.test_file, self.model_file, self.predicted_file)

    def train(self):
        to_file = open(self.train_file, 'w')
        self.prepare_data(TRAIN_PARSE_PATH, TRAIN_REL_PATH, 'train', to_file)
        to_file.close()
        Corpus.train_with_opennlp(self.train_file, self.model_file)

    def print_performance(self):
        gold = [it.strip().split()[-1].split('|') for it in open(self.test_file)]
        pred = [it.strip().split()[-1] for it in open(self.predicted_file)]
        print gold
        evaluate(gold, pred)

if __name__ == '__main__':
    handler = Explicit()
    handler.train()
    # handler.test()
    # handler.print_performance()

