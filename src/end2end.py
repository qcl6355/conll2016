#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Sheng Li'

import os
import sys
import argparse
import codecs

from corpus import Corpus
from relation import Relation
from connective import Connective
from argument import Argument
from explicit import Explicit
from nonexp import NonExplicit
from common import *

logs = sys.stderr

FILE_PATH = os.path.dirname(os.path.abspath(__file__))


class DiscourseParser(object):
    """
    A PDTB-styled Shallow Discourse Parser
    """
    def __init__(self):
        self.conn_res_name = FILE_PATH+'/../tmp/conll.conn.predicted'

    def process_parsed_conn(self, articles, which='test'):
        """
        generate explicit relation for each true discourse connective
        """
        connParser = Connective()
        conn_feat_name = FILE_PATH + '/../tmp/conn.feat'
        conn_feat_file = codecs.open(conn_feat_name, 'w', 'utf-8')
        checked_conns = []
        for art in articles:
            checked_conns.append(connParser.print_features(art, which, conn_feat_file))
        conn_feat_file.close()
        conn_pred_name = FILE_PATH + '/../tmp/conn.pred'
        Corpus.test_with_opennlp(conn_feat_name, connParser.model_file, conn_pred_name)
        conn_res = [l.strip().split()[-1] for l in codecs.open(conn_pred_name, 'r', 'utf-8')]
        assert len(checked_conns) == len(articles), 'article size not match'
        s = 0
        for art, cand_conns in zip(articles, checked_conns):
            length = len(cand_conns)
            cand_res = conn_res[s:s+length]
            s += length
            for conn, label in zip(cand_conns, cand_res):
                if label == '1':
                    rel = Relation()
                    rel.doc_id = art.id
                    rel.rel_type = 'Explicit'
                    rel.article = art
                    rel.conn_leaves = conn
                    rel.conn_addr = [n.leaf_id for n in conn]
                    art.exp_relations.append(rel)
        assert s == len(conn_res), 'conn size not match'

    def process_parsed_arg(self, articles, which='test'):
        arg_feat_name = FILE_PATH + '/../tmp/arg.feat'
        arg_feat_file = codecs.open(arg_feat_name, 'w', 'utf-8')
        arg_checked = []
        argParser = Argument()
        for art in articles:
            for rel in art.exp_relations:
                arg_checked.append(argParser.print_features(rel, which, arg_feat_file))
        arg_feat_file.close()
        arg_pred_name = FILE_PATH + '/../tmp/arg.pred'
        Corpus.test_with_opennlp(arg_feat_name, argParser.model_file, arg_pred_name)
        arg_res = [l.strip().split()[-1] for l in codecs.open(arg_pred_name, 'r', 'utf-8')]
        rid = 0
        s = 0
        for art in articles:
            for rel in art.exp_relations:
                args = arg_checked[rid]
                labels = arg_res[s:s+len(args)]
                rid += 1
                s += len(args)
                merge_result = argParser.merge(rel, args, labels)
                rel.arg1_leaves = merge_result['arg1'] if 'arg1' in merge_result else []

                # if current sentence couldn't resovle any arg1 leaves, we
                # consider previous root
                if len(rel.arg1_leaves) == 0:
                    # consider previous root if exists
                    conn_sid = args[0].goto_tree().sent_id
                    if conn_sid > 0:
                        prev_tree = rel.article.sentences[conn_sid-1].tree
                        if not prev_tree.is_null():
                            prev_root = prev_tree.root
                            tmp_feat_name = FILE_PATH+'/../tmp/arg.prev.feat'
                            tmp_file = codecs.open(tmp_feat_name, 'w', 'utf-8')
                            argParser.print_features(rel, which, tmp_file, prev_root)
                            tmp_file.close()
                            tmp_pred_name = FILE_PATH + '/../tmp/arg.prev.pred'
                            Corpus.test_with_opennlp(tmp_feat_name, argParser.model_file, tmp_pred_name)
                            tmp_res = [l.strip().split()[-1] for l in codecs.open(tmp_pred_name, 'r', 'utf-8')]
                            if tmp_res[0] == 'arg1':
                                rel.arg1_leaves = prev_root.get_leaves()

                rel.arg1_leaves = self.remove_leading_tailing_punc(rel.arg1_leaves)
                rel.arg1_addr = [n.leaf_id for n in rel.arg1_leaves]
                rel.arg1_sid = rel.arg1_leaves[-1].goto_tree().sent_id if len(rel.arg1_leaves) > 0 else -1
                rel.arg1_text = ' '.join(n.value for n in rel.arg1_leaves)
                rel.arg2_leaves = merge_result['arg2'] if 'arg2' in merge_result else []
                rel.arg2_leaves = self.remove_leading_tailing_punc(rel.arg2_leaves)
                rel.arg2_addr = [n.leaf_id for n in rel.arg2_leaves]
                rel.arg2_sid = rel.arg2_leaves[0].goto_tree().sent_id if len(rel.arg2_leaves) > 0 else -1
                rel.arg2_text = ' '.join(n.value for n in rel.arg2_leaves)

        assert len(arg_res) == s, 'arg candidate size not match'

    def process_exp_sense(self, articles, which='test'):
        exp_feat_name = FILE_PATH + '/../tmp/exp.feat'
        expParser = Explicit()
        exp_sense_file = codecs.open(exp_feat_name, 'w', 'utf-8')
        for art in articles:
            for rel in art.exp_relations:
                expParser.print_features(rel, ['xxxxx'], which, exp_sense_file)
        exp_sense_file.close()
        exp_pred = FILE_PATH + '/../tmp/exp.pred'
        Corpus.test_with_opennlp(exp_feat_name, expParser.model_file, exp_pred)

        exp_res = [l.strip().split()[-1] for l in codecs.open(exp_pred, 'r', 'utf-8')]
        rid = 0
        for art in articles:
            for rel in art.exp_relations:
                pred_sense = exp_res[rid]
                rel.sense = [pred_sense]
                rid += 1

    def process_nonexp_sense(self, articles, which):
        nonexp_feat_name = FILE_PATH + '/../tmp/nonexp.feat'
        nonexp_sense_file = codecs.open(nonexp_feat_name, 'w', 'utf-8')
        nonexpParser = NonExplicit()  # change name later
        for art in articles:
            self.generate_nonexp_relations(art)
            for rel in art.nonexp_relations:
                nonexpParser.print_features(rel, ['xxxxx'], nonexp_sense_file)
        nonexp_sense_file.close()
        nonexp_pred_name = FILE_PATH + '/../tmp/nonexp.pred'
        Corpus.test_with_opennlp(nonexp_feat_name, nonexpParser.model_file, nonexp_pred_name)
        nonexp_res = [l.strip().split()[-1] for l in codecs.open(nonexp_pred_name, 'r', 'utf-8')]

        rid = 0
        for art in articles:
            for rel in art.nonexp_relations:
                pred_sense = nonexp_res[rid]
                if pred_sense == 'EntRel':
                    r_type = 'EntRel'
                elif pred_sense == 'NoRel':
                    r_type = 'NoRel'
                else:
                    r_type = 'Implicit'
                rel.rel_type = r_type
                rel.sense = [pred_sense]
                rid += 1

        assert len(nonexp_res) == rid, 'nonexp relations size not match'

    def parse(self, parse_path, raw_home, output):
        """
        @param parse_path: json format parse file
        @param raw_home: raw text home
        """
        which = 'test'
        # TODO: connective identification
        articles =[]
        for art in Corpus.read_parses(parse_path):
            art.read_raw_text(raw_home+'/'+art.id)
            art.set_article_level_word_id()
            articles.append(art)

        self.process_parsed_conn(articles, which)

        # TODO: explicit argument extraction
        self.process_parsed_arg(articles, which)

        # TODO: explicit sense classification
        self.process_exp_sense(articles, which)

        # TODO: nonexp sense classification
        # generate candidate nonexp relations
        self.process_nonexp_sense(articles, which)

        # TODO: noexp argument post-process

        # output conll json format
        for art in articles:
            for rel in art.exp_relations + art.nonexp_relations:
                if rel.rel_type != 'NoRel':
                    print >> output, rel.output_json_format()

    def generate_nonexp_relations(self, article):
        for para in article.paragraphs:
            for s1, s2 in zip(para.sentences[:-1], para.sentences[1:]):
                if not article.has_exp_relation(s1.id):
                    # TODO: Add detail implementation
                    rel = Relation()
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

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser("Shallow Discourse Parser")
    arg_parser.add_argument('-c', '--input_home', help='test data home directory')
    arg_parser.add_argument('-o', '--output_home', help='output result home directory')
    arg_parser.add_argument('-r', '--result_name', help='output result file name')
    args = arg_parser.parse_args()
    # parse_path = args.input_home+'/pdtb-parses.json'
    # raw_path = args.input_home+'/raw'
    output_stream = codecs.open(args.output_home+'/'+args.result_name, 'w', 'utf-8')
    dp = DiscourseParser()
    dp.parse(DEV_PARSE_PATH, DEV_RAW_PATH, output_stream)
    output_stream.close()
