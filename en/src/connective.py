# -*- coding: utf-8 -*-
import sys
import os

from common import *
from corpus import Corpus

logs = sys.stderr
FILE_PATH = os.path.dirname(os.path.abspath(__file__))


class Connective():
    """
    Connective Identification Component
    """
    def __init__(self):
        self.train_file = FILE_PATH + '/../data/conll.conn.train'
        self.train_vec_file = FILE_PATH + '/../data/conll.conn.train.vec'
        self.feat_map_file = FILE_PATH + '/../data/conll.conn.map'
        self.test_file = FILE_PATH + '/../data/conll.conn.test'
        self.test_vec_file = FILE_PATH + '/../data/conll.conn.test.vec'
        self.model_file = FILE_PATH + '/../data/conll.conn.model'
        self.predicted_file = FILE_PATH + '/../data/conll.conn.test.predicted'

    def train(self):
        # to_file = open(self.train_file, 'w')
        # self.prepare_data(TRAIN_PARSE_PATH, TRAIN_REL_PATH, 'train', to_file)
        # to_file.close()
        Corpus.train_with_opennlp(self.train_file, self.model_file)
        # gen_svm_train(self.train_file, self.train_vec_file, self.feat_map_file)
        # svm_learn(self.train_vec_file, self.model_file)

    def test(self):
        # to_file = open(self.test_file, 'w')
        # self.prepare_data(DEV_PARSE_PATH, DEV_REL_PATH, 'test', to_file)
        # to_file.close()
        Corpus.test_with_opennlp(self.test_file, self.model_file, self.predicted_file)

        # feat_map = read_svm_map(self.feat_map_file)
        # gen_svm_test(self.test_file, feat_map, self.test_vec_file)
        # svm_classify(self.test_vec_file, self.model_file, self.predicted_file)

    def prepare_data(self, parse_path, rel_path, which, to_file):
        rel_dict = Corpus.read_relations(rel_path)
        for art in Corpus.read_parses(parse_path, rel_dict):
            for rel in art.relations:
                if rel.rel_type != 'Explicit':
                    continue
                rel.article = art
                rel.get_conn_leaves()
            self.print_features(art, which, to_file)

    def eval_data(self, stand_data, predicted_data):
        stand = [x.strip().split()[-1] for x in open(stand_data)]
        predicted = [x.strip().split()[-1] for x in open(predicted_data)]
        # predicted = [float(x.strip().split()[-1]) for x in open(predicted_data)]
        # tmp = []
        # for pred in predicted:
        #     if pred > 0:
        #         tmp.append('1')
        #     else:
        #         tmp.append('0')
        # predicted = tmp

        true_positive = true_negative = false_positive = false_negative = 0

        for i in range(len(stand)):
            if stand[i] == '1' and predicted[i] == '1':
                true_positive += 1
            elif stand[i] == '1' and predicted[i] == '0':
                false_negative += 1
            elif stand[i] == '0' and predicted[i] == '1':
                false_positive += 1
            else:
                true_negative += 1
        precision = true_positive*100.0/(true_positive+false_positive)
        recall = true_positive*100.0/(true_positive+false_negative)
        f1 = 2*precision*recall/(precision+recall)
        acc = (true_positive+true_negative)*100.0/(true_positive+
                                                   true_negative+
                                                   false_positive+
                                                   false_negative)
        print '====================result==================='
        print 'precision:'+str(precision)
        print 'recall:'+str(recall)
        print 'F1:'+str(f1)
        print 'accuracy:'+str(acc)
        print '============================================='

        return [precision, recall, f1, acc]

    def print_features(self, article, which, to_file):
        checked_conns = []
        for sentence in article.sentences:
            all_conns = sentence.check_connectives()
            checked_conns += all_conns
            for conn in all_conns:
                conn_str = '_'.join(n.value for n in conn)
                to_file_line = ''
                to_file_line += 'conn_lc:'+conn_str.lower()+' '
                to_file_line += 'conn:'+conn_str+' '

                conn_pos = '_'.join([x.parent_node.value for x in conn])
                to_file_line += 'lexsyn:conn_POS:'+conn_pos+' '

                prev_leaf = Corpus.get_other_leaf(conn[0], -1, article)
                if prev_leaf is not None:
                    to_file_line += 'lexsyn:with_prev_full:'+prev_leaf.value+'_'+conn_str+' '

                    prev_pos = prev_leaf.parent_node.value
                    to_file_line += 'lexsyn:prev_POS:'+prev_pos+' '
                    to_file_line += 'lexsyn:with_prev_POS:'+prev_pos+'_'+conn_pos.split('_')[0]+' '
                    to_file_line += 'lexsyn:with_prev_POS_full:'+prev_pos+'_'+conn_pos+' '

                next_leaf = Corpus.get_other_leaf(conn[-1], 1, article)
                if next_leaf is not None:
                    to_file_line += 'lexsyn:with_next_full:'+conn_str+'_'+next_leaf.value+' '

                    next_pos = next_leaf.parent_node.value
                    to_file_line += 'lexsyn:next_POS:'+next_pos+' '
                    to_file_line += 'lexsyn:with_next_POS:'+conn_pos.split('_')[-1]+'_'+next_pos+' '
                    to_file_line += 'lexsyn:with_next_POS_full:'+conn_pos+'_'+next_pos+' '

                # Pitler & Nenkova (ACL 09) features:
                # self_cat, parent_cat, left_cat, right_cat, right_VP, right_trace
                res = sentence.get_connective_categories(conn)

                res2 = ['selfCat:'+res[0],
                        'parentCat:'+res[1],
                        'leftCat:'+res[2],
                        'rightCat:'+res[3]]
                if res[4]:
                    res2.append('rightVP')
                if res[5]:
                    res2.append('rightTrace')

                for e in res2:
                    to_file_line += 'syn:'+e+' '

                for e in res2:
                    to_file_line += 'conn-syn:'+'conn:'+conn_str+'-'+e+' '

                for j in range(0, len(res2)):
                    for pair in res2[j+1:]:
                        to_file_line += 'syn-syn:'+res2[j]+'-'+pair+' '

                res3 = sentence.get_syntactic_features(*res[6])
                to_file_line += 'path-self>root:'+res3[0]+' '
                to_file_line += 'path-self>root2:'+res3[1]+' '

                label = '0'
                if conn in article.disc_connectives:
                    label = '1'
                to_file.write(to_file_line+' '+label+'\n')
        return checked_conns

if __name__ == '__main__':
    handler = Connective()
    handler.train()
    handler.test()
    handler.eval_data(handler.test_file, handler.predicted_file)
