__author__ = 'Sheng'
import sys
import re
from collections import defaultdict


class DepNode(object):
    __slots__ = ('value', 'child_nodes', 'parent', 'relation')

    def __init__(self, v):
        self.value = v
        self.child_nodes = []
        self.parent = None
        self.relation = None

    def __str__(self):
        print 'parent:%s-%s;relation:%s' % (self.parent.value, self.value, self.relation)


class DepTree(object):
    __slots__ = ('sentence', 'text', 'nodes')
    """
    Model Dependency Tree
    """
    def __init__(self, sen, depText):
        self.sentence = sen
        self.text = depText
        self.nodes = []
        for leaf in self.sentence.leaves:
            leaf.dep = DepNode(leaf.value)
            self.nodes.append(leaf.dep)
        self.build_dependency_tree(depText)

    def build_dependency_tree(self, depText):
        for rule in depText:
            relation = rule[0].encode('utf-8')
            w1 = rule[1]
            w2 = rule[2]

            pidx = int(w1.split('-')[-1]) - 1
            cidx = int(w2.split('-')[-1]) - 1
            if pidx < 0:
                continue
            parent = self.nodes[pidx]
            child = self.nodes[cidx]
            parent.child_nodes.append(child)
            child.parent = parent
            child.relation = relation

    @staticmethod
    def get_dependency_rules(rule_dict, nodes, with_leaf=True, with_label=True):
        for leaf in nodes:
            dnode = leaf.dep
            if dnode and len(dnode.child_nodes) != 0:
                rule = '%s<-' % dnode.value
                if with_label and with_leaf:
                    rule += '_'.join('<%s>:%s' % (c.relation, c.value) for c in dnode.child_nodes)
                elif with_label:
                    rule += '_'.join('<%s>' % c.relation for c in dnode.child_nodes)
                elif with_leaf:
                    rule += '_'.join('%s' % c.relation for c in dnode.child_nodes)
                if not re.search('<-$', rule):
                    rule_dict[rule] += 1

if __name__ == '__main__':
    pass
