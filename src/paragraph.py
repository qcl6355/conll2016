__author__ = 'Sheng Li'

class Paragraph(object):
    __slots__ = ('sentences', 'id', 'article', 'begin_offset', 'end_offset')

    def __init__(self, sc, ec, pid):
        self.id = pid
        self.begin_offset = sc
        self.end_offset = ec
        self.sentences = []

    # def __init__(self, all_sents, start_sid, end_sid, pid):
    #     self.sentences = all_sents[start_sid:end_sid]
    #     self.id = pid
    #     self.article = None

    def __getitem__(self, i):
        return self.sentences[i]

    def __len__(self):
        return len(self.sentences)

    # check adjacent sentences has explicit relation
    def has_exp_relation(self, idx):
        sid1 = self.sentences[idx].id
        sid2 = self.sentences[idx+1].id

        for rel in self.article.exp_relations:
            if rel.arg1_sid == sid1 and rel.arg2_sid == sid2:
                return True
        return False

    def __str__(self):
        return 'begin %s, end %s' % (self.begin_offset, self.end_offset)

    __repr__ = __str__

if __name__ == '__main__':
    pass
