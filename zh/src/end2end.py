#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

    def _process_parsed_conn(self, articles, which='test'):
        """
        generate explicit relation for each true discourse connective
        """
        connParser = Connective()
        conn_feat_name = FILE_PATH + '/../tmp/conn.feat'
        conn_feat_file = open(conn_feat_name, 'w')
        checked_conns = []
        for art in articles:
            checked_conns.append(connParser.print_features(art, which, conn_feat_file))
        conn_feat_file.close()
        conn_vec_name = FILE_PATH + '/../tmp/conn.vec'
        conn_pred_name = FILE_PATH + '/../tmp/conn.pred'
        Corpus.test_with_svm(conn_feat_name, connParser.feat_map_file, conn_vec_name, connParser.model_file, conn_pred_name)
        conn_res = [float(l.strip().split()[-1]) for l in open(conn_pred_name, 'r')]
        assert len(checked_conns) == len(articles), 'article size not match'
        s = 0
        for art, cand_conns in zip(articles, checked_conns):
            length = len(cand_conns)
            cand_res = conn_res[s:s+length]
            s += length
            for conn, label in zip(cand_conns, cand_res):
                if label > 0:
                    rel = Relation()
                    rel.doc_id = art.id
                    rel.rel_type = 'Explicit'
                    rel.article = art
                    rel.conn_leaves = conn
                    rel.conn_addr = [n.leaf_id for n in conn]
                    art.exp_relations.append(rel)
            # remove auto checked confilict connectives
            # art.remove_confilict_relations()
        assert s == len(conn_res), 'conn size not match'

    def _process_parsed_argpos(self, articles, which='test'):
        argpos_feat_name = FILE_PATH + '/../tmp/argpos.feat'
        argpos_feat_file = open(argpos_feat_name, 'w')
        argpos_checked = []
        argposParser = ArgPos()
        for art in articles:
            for rel in art.exp_relations:
                argpos_checked.append(argposParser.print_features(rel, which, argpos_feat_file))
        argpos_feat_file.close()
        argpos_pred_name = FILE_PATH + '/../tmp/argpos.pred'
        Corpus.test_with_opennlp(argpos_feat_name, argposParser.model_file, argpos_pred_name)
        argpos_res = [l.strip().split()[-1] for l in open(argpos_pred_name, 'r')]
        return argpos_res

    def _process_parsed_arg(self, articles, which='test'):
        arg_feat_name = FILE_PATH + '/../tmp/arg.feat'
        arg_feat_file = open(arg_feat_name, 'w')
        arg_checked = []
        argParser = Argument()
        for art in articles:
            for rel in art.exp_relations:
                arg_checked.append(argParser.print_features(rel, which, arg_feat_file))
        arg_feat_file.close()
        arg_vec_name = FILE_PATH + '/../tmp/arg.vec'
        arg_pred_name = FILE_PATH + '/../tmp/arg.pred'
        # Corpus.test_with_svm(arg_feat_name, argParser.feat_map_file, arg_vec_name, argParser.model_file, arg_pred_name)
        Corpus.test_with_opennlp(arg_feat_name, argParser.model_file, arg_pred_name)
        arg_res = [LABEL_ARG_MAP[l.strip().split()[-1]] for l in open(arg_pred_name, 'r')]

        tmp_feat_name = FILE_PATH+'/../tmp/arg.prev.feat'
        tmp_file = open(tmp_feat_name, 'w')
        for art in articles:
            for rel in art.exp_relations:
                conn_sid = rel.conn_leaves[0].goto_tree().sent_id
                if conn_sid > 0:
                    prev_tree = rel.article.sentences[conn_sid-1].tree
                    if not prev_tree.is_null():
                        prev_root = prev_tree.root
                        argParser.print_features(rel, which, tmp_file, prev_root)
        tmp_file.close()
        tmp_pred_name = FILE_PATH + '/../tmp/arg.prev.pred'
        tmp_vec_name = FILE_PATH + '/../tmp/arg.prev.vec'
        # Corpus.test_with_svm(tmp_feat_name, argParser.feat_map_file, tmp_vec_name, argParser.model_file, tmp_pred_name)
        Corpus.test_with_opennlp(tmp_feat_name, argParser.model_file, tmp_pred_name)
        arg_prev_res = [LABEL_ARG_MAP[l.strip().split()[-1]] for l in open(tmp_pred_name, 'r')]

        rid = 0
        s = 0
        index = 0
        for art in articles:
            for rel in art.exp_relations:
                args = arg_checked[rid]
                labels = arg_res[s:s+len(args)]
                rid += 1
                s += len(args)
                merge_result = argParser.merge(rel, args, labels)
                rel.arg1_leaves = merge_result['arg1'] if 'arg1' in merge_result else []
                conn_sid = args[0].goto_tree().sent_id

                # if current sentence couldn't resovle arg leaves, consider previous root as a candidate
                if len(rel.arg1_leaves) == 0 and conn_sid > 0 and arg_prev_res[index] == 'arg1':
                    rel.arg1_leaves = rel.article.sentences[conn_sid-1].leaves

                if len(rel.arg2_leaves) == 0 and conn_sid > 0 and arg_prev_res[index] == 'arg2':
                    rel.arg2_leaves = rel.article.sentences[conn_sid-1].leaves

                if conn_sid > 0:
                    index += 1

                rel.arg1_leaves = self.remove_leading_tailing_punc(rel.arg1_leaves)
                rel.arg1_addr = [n.leaf_id for n in rel.arg1_leaves]
                rel.arg1_sid = rel.arg1_leaves[-1].goto_tree().sent_id if len(rel.arg1_leaves) > 0 else -1
                rel.arg1_text = ' '.join(n.value for n in rel.arg1_leaves)
                rel.arg2_leaves = merge_result['arg2'] if 'arg2' in merge_result else []
                rel.arg2_leaves = self.remove_leading_tailing_punc(rel.arg2_leaves)
                rel.arg2_addr = [n.leaf_id for n in rel.arg2_leaves]
                rel.arg2_sid = rel.arg2_leaves[0].goto_tree().sent_id if len(rel.arg2_leaves) > 0 else -1
                rel.arg2_text = ' '.join(n.value for n in rel.arg2_leaves)

        assert len(arg_prev_res) == index, 'arg prev size not match'
        assert len(arg_res) == s, 'arg candidate size not match'

    def _process_exp_sense(self, articles, which='test'):
        exp_feat_name = FILE_PATH + '/../tmp/exp.feat'
        expParser = Explicit()
        exp_sense_file = open(exp_feat_name, 'w')
        for art in articles:
            for rel in art.exp_relations:
                expParser.print_features(rel, ['Conjunction'], which, exp_sense_file)
        exp_sense_file.close()
        exp_vec = FILE_PATH + '/../tmp/exp.vec'
        exp_pred = FILE_PATH + '/../tmp/exp.pred'
        # Corpus.test_with_svm(exp_feat_name, expParser.feat_map_file, exp_vec, expParser.model_file, exp_pred)
        Corpus.test_with_opennlp(exp_feat_name, expParser.model_file, exp_pred)

        exp_res = [LABEL_SENSES_MAP[l.strip().split()[-1]] for l in open(exp_pred, 'r')]
        rid = 0
        for art in articles:
            for rel in art.exp_relations:
                pred_sense = exp_res[rid]
                rel.sense = [pred_sense]
                rid += 1

    def _process_nonexp_sense(self, articles, which):
        nonexp_feat_name = FILE_PATH + '/../tmp/nonexp.feat'
        nonexp_sense_file = open(nonexp_feat_name, 'w')
        nonexpParser = NonExplicit()  # change name later
        for art in articles:
            self.generate_nonexp_relations(art)
            for rel in art.nonexp_relations:
                nonexpParser.print_features(rel, ['xxxxx'], nonexp_sense_file)
        nonexp_sense_file.close()
        nonexp_pred_name = FILE_PATH + '/../tmp/nonexp.pred'
        Corpus.test_with_opennlp(nonexp_feat_name, nonexpParser.model_file, nonexp_pred_name)
        nonexp_res = [l.strip().split()[-1] for l in open(nonexp_pred_name, 'r')]

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

    def _post_process_nonexp_arguments(self, articles, which='test'):
        attrParser = Attribution()
        attr_feat_name = FILE_PATH + '/../tmp/attr.feat'
        attr_file = codecs.open(attr_feat_name, 'w', 'utf-8')
        for art in articles:
            for rel in art.nonexp_relations:
                if rel.rel_type == 'Implicit':
                    s1_clauses = art.sentences[rel.arg1_sid].clauses
                    s2_clauses = art.sentences[rel.arg2_sid].clauses

                    # for argument 1
                    for idx, clause in enumerate(s1_clauses):
                        prev_clause = s1_clauses[idx-1] if idx > 0 else None
                        next_clause = s1_clauses[idx+1] if idx < len(s1_clauses) -1 else None
                        attrParser.print_features(clause, prev_clause, next_clause, rel.arg1_leaves, which, attr_file)

                    # for argument 2
                    for idx, clause in enumerate(s2_clauses):
                        prev_clause = s2_clauses[idx-1] if idx > 0 else None
                        next_clause = s2_clauses[idx+1] if idx < len(s2_clauses) -1 else None
                        attrParser.print_features(clause, prev_clause, next_clause, rel.arg2_leaves, which, attr_file)
        attr_file.close()

        attr_pred_name = FILE_PATH + '/../tmp/attr.pred'
        Corpus.test_with_opennlp(attr_feat_name, attrParser.model_file, attr_pred_name)
        attr_res = [l.strip().split()[-1] for l in codecs.open(attr_pred_name, 'r', 'utf-8')]

        # combine results
        idx = 0
        for art in articles:
            for rel in art.nonexp_relations:
                if rel.rel_type == 'Implicit':
                    s1_clauses = art.sentences[rel.arg1_sid].clauses
                    s2_clauses = art.sentences[rel.arg2_sid].clauses

                    # for argument 1
                    arg1_leaves = []
                    for clause in s1_clauses:
                        if len(clause) == 1 and is_punc(clause[0].parent_node.value):
                            arg1_leaves += clause
                        elif attr_res[idx] != '1':
                            arg1_leaves += clause
                        idx += 1

                    rel.arg1_leaves = arg1_leaves

                    # for argument 2
                    arg2_leaves = []
                    for clause in s2_clauses:
                        if len(clause) == 1 and is_punc(clause[0].parent_node.value):
                            arg2_leaves += clause
                        elif attr_res[idx] != '1':
                            arg2_leaves += clause
                        idx += 1

                    rel.arg2_leaves = arg2_leaves

                    rel.arg1_leaves = self.remove_leading_tailing_punc(rel.arg1_leaves)
                    rel.arg1_addr = [n.leaf_id for n in rel.arg1_leaves]
                    rel.arg1_text = ' '.join(n.value for n in rel.arg1_leaves)

                    rel.arg2_leaves = self.remove_leading_tailing_punc(rel.arg2_leaves)
                    rel.arg2_addr = [n.leaf_id for n in rel.arg2_leaves]
                    rel.arg2_text = ' '.join(n.value for n in rel.arg2_leaves)

        assert len(attr_res) == idx, 'attrbution counts not match'

    def parse(self, parse_path, raw_home, output):
        """
        @param parse_path: json format parse file
        @param raw_home: raw text home
        """
        which = 'test'
        # TODO: connective identification
        articles =[]
        for art in Corpus.read_parses(parse_path):
            # art.read_raw_text(raw_home+'/'+art.id)
            art.set_article_level_word_id()
            articles.append(art)
        # articles.sort(key=lambda x:x.id)

        print >> logs, "===read data compelete==="

        print >> logs, "===1. connective identification==="
        self._process_parsed_conn(articles, which)

        # TODO: explicit argument extraction
        print >> logs, "===2. argument extraction==="
        self._process_parsed_arg(articles, which)

        # TODO: explicit sense classification
        print >> logs, "===3. explicit sense classification==="
        self._process_exp_sense(articles, which)

        # TODO: nonexp sense classification
        # generate candidate nonexp relations
        print >> logs, "===4. nonexp sense classification==="
        self._process_nonexp_sense(articles, which)

        # TODO: nonexp argument post-process
        print >> logs, "===5. nonexp arguments postproceesing==="
        # self._post_process_nonexp_arguments(articles, which)

        print >> logs, "===6. convert into json format==="
        # output conll json format
        for art in articles:
            for rel in art.exp_relations + art.nonexp_relations:
                if rel.rel_type != 'NoRel':
                    print >> output, rel.output_json_format()

        print >> logs, "===done.==="

    def generate_nonexp_relations(self, article):
        for s1, s2 in zip(article.sentences[:-1], article.sentences[1:]):
            if not article.has_exp_inter_relation(s1.id):
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

        # sentence intra nonexp relation
        for sen in article.sentences:
            tree = sen.tree
            if len(sen.clauses) <= 1 :
                continue
            for c1, c2 in zip(sen.clauses[:-1], sen.clauses[1:]):
                if not article.has_exp_intra_relation(sen.id):
                    rel = Relation()
                    rel.article = article
                    rel.doc_id = article.id
                    rel.arg1s['parsed'] = tree.find_subtrees(c1)
                    rel.arg1_leaves = self.remove_leading_tailing_punc(c1)
                    rel.arg1_addr = [n.leaf_id for n in rel.arg1_leaves]
                    rel.arg1_sid = sen.id
                    rel.arg1_text = ' '.join(n.value for n in rel.arg1_leaves)

                    rel.arg2s['parsed'] = tree.find_subtrees(c2)
                    rel.arg2_leaves = self.remove_leading_tailing_punc(c2)
                    rel.arg2_addr = [n.leaf_id for n in rel.arg2_leaves]
                    rel.arg2_sid = sen.id
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
