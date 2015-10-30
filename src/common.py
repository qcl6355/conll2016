# -*- coding: utf-8 -*-
__author__ = "Sheng Li"
import os
"""
Specify constant variables and useful functions
"""

def aset(st):
    """ aset("A B C") => set(["A", "B", "C"]) """
    return set(st.split())


punc_tags = aset("# $ `` '' -LRB- -RRB- , . :")
verb_tags = aset("VB VBD VBG VBN VBP VBZ MD")
punctuation = aset("`` '' ` ' ( ) { } [ ] , . ! ? : ; ... --")


def is_punc(label):
    return label in punc_tags


def is_verb(label):
    return label in verb_tags


CORPUS_HOME = '/Users/Sheng/corpora/conll15st-train-dev/conll15st_data'

TRAIN_REL_PATH = CORPUS_HOME + '/pdtb-data-01-20-15-train.json'
DEV_REL_PATH = CORPUS_HOME + '/pdtb-data-01-20-15-dev.json'
TRAIN_PARSE_PATH = CORPUS_HOME + '/pdtb-parses-01-12-15-train.json'
DEV_PARSE_PATH = CORPUS_HOME + '/pdtb-parses-01-12-15-dev.json'
TRAIN_RAW_PATH = CORPUS_HOME + '/raw_train'
DEV_RAW_PATH = CORPUS_HOME + '/raw_dev'


SENSES = {'Temporal.Asynchronous.Precedence',
		'Temporal.Asynchronous.Succession',
		'Temporal.Synchrony',
		'Contingency.Cause.Reason',
		'Contingency.Cause.Result',
		'Contingency.Condition',
		'Comparison.Contrast',
		'Comparison.Concession',
		'Expansion.Conjunction',
		'Expansion.Instantiation',
		'Expansion.Restatement',
		'Expansion.Alternative',
		'Expansion.Alternative.Chosen_alternative',
		'Expansion.Exception',
		'EntRel',
                }


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
LIB_DIR = CURR_DIR + '/../lib'
CLASSPATH = CURR_DIR + '/../eval:' + LIB_DIR + '/maxent-2.5.2/lib/trove.jar:' + \
            LIB_DIR + '/maxent-2.5.2/output/maxent-2.5.2.jar:'

Conn_group = ['on the other hand', 'in the mean time', 'as soon as', 'as long as', 'in the end', 'as an alternative', 'as a result', 'before and after', 'on the contrary', 'when and if', 'in other words', 'if and when', 'in addition', 'by comparison', 'in sum', 'by contrast', 'insofar as', 'in short', 'for instance', 'for example', 'in particular', 'in turn', 'as if', 'now that', 'much as', 'in fact', 'in contrast', 'as though', 'as well', 'so that', 'by then', 'lest',
'particularly', 'indeed', 'still', 'yet', 'also', 'except', 'meantime', 'finally', 'then', 'thereby', 'meanwhile', 'overall', 'nor', 'alternatively', 'separately', 'because', 'further', 'ultimately', 'for', 'furthermore', 'since', 'before', 'after', 'simultaneously', 'however', 'besides', 'afterward', 'afterwards', 'plus', 'hence', 'or', 'otherwise', 'regardless', 'although', 'previously', 'thereafter', 'moreover', 'similarly', 'specifically', 'next', 'accordingly', 'therefore', 'until', 'but', 'else', 'while', 'and', 'likewise', 'thus', 'as', 'conversely', 'if', 'nonetheless', 'whereas', 'when', 'till', 'instead', 'unless', 'though', 'earlier', 'upon', 'additionally', 'nevertheless', 'consequently', 'later', 'rather', 'so', 'once']
Conn_intra = ['if..then', 'neither..nor', 'either..or']
Conn_inter = ['on the one hand..on the other hand']

PDTB_Conn_group = ["on the other hand",
  "as a result", "as an alternative", "as long as", "as soon as",
  "before and after", "if and when", "in other words", "in the end", "on the contrary", "when and if",
  "as if", "as though", "as well", "by comparison", "by contrast", "by then", "for example", "for instance",
  "in addition", "in contrast", "in fact", "in particular", "in short", "in sum", "in turn", "insofar as",
  "much as", "now that", "so that",
  "accordingly", "additionally", "after", "afterward", "also", "alternatively", "although", "and", "as",
  "because", "before", "besides", "but", "consequently", "conversely", "earlier", "else", "except",
  "finally", "for", "further", "furthermore", "hence", "however", "if", "indeed", "instead", "later",
  "lest", "likewise", "meantime", "meanwhile", "moreover", "nevertheless", "next", "nonetheless", "nor",
  "once", "or", "otherwise", "overall", "plus", "previously", "rather", "regardless", "separately",
  "similarly", "simultaneously", "since", "so", "specifically", "still", "then", "thereafter",
  "thereby", "therefore", "though", "thus", "till", "ultimately", "unless", "until", "when", "whereas",
  "while", "yet"]

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
        # begin a new parsed tree
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
