"""
Processor for performing part-of-speech tagging
"""
import os

from classla.models.common import doc
from classla.models.common.pretrain import Pretrain
from classla.models.common.utils import unsort
from classla.models.pos.data import DataLoader
from classla.models.pos.trainer import Trainer
from classla.pipeline._constants import *
from classla.pipeline.processor import UDProcessor, register_processor

@register_processor(name=POS)
class POSProcessor(UDProcessor):

    # set of processor requirements this processor fulfills
    PROVIDES_DEFAULT = set([POS])
    # set of processor requirements for this processor
    REQUIRES_DEFAULT = set([TOKENIZE])

    def _set_up_model(self, config, use_gpu):
        # get pretrained word vectors
        self._pretrain = Pretrain(config['pretrain_path']) if 'pretrain_path' in config else None

        if 'use_lexicon' in self.config and self.config['use_lexicon']:
            assert 'lemma_model_path' in self.pipeline.config, 'If `pos_use_lexicon` tag is used, you must add lemma processor to processors!'
            arg = {'constrain_via_lexicon': self.pipeline.config['lemma_model_path']}
        else:
            arg = None
        # set up trainer
        self._trainer = Trainer(args=arg, pretrain=self.pretrain, model_file=config['model_path'], use_cuda=use_gpu)

    def process(self, document):
        batch = DataLoader(
            document, self.config['batch_size'], self.config, self.pretrain, vocab=self.vocab, evaluation=True,
            sort_during_eval=True)
        preds = []
        for i, b in enumerate(batch):
            preds += self.trainer.predict(b)
        preds = unsort(preds, batch.data_orig_idx)
        batch.doc.set([doc.UPOS, doc.XPOS, doc.FEATS], [y for x in preds for y in x])
        return batch.doc
