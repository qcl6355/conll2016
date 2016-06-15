#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Sheng Li"
import sys
import os
import math
from collections import defaultdict

class Document:
    def __init__(self, label, words):
        self.label = label
        self.words = words

    def __str__(self):
        return "%s|%d" % (self.label, len(self.words))

def read_svm_map(feat_file):
    word_map = {}
    for line in open(feat_file):
        word, idx= line.strip().split('')
        word_map[word] = int(idx)
    return word_map

def gen_svm_train(train_file, vec_file, feat_file):
    docs = []
    for line in open(train_file):
        tks = line.strip().split()
        label = tks[-1]
        ws = defaultdict(float)
        for t in tks[:-1]:
            t= t.strip()
            if t != "":
                ws[t] += 1.
        docs.append(Document(label, ws))

    word_map = {}
    index = 1
    to_file = open(vec_file, 'w')
    for doc in docs:
        fv = defaultdict(float)
        for word in doc.words:
            if word not in word_map:
                word_map[word] = index
                index += 1
            fv[word_map.get(word)] = doc.words[word]

        l2_norm = math.sqrt(sum(v*v for v in fv.values()))
        print >> to_file, doc.label + ' ' + ' '.join('%d:%f' % (k, v / l2_norm) for k, v in sorted(fv.items(), key=lambda x:x[0]))
    to_file.close()

    map_file = open(feat_file, 'w')
    for word, idx in word_map.items():
        print >> map_file, '%s%d' % (word, idx)
    map_file.close()


def gen_svm_test(test_file, word_map, vec_file):
    to_file = open(vec_file, 'w')
    for line in open(test_file):
        tks = line.strip().split()
        label = tks[-1]
        tmp = defaultdict(float)
        for word in tks[:-1]:
            if word in word_map:
                tmp[word] += 1.0

        doc = {}
        for w in tmp:
            doc[word_map.get(w)] = tmp[w]

        l2_norm = math.sqrt(sum(v*v for v in doc.values()))
        print >> to_file, label + ' ' + ' '.join('%d:%f' % (k, v / l2_norm) for k, v in sorted(doc.items(), key=lambda x:x[0]))
    to_file.close()


def svm_learn(train_file, model_file):
    cmd = SVM_LEARN + ' %s %s' % (train_file, model_file)
    os.system(cmd)


def svm_classify(test_file, model_file, pred_file):
    cmd = SVM_CLASSIFY + ' %s %s %s' % (test_file, model_file, pred_file)
    os.system(cmd)

"""
Specify constant variables and useful functions
"""

def aset(st):
    """ aset("A B C") => set(["A", "B", "C"]) """
    return set(st.split())


punc_tags = aset("# $ `` '' -LRB- -RRB- , . : PU")
verb_tags = aset("VB VBD VBG VBN VBP VBZ MD")
punctuation = aset("`` '' ` ' ( ) { } [ ] , . ! ? : ; ... --")

CLAUSE_PUNCS = aset("， 。 ！ ？")

def is_punc(label):
    return label in punc_tags


def is_verb(label):
    return label in verb_tags


CORPUS_HOME = '/Users/Sheng/corpora/conll16st-en-zh-dev-train'

TRAIN_REL_PATH = CORPUS_HOME + '/conll16st-zh-01-08-2016-train/relations.json'
DEV_REL_PATH = CORPUS_HOME + '/conll16st-zh-01-08-2016-dev/relations.json'
TRAIN_PARSE_PATH = CORPUS_HOME + '/conll16st-zh-01-08-2016-train/parses.json'
DEV_PARSE_PATH = CORPUS_HOME + '/conll16st-zh-01-08-2016-dev/parses.json'
TRAIN_RAW_PATH = CORPUS_HOME + '/conll16st-zh-01-08-2016-train/raw'
DEV_RAW_PATH = CORPUS_HOME + '/conll16st-zh-01-08-2016-dev/raw'


SENSES = {
    'Alternative',
    'Causation',
    'Conditional',
    'Conjunction',
    'Contrast',
    'EntRel',
    'Expansion',
    'Progression',
    'Purpose',
    'Temporal',
}

SENSES_LABEL_MAP = {
        'Alternative':'0',
        'Causation':'1',
        'Conditional':'2',
        'Conjunction':'3',
        'Contrast':'4',
        'EntRel':'5',
        'Expansion':'6',
        'Progression':'7',
        'Purpose':'8',
        'Temporal':'9'}

LABEL_SENSES_MAP = {
        '0':'Alternative',
        '1':'Causation',
        '2':'Conditional',
        '3':'Conjunction',
        '4':'Contrast',
        '5':'EntRel',
        '6':'Expansion',
        '7':'Progression',
        '8':'Purpose',
        '9':'Temporal'}

ARG_LABEL_MAP = {'None':'0', 'arg1':'1', 'arg2':'2'}
LABEL_ARG_MAP = {'0':'None', '1':'arg1', '2':'arg2'}


# feature classes
VERB_SIGN = 'verb'  # verb features
MOD_SIGN = 'mod'  # modality
POL_SIGN = 'pol'  # polarity tags
FIRST_SIGN = 'first'  # first last and first3
PRODUCT_SIGN = 'product'  # product rules
WORD_SIGN = 'word'  # word pair
CONN_SIGN = 'connective'  # sentence connective

ALL_FEATS = [VERB_SIGN, POL_SIGN, MOD_SIGN, FIRST_SIGN, PRODUCT_SIGN, WORD_SIGN, CONN_SIGN]

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = CURR_DIR + '/../../lib'
CLASSPATH = CURR_DIR + '/../../eval:' + LIB_DIR + '/maxent-2.5.2/lib/trove.jar:' + \
            LIB_DIR + '/maxent-2.5.2/output/maxent-2.5.2.jar:'
# SVM_LEARN = LIB_DIR + '/svm_light/svm_learn'
# SVM_CLASSIFY = LIB_DIR + '/svm_light/svm_classify'

SVM_LEARN = LIB_DIR + '/libsvm/svm-train -t 0'
SVM_CLASSIFY = LIB_DIR + '/libsvm/svm-predict'


CONN_GROUP = ['此外 还 有', '另 一 方面', '与 此 同时', '何况 还 有', '在 此 之前', '但 实际上', '另外 还', '同时 也', '是 为了', '尽管如此', '正 因为', '同时 亦', '从而 使', '有鉴于此', '相反 的', '从而 也', '换句话说', '同时 还', '也 因此', '特别是', '事实上', '每 当', '也 就', '每 逢', '以 期', '为 此', '以 使', '尤其是', '却 也', '由 此', '直 至', '若 是', '进一步', '还 有', '自 此', '特别', '于是', '以来', '仍然', '尤其', '於是', '否则', '以免', '包括', '不过', '所以', '使得', '然后', '进而', '通过', '不管', '首先', '此前', '不论', '例如', '随後', '诸如', '反倒', '假使', '但是', '像是', '再说', '之后', '因为', '以及', '为了', '因而', '随着', '总之', '只要', '其中', '同时', '以便', '或是', '从而', '只是', '由于', '结果', '继而', '每当', '然而', '初期', '最后', '同样', '此后', '另外', '相反', '而且', '甚至', '此外', '以后', '无论', '经过', '期间', '其後', '之前', '虽然', '加上', '这样', '如果', '假如', '不久', '还是', '加之', '其次', '因此', '最终', '后来', '尽管', '一旦', '随后', '鉴於', '即使', '至於', '由於', '更是', '并且', '要', '一', '再', '而', '且', '但', '经', '不', '是', '如', '和', '可', '间', '及', '故', '前', '也', '因', '来', '令', '连', '后', '另', '或', '为', '先', '仍', '以', '若', '却', '并', '後', '则', '亦', '就', '更', '又', '时', '才', '还', '即', '使']
CONN_INTRA = ['之所以..是 因为..的 缘故', '如果 说..的话..那么..又', '在..下..在..的 基础 上', '（ 丙 ）..及 （ 丁 ）', '（ 一 ）..及 （ 二 ）', '在..的 情况 下..还', '一 方面..一 方面 也', '的 目的..就 是 要', '大概 是 由于..所以', '在..时..在..时', '在..的 同时..还', '在..的 同时..却', '因为..因为..由於', '一 方面..一 方面', '远 不 是..而 是', '在..的 同时..也', '不 要 说..就 连', '在..的 情况 下', '与 此 同时..还', '如果..那么..就', '不..不..而 是', '之所以..是 因为', '就 在..的 时候', '与 此 同时..也', '在..的 过程 中', '不 是..却 是', '并 不..而 是', '继..以来..又', '如果..仍然 还', '但是..同时 又', '不仅..而且 还', '不 是..才 是', '二 是..三 是', '正 值..之 际', '仅仅 因为..就', '一 是..二 是', '不 是..而 是', '除了..外..还', '虽然..但..却', '不仅..而且 也', '在..过程 中', '在..的 同时', '只有..才 能', '而..就 更为', '在..的 年代', '不 再..只是', '每 到..时节', '除..外..并', '的 同时..也', '除..外..也', '无论..也 会', '除..外..还', '当..的 时候', '不管..还 是', '不..不..而', '在..的 时候', '并 不..而', '正 当..时', '要 想..就', '除了..之外', '由于..所以', '经过..之后', '本来..结果', '但 也..并', '不管..还是', '由于..因而', '早 在..中', '别 说..连', '自从..以后', '如果..那么', '与其..不如', '为了..为了', '不仅..而且', '即使..至少', '尽管..但是', '虽然..但是', '自从..以来', '尽管..仍然', '同时..还', '然而..也', '只有..才', '只要..就', '除了..外', '是..还是', '另外..也', '由於..故', '随着..也', '不仅..更', '在..之后', '不过..并', '此外..还', '而且..也', '继..之后', '在..之际', '同时..并', '自..以来', '同时..也', '通过..使', '不论..都', '尽管..但', '不论..均', '此外..也', '还..甚至', '至于..则', '虽然..但', '不仅..还', '同时..更', '从..以来', '不管..总', '至於..则', '如果..就', '由于..令', '首先..再', '如果..则', '不仅..也', '即便..也', '一旦..就', '在..期间', '另外..还', '但是..也', '如果..将', '先..然后', '在..上', '在..下', '在..后', '而..亦', '在..中', '在..前', '不..而', '而..却', '不..就', '一..就', '二..三', '如..则', '从..后', '当..时', '如..就', '只..就', '三..四', '而..又', '除..外', '既..又', '或..或', '但..却', '而..则', '继..后', '一..二', '如..便', '而..也', '因..故', '自..後', '虽..却', '虽..但', '後..才', '既..也', '在..後', '但..则', '自..后', '还..再', '若..就', '后..还', '当..后', '到..时', '在..时', '当..後']

# CONN_INTRA = ['在..的 同时']

def cross_product(feat1, feat2):
    if len(feat1) == 0 or len(feat2) == 0:
        return
    res = {}
    for k1 in feat1:
        for k2 in feat2:
            k = '%s_%s' % (k1, k2)
            v = feat1[k1] * feat2[k2]
            res[k] = v
    return res


def read_trees(file_path):
    parsed = []
    raw = ""
    for line in open(file_path):
        # begin a new parse tree
        if re.search(r'^\((S1|ROOT|TOP|S)? ?\(', line):
            if raw.strip() != "":
                parsed.append(raw)
            raw = line
        else:
            raw += line
    if raw.strip() != "":
        parsed.append(raw)
    return parsed


def evaluate(gold, predict):
    assert len(gold) == len(predict)

    acc = defaultdict(int)
    p_count = defaultdict(int)
    g_count = defaultdict(int)
    over_acc = 0

    for p, g in zip(predict, gold):
        p_count[p] += 1
        for ag in g:
            g_count[ag] += 1
        if p in g:
            acc[p] += 1
            over_acc += 1

    for k in g_count:
        if acc[k] > 0:
            print k
            print_measure(acc[k], p_count[k], g_count[k])
        else:
            print "key :%s = 0; gold count:%s" % (k, g_count[k])

    print
    print "acc_count:%s, all_count:%s \t overall accuracy:\t %.2f" % \
          (over_acc, len(gold), over_acc * 100.0 / len(gold))


def print_measure(acc, p_count, g_count):
    print acc, p_count, g_count

    p = acc * 1.0 / p_count
    r = acc * 1.0 / g_count
    f1 = 2 * p * r / (p + r)

    sys.stdout.write('precision:%.2f\t' % (p*100.0))
    sys.stdout.write('recall:%.2f\t' % (r * 100.0))
    sys.stdout.write('F1:%.2f\n' % (f1 * 100.0))
    print
    return [p, r, f1]

if __name__ == '__main__':
    print set(Conn_group) - set(PDTB_Conn_group)
