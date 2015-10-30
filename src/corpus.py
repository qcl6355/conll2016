# -*- coding: utf-8 -*-
from __future__ import division
__author__ = "Sheng Li"

import os
import sys
import math
import argparse
import json
from collections import defaultdict
logs = sys.stderr

from common import *
from article import Article
from feature import Feature
from relation import Relation
from sentence import Sentence


FILE_PATH = os.path.dirname(__file__)
# feat_handle = Feature()

brown_cluster = None

class Corpus(object):
    __slots__ = ('version',)

    def __init__(self):
        self.version = "Penn Discourse TreeBank V2.0"

    @staticmethod
    def get_other_leaf(curr, offset, article):
        tree = curr.goto_tree()
        sen = article.sentences[tree.sent_id]
        leaves = sen.leaves
        curr_index = sen.leaves.index(curr)
        if curr_index != -1:
            expect_index = offset + curr_index
            if expect_index >= 0 and expect_index < len(leaves):
                return leaves[expect_index]

    @staticmethod
    def load_brown_cluster(brown_cluster_path):
        global brown_cluster
        brown_cluster = defaultdict()
        for line in open(brown_cluster_path):
            cluster, word, _ = line.strip().split('\t')
            brown_cluster[word] = cluster

    @staticmethod
    def read_relations(rel_path):
        rel_dict = defaultdict(list)
        for x in open(rel_path):
            rel = Relation()
            rel.init_with_annotation(json.loads(x))
            rel_dict[rel.doc_id].append(rel)
        return rel_dict

    @staticmethod
    def read_parses(parse_path, relations_dict=None):
        parses = [json.loads(x) for x in open(parse_path)]
        for doc_id in parses[0]:
            print >> logs, "Doc ID:%s" % doc_id
            doc = parses[0][doc_id]
            sentences = []
            for sid, sen in enumerate(doc['sentences']):
                parse_tree = sen['parsetree']
                dep_tree = sen['dependencies']
                words = sen['words']
                sentences.append(Sentence(sid, parse_tree, dep_tree, words))
            if relations_dict is not None:
                relations = relations_dict[doc_id]
            else:
                relations = []
            params = {'sens': sentences, 'rels':relations}
            yield Article(doc_id, params)

    @staticmethod
    def is_non_exp_relation(rel, which):
        return rel.rel_type != 'Explicit' and rel.rel_type != 'NoRel' if which == 'train' else rel.rel_type != 'Explicit'

    @staticmethod
    def is_implicit_relation(rel, which):
        return rel.rel_type == 'Implicit'

    @staticmethod
    def is_inter_relations(rel, which):
        if rel.rel_type != 'Explicit':
            return True if which != 'train' else rel.rel_type != 'NoRel'
        elif rel.arg1_sid == rel.arg2_sid:
            return True
        else:
            return False

    @staticmethod
    def get_data(sections, which, filter_function=None):
        unary = False

        instances = []
        # generate data
        inst_id = 0
        for sec_id in sections:
            print >> sys.stderr, sec_id
            for art in Corpus.read_section(sec_id):
                for rel in art.relations:
                    inst_id += 1

                    if filter_function is not None and not filter_function(rel, which):
                        # select candidate relations, when filter function is `None', it means
                        # all relations are OK.
                        continue
                    else:
                        if which == 'train' and rel[1] == 'NoRel':
                            # in training mode, we do not need NoRel relation
                            continue

                    # get proper relation labels
                    if rel[1] == 'NoRel':
                        labels = ['NoRel']
                    elif rel[1] == 'EntRel':
                        labels = ['EntRel']
                    else:
                        if which == 'train':
                            labels = rel.level_1_types()[0:1]
                        elif which == 'test':
                            labels = rel.level_1_types()[0:1]
                        else:
                            labels = ['xxxxx']

                    feat_vec = [feat_handle.extract_verb(rel), feat_handle.extract_polarity(rel),
                                feat_handle.extract_modality(rel), feat_handle.extract_first_last(rel),
                                feat_handle.extract_production_rules(rel, unary),
                                feat_handle.extract_word_pair(rel),
                                feat_handle.extract_argument_connective(rel, which)]

                    rel_tb = defaultdict(lambda: defaultdict(list))
                    for lid, l in enumerate(labels):
                        for idx, feat in enumerate(ALL_FEATS):
                            rel_tb[l][feat] = ("InstID:%s-%s" % (inst_id, lid), feat_vec[idx])
                    instances.append(rel_tb)

        return instances

    @staticmethod
    def get_rel_dist(rel_path):
        rel_dist = defaultdict(int)
        for rel in Corpus.read_relations(rel_path):
            for s in rel.sense:
                rel_dist[s] += 1

        for k in rel_dist:
            print k, rel_dist[k]

    @staticmethod
    def get_production_rule_dict(train_sec, threshold=5):
        rule_dist = defaultdict(int)
        for sec_id in train_sec:
            for art in Corpus.read_section(sec_id):
                for rel in art.relations:
                    if rel[1] == 'Implicit':  # or rel[1] == 'EntRel':
                        rel.get_production_rule(rule_dist, unary=False)

        filter_res = {k: v for k, v in rule_dist.items() if v >= threshold}
        for k in filter_res:
            print "%s %s" % (k, filter_res[k])

    @staticmethod
    def collect_feature_relation_stat(frequency, parse_path, rel_path, feature_type="rule"):
        global brown_cluster
        """ MI method to rank feature"""
        n1_ = defaultdict(int)
        n_1 = defaultdict(int)
        n11 = defaultdict(int)
        n = 0

        rel_dict = Corpus.read_relations(rel_path)
        for art in Corpus.read_parses(parse_path, rel_dict):
            for rel in art.relations:
                if rel.rel_type == 'Explicit':
                    continue

                rel.article = art
                rel.get_arg_leaves()

                types = set(rel.sense)
                # only consider conll possible senses
                types = {s for s in types if s in SENSES}

                if feature_type == "rule":
                    rule_dist = defaultdict(int)
                    rel.get_production_rule(rule_dist, unary=False)
                    collect_features = rule_dist
                elif feature_type == "dep":
                    rule_dist = defaultdict(int)
                    rel.get_dependency_rule(rule_dist)
                    collect_features = rule_dist
                elif feature_type == "word-pair":
                    token1 = [l.stem for l in rel.arg1_leaves]
                    token2 = [l.stem for l in rel.arg2_leaves]
                    pairs = defaultdict(int)
                    for w1 in token1:
                        for w2 in token2:
                            pairs[w1 + "_" + w2] += 1
                    collect_features = pairs
                elif feature_type == "brown":
                    token1 = [l.value for l in rel.arg1_leaves]
                    token2 = [l.value for l in rel.arg2_leaves]
                    pairs = defaultdict(int)
                    for w1 in token1:
                        for w2 in token2:
                            pairs['b:'+brown_cluster.get(w1,'nil') + "_b:" + brown_cluster.get(w2,'nil')] += 1
                    collect_features = pairs
                else:
                    collect_features = {}
                    print 'error: not correct feature type'

                for t in types:
                    n += 1
                    n_1[t] += 1

                    for r in collect_features:
                        n1_[r] += 1
                        n11[r + ' ' + t] += 1

        mi_rule = defaultdict(float)
        for r in n1_:
            if n1_[r] < frequency:
                continue
            nn1_ = n1_[r]
            for t in n_1:
                nn_1 = n_1[t]
                nn11 = n11[r + ' ' + t]

                nn01 = nn_1 - nn11
                nn0_ = n - nn1_
                nn_0 = n - nn_1
                nn10 = nn1_ - nn11
                nn00 = nn0_ - nn01

                a = (nn11 + 1) / (n + 4) * math.log((n + 4) * (nn11 + 1) / (nn1_ + 2) / (nn_1 + 2), base=2)
                b = (nn01 + 1) / (n + 4) * math.log((n + 4) * (nn01 + 1) / (nn0_ + 2) / (nn_1 + 2), base=2)
                c = (nn10 + 1) / (n + 4) * math.log((n + 4) * (nn10 + 1) / (nn1_ + 2) / (nn_0 + 2), base=2)
                d = (nn00 + 1) / (n + 4) * math.log((n + 4) * (nn00 + 1) / (nn0_ + 2) / (nn_0 + 2), base=2)

                key = "%s %s %s %s %s %s %s" % (r, t, n1_[r], nn11, nn10, nn01, nn00)
                mi_rule[key] = a + b + c + d

        res = sorted(mi_rule.items(), key=lambda x: x[1], reverse=True)
        for k in res:
            print "%s %s" % k

    @staticmethod
    def dump_exp_index():
        for sec in test_data:
            for article in Corpus.read_section(sec):
                name = '%s/%s/%s.addr' % (GOLD_EXP_CONN_ADDRESS, sec, article.id)
                to_file = open(name, 'w')
                for rel in article.relations:
                    to_line = '%s|%s|' % (rel[1], article.id)
                    if rel[1] == 'Explicit':
                        conn_addr = rel.resolve_token_address(rel.conn_leaves)
                        to_line += conn_addr
                    arg1_addr = rel.resolve_token_address(rel.arg1_leaves)
                    arg2_addr = rel.resolve_token_address(rel.arg2_leaves)
                    to_line += '|%s|%s' % (arg1_addr, arg2_addr)
                    to_file.write(to_line+'\n')
                to_file.close()

    @staticmethod
    def train_with_opennlp(train_file, model_file):
        cmd = "java -cp " + CLASSPATH + " CreateModel -real " + train_file + " " + model_file
        os.system(cmd)

    @staticmethod
    def test_with_opennlp(test_file, model_file, predict_file):
        cmd = "java -cp " + CLASSPATH + " Predict -real " + test_file + " " + model_file + " > " + \
              predict_file
        os.system(cmd)

    @staticmethod
    def mallet_train(train_file, model_file, algorithm="MaxEnt"):
        """
        mallet training interface
        :param train_file:
        :param model_file:
        :param algorithm: MaxEnt, NaiveBayes, MaxEntL1 etc.
        :return:
        """
        cmd = 'set MALLET_HOME=' + MALLET_HOME
        cmd1 = cmd + '& ' + MALLET_HOME + '/bin/mallet import-file --input ' + \
               train_file + ' --preserve-case --token-regex "\S+" --output ' + train_file + '.mallet'
        os.system(cmd1)

        cmd2 = cmd + '& ' + MALLET_HOME + '/bin/mallet train-classifier --input ' + \
               train_file + '.mallet --output-classifier ' + model_file + \
               ' --trainer ' + algorithm
        os.system(cmd2)

    @staticmethod
    def mallet_predict(test_file, model_file, res_file):
        """
        mallet testing interface
        :param test_file:
        :param model_file:
        :param res_file:
        :return:
        """
        cmd = 'set MALLET_HOME=' + MALLET_HOME
        cmd += '& ' + MALLET_HOME + '/bin/mallet classify-file --input ' + \
               test_file + ' --output ' + res_file + ' --classifier ' + \
               model_file
        os.system(cmd)


def test(rel_path, parse_path):
    rel_dict = Corpus.read_relations(rel_path)
    for art in Corpus.read_parses(parse_path, rel_dict):
        art.set_article_level_word_id()
        for rel in art.relations:
            rel.article = art
            rel.get_arg_leaves()
            for addr, arg in zip(rel.arg1_addr, rel.arg1_leaves):
                if int(addr[2]) != arg.leaf_id:
                    print addr[2], arg.leaf_id
                    print rel.arg1_text
                    exit(-1)

            # test arg1
            # print rel.arg1_text
            # arg1_leaves = []
            # for subt in rel.arg1s['parsed']:
            #       arg1_leaves += subt.get_leaves()
            # print ' '.join(l.value for l in arg1_leaves)

            # test arg2
            # print rel.arg2_text
            # arg2_leaves = []
            # for subt in rel.arg2s['parsed']:
            #       arg2_leaves += subt.get_leaves()
            # print ' '.join(l.value for l in arg2_leaves)



if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser("Corpus Helper Class")
    arg_parser.add_argument('-t', '--feat', help='generate feature vocab with MI method', type=int, choices=[1, 2, 3])
    args = arg_parser.parse_args()
    # print 'train data distribution'
    # Corpus.get_rel_dist(TRAIN_REL_PATH)

    # print 'test data distribution'
    # Corpus.get_rel_dist(DEV_REL_PATH)

    # Corpus.get_rel_dist(dev_data)

    # get_production_rule_dict(train_data)

    # feature_type = "rule"
    # feature_type = "dep"
    # feature_type = "word-pair"
    feature_type = 'brown'
    if feature_type == "brown":
        brown_cluster_path = FILE_PATH + '/../lib/brown-c100.txt'
        Corpus.load_brown_cluster(brown_cluster_path)
    Corpus.collect_feature_relation_stat(5, TRAIN_PARSE_PATH, TRAIN_REL_PATH, feature_type)

    # Corpus.dump_exp_index()
    # test(TRAIN_REL_PATH, TRAIN_PARSE_PATH)
    # test(DEV_REL_PATH, DEV_PARSE_PATH)
