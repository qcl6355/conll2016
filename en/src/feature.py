#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = "Sheng Li"

import os
from collections import defaultdict

from deptree import DepTree
from common import is_verb, cross_product

FILE_PATH = os.path.dirname(__file__)

levin_lcs = FILE_PATH + '/../../lib/verbs-English.lcs'
mpqa_sub_path = FILE_PATH + '/../../lib/subjclueslen1-HLTEMNLP05.tff'
inquirer_lex = FILE_PATH + '/../../lib/inqdict.txt'
product_rule = FILE_PATH + '/../../lib/mi-product-rule.txt'
dep_rule = FILE_PATH + '/../../lib/mi-dep-rule.txt'
word_pair_path = FILE_PATH + '/../../lib/mi-word-pair.txt'
brown_cluster_path = FILE_PATH + '/../../lib/brown-c3200.txt'
brown_rule_path = FILE_PATH + '/../../lib/mi-brown-c100.txt'


class Feature(object):

    __slots__ = 'word_dict', 'rule_dict', 'dep_dict', 'levin_dict', 'mpqa_dict', 'neg_inq_dict', 'brown_cluster', 'brown_dict'

    """
    provide various methods to extact features
    """

    def __init__(self):
        self.load_init_lexicon()

    def load_init_lexicon(self):
        # load levin lexicon
        # self._load_levin_lexicon()

        # load mpqa lexicon
        self._load_mpqa_lexicon()

        # load inquier lexicon
        self._load_inquirer_lexicon()

        # load production rule
        self._load_production_rule()

        # load dep rule
        self._load_dependency_rule()

        # load word pair dict
        self._load_word_pair()

        # load brown cluster
        self._load_brown_cluster()

        # load brown cluster rule
        # self._load_brown_rule()

    def _load_brown_cluster(self):
        self.brown_cluster = defaultdict()
        for line in open(brown_cluster_path):
            cluster, word, _ = line.strip().split('\t')
            self.brown_cluster[word] = cluster

    def _load_brown_rule(self, num=500):
        self.brown_dict = defaultdict(float)
        count = 0
        for line in open(brown_rule_path):
            if count == num:
                break
            items = line.strip().split()
            if items[0] not in self.brown_dict:
                self.brown_dict[items[0]] = float(items[-1])
                count += 1

    def _load_word_pair(self, num=500):
        self.word_dict = defaultdict(float)
        count = 0
        for line in open(word_pair_path):
            if count == num:
                break
            items = line.strip().split()
            if items[0] not in self.word_dict:
                self.word_dict[items[0]] = float(items[-1])
                count += 1

    def _load_production_rule(self, num=100):
        self.rule_dict = defaultdict(float)
        count = 0
        for line in open(product_rule):
            # if count == num:
            #     break
            items = line.strip().split()
            if items[0] not in self.rule_dict:
                self.rule_dict[items[0]] = float(items[-1])
                count += 1

    def _load_dependency_rule(self, num=100):
        self.dep_dict = defaultdict(float)
        count = 0
        for line in open(dep_rule):
            # if count == num:
            #     break
            items = line.strip().split()
            if items[0] not in self.dep_dict:
                self.dep_dict[items[0]] = float(items[-1])
                count += 1

    def _load_levin_lexicon(self):
        """ Example:
        ;; Grid: 31.1.a#1#_ag_exp,instr(with)#abash#abash#abash#abash+ingly#(1.5,01020392)(1.6,01223592)###AD
        """
        self.levin_dict = defaultdict(set)
        for line in open(levin_lcs):
            line = line.strip()
            if line.startswith(';; Grid:'):
                item = line.split('#')
                v_c = item[0].replace(';; Grid: ', '')
                w = item[3]
                self.levin_dict[w].add(v_c)

    def _load_mpqa_lexicon(self):
        """ Example:
        type=weaksubj len=1 word1=abandoned pos1=adj stemmed1=n priorpolarity=negative
        """
        self.mpqa_dict = {}
        for line in open(mpqa_sub_path):
            item = line.strip().split()
            w = item[2].replace('word1=', '')
            p = item[-1].replace('priorpolarity=', '')
            self.mpqa_dict[w] = p

    def _load_inquirer_lexicon(self):
        """Example:
        ABANDON H4Lvd Neg Ngtv Weak Fail IAV AFFLOSS AFFTOT SUPV  |
        """
        self.neg_inq_dict = set()
        for idx, line in enumerate(open(inquirer_lex)):
            if idx == 0:
                continue
            item = line.strip().split()
            for it in item:
                if it == 'Neg':
                    self.neg_inq_dict.add(item[0].lower().split('#')[0])
                    break

    @staticmethod
    def extract_first_last(rel):
        """
        feature: First-Last, First3
        """
        arg1_leaves = rel.arg1_leaves
        arg2_leaves = rel.arg2_leaves
        feat_vec = []
        if len(arg1_leaves) > 0:
            feat_vec.append('Arg1First_%s:1' % arg1_leaves[0].value)
            feat_vec.append('Arg1Last_%s:1' % arg1_leaves[-1].value)
        if len(arg2_leaves) > 0:
            feat_vec.append('Arg2First_%s:1' % arg2_leaves[0].value)
            feat_vec.append('Arg2Last_%s:1' % arg2_leaves[-1].value)
        if len(arg1_leaves) > 0 and len(arg2_leaves) > 0:
            feat_vec.append('Arg12FF_%s_%s:1' % (arg1_leaves[0].value, arg2_leaves[0].value))
            feat_vec.append('Arg12LL_%s_%s:1' % (arg1_leaves[-1].value, arg2_leaves[-1].value))

        num = min(3, len(arg1_leaves))
        feat_vec.append('Arg1First3_%s:1' % ('_'.join(l.value for l in arg1_leaves[:num])))
        num = min(3, len(arg2_leaves))
        feat_vec.append('Arg2First3_%s:1' % ('_'.join(l.value for l in arg2_leaves[:num])))
        return feat_vec

    def extract_verb(self, rel):
        """
        extract verb features
        """
        arg1_leaves = rel.arg1_leaves
        arg2_leaves = rel.arg2_leaves
        arg1 = rel.arg1s['parsed']
        arg2 = rel.arg2s['parsed']

        # verb pair of highest levin class
        num_same_class = 0
        h1 = self._get_subtree_vc(arg1_leaves)
        h2 = self._get_subtree_vc(arg2_leaves)
        for vc1 in h1:
            for vc2 in h2:
                if not vc1.isdisjoint(vc2):
                    num_same_class += 1

        feat_vec = ['num_pair:%s' % num_same_class]

        # average length of verb phrases
        len_v1 = self._get_ave_vp(arg1)
        len_v2 = self._get_ave_vp(arg2)
        feat_vec.append('arg1_ave_len:%s' % len_v1)
        feat_vec.append('arg2_ave_len:%s' % len_v2)

        # main verb (simply use first verb as main verb)
        m_v1 = self._get_main_verb(arg1_leaves)
        m_v2 = self._get_main_verb(arg2_leaves)
        if m_v1 is not None:
            feat_vec.append('arg1_main_verb_pos_%s:1' % m_v1.parent_node.value)
        if m_v2 is not None:
            feat_vec.append('arg2_main_verb_pos_%s:1' % m_v2.parent_node.value)

        return feat_vec

    @staticmethod
    def _get_main_verb(leaves):
        """
        simply take the first verb as main verb
        """
        for leaf in leaves:
            if is_verb(leaf.parent_node.value):
                return leaf

    @staticmethod
    def _get_ave_vp(args):
        """average length of verb phrases
        """
        verb_phrases = []
        for node in args:
            node.get_len_of_verb_phrases(verb_phrases)

        if len(verb_phrases) == 0:
            return 0
        else:
            return sum(verb_phrases) / len(verb_phrases)

    def _get_subtree_vc(self, leaves):
        verb_class = []
        for leaf in leaves:
            if is_verb(leaf.parent_node.value) and \
                            leaf.lemmatized in self.levin_dict:
                verb_class.append(self.levin_dict[leaf.lemmatized])

        return verb_class

    def extract_polarity(self, rel):
        """
        extract polarity features
        """
        arg1_leaves = rel.arg1_leaves
        arg2_leaves = rel.arg2_leaves

        feat_vec = []
        # process Arg1
        pol1 = self._get_polarity(arg1_leaves)
        feat_vec += ['Arg1P_%s:%s' % (p, pol1[p])
                     for p in pol1 if pol1[p] != 0]

        # process Arg2
        pol2 = self._get_polarity(arg2_leaves)
        feat_vec += ['Arg2P_%s:%s' % (p, pol2[p])
                     for p in pol2 if pol2[p] != 0]

        # cross product of polarity
        cp = cross_product(pol1, pol2)
        if cp is not None:
            feat_vec += ['pcp_%s:%s' % (p, cp[p])
                         for p in cp if cp[p] != 0]

        return feat_vec

    def _get_polarity(self, leaves):
        polarity = defaultdict(int)
        # record positive, negative, neutral word count
        for leaf in leaves:
            # key = leaf.value.lower()
            key = leaf.stem
            if key in self.mpqa_dict:
                polarity[self.mpqa_dict[key]] += 1

        # record negated positive count
        for idx, leaf in enumerate(leaves):
            # key = leaf.value.lower()
            key = leaf.stem
            if key in self.mpqa_dict and self.mpqa_dict[key] == 'positive':
                # specify 3 window before current word
                for offset in [1, 2, 3]:
                    if idx - offset >= 0:
                        before = leaves[idx - offset].stem.lower()
                        if before in self.neg_inq_dict:
                            polarity['negatedPositive'] += 1
                            polarity['positive'] -= 1
                            break
        return polarity

    def extract_modality(self, rel):
        """ extract modality feature
        """
        arg1_leaves = rel.arg1_leaves
        arg2_leaves = rel.arg2_leaves
        feat_vec = []

        m_v1 = self._get_modality(arg1_leaves)
        m_v2 = self._get_modality(arg2_leaves)
        # presence or absence of Modality word
        if len(m_v1) != 0:
            feat_vec.append('arg1HasMod:1')
        else:
            feat_vec.append('arg1HasMod:0')

        if len(m_v2) != 0:
            feat_vec.append('arg2HasMod:1')
        else:
            feat_vec.append('arg2HasMod:0')

        # specific modal words of each argument
        if len(m_v1) != 0:
            feat_vec += ['arg1MW_%s:%s' % (k, v) for k, v in m_v1.items()]

        if len(m_v2) != 0:
            feat_vec += ['arg2MW_%s:%s' % (k, v) for k, v in m_v2.items()]

        # cross products of modal words
        cp = cross_product(m_v1, m_v2)
        if cp is not None:
            feat_vec += ['mcp_%s:%s' % (k, v)
                         for k, v in cp.items() if v != 0]

        return feat_vec

    @staticmethod
    def _get_modality(leaves):
        modality_arg = defaultdict(int)
        for leaf in leaves:
            if leaf.parent_node.value == 'MD':
                modality_arg[leaf.lemmatized] = 1
        return modality_arg

    def extract_production_rules(self, relation, unary=False):
        """extract constituent production rules"""
        res1 = defaultdict(int)
        res2 = defaultdict(int)

        for n in relation.arg1s['parsed']:
            if unary:
                n.get_unary_production_rules(res1)
            else:
                n.get_production_rules(res1, -1)

        for n in relation.arg2s['parsed']:
            if unary:
                n.get_unary_production_rules(res2)
            else:
                n.get_production_rules(res2, -1)

        feat_vec = []
        for k in self.rule_dict:
            a1 = k in res1
            a2 = k in res2
            if a1: feat_vec.append(k + ":1")
            if a2: feat_vec.append(k + ":2")
            if a1 and a2: feat_vec.append(k + ":12")

        return feat_vec

    def extract_dependency_rules(self, relation):
        """
        extract dependency rules
        :param relation:
        :return:
        """
        res1 = defaultdict(int)
        res2 = defaultdict(int)
        DepTree.get_dependency_rules(res1, relation.arg1_leaves, False, True)
        DepTree.get_dependency_rules(res2, relation.arg2_leaves, False, True)

        feat_vec = []
        for k in self.dep_dict:
            a1 = k in res1
            a2 = k in res2
            if a1: feat_vec.append(k + ":1")
            if a2: feat_vec.append(k + ":2")
            if a1 and a2: feat_vec.append(k + ":12")

        return feat_vec

    def extract_arg2_first3(self, relation):
        """
        :param relations:
        :return:
        """
        feat_vec = []
        num = min(3, len(relation.arg2_leaves))
        feat_vec.append('Arg2First3_%s:1' % ('_'.join(l.value.lower() for l in relation.arg2_leaves[:num])))
        return feat_vec

    def extract_word_pair(self, rel):
        tmp = set()
        for w1 in rel.arg1_leaves:
            for w2 in rel.arg2_leaves:
                k = w1.stem + "_" + w2.stem
                if k in self.word_dict:
                    tmp.add(k)

        return ["%s:1" % k for k in tmp]

    def extract_brown_cluster(self, rel):
        tmp = set()
        for w1 in rel.arg1_leaves:
            for w2 in rel.arg2_leaves:
                k = 'b:'+self.brown_cluster.get(w1.value, 'nil') + '_b:' \
                        + self.brown_cluster.get(w2.value, 'nil')
                # if k in self.brown_dict:
                tmp.add(k)

        return ["%s:1" % k for k in tmp]


    def extract_argument_connective(self, rel, which):
        s1 = rel.article.sentences[rel.arg1_sid]
        s2 = rel.article.sentences[rel.arg2_sid]
        res = []

        s1_conns = s1.auto_connectives if which == 'parse' else s1.gold_connectives
        for conn in s1_conns:
            flag = True
            for leaf in conn:
                if leaf not in rel.arg1_leaves:
                    flag = False
                    break
            if flag:
                res.append('arg1_conn:%s' % '_'.join(n.value.lower() for n in conn))

        s2_conns = s2.auto_connectives if which == 'parse' else s2.gold_connectives
        for conn in s2_conns:
            flag = True
            for leaf in conn:
                if leaf not in rel.arg2_leaves:
                    flag = False
                    break
            if flag:
                res.append('arg2_conn:%s' % '_'.join(n.value.lower() for n in conn))

        if rel[1] == 'Explicit':
            res.append('arg2_conn:%s' % '_'.join(n.value.lower() for n in rel.conn_leaves))
        return res
