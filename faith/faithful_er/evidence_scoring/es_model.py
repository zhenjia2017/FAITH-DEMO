"""
A CrossEncoder takes a sentence pair as input and outputs a label. Here, it output a continious labels 0...1 to indicate the similarity between the input pair.
It does NOT produce a sentence embedding and does NOT work for individual sentences.
"""
import math
import time
import csv
import numpy as np
import os
from faith.library.utils import get_logger
from sentence_transformers.cross_encoder import CrossEncoder
from sentence_transformers.cross_encoder.evaluation import CEBinaryClassificationEvaluator
from sentence_transformers.readers import InputExample
from faith.faithful_er.evidence_scoring.dataset_es import DatasetES

from torch.utils.data import DataLoader

import torch

class ESModel(torch.nn.Module):
    def __init__(self, config, benchmark):
        super(ESModel, self).__init__()
        self.config = config
        self.logger = get_logger(__name__, config)
        self.benchmark = benchmark
        self.data_dir = self.config["path_to_data"]
        self.bert_model_name = self.config["bert_model"]
        self.bert_pretrain_model = self.config["bert_pretrained_model"]
        self.bert_save_model_faith = os.path.join(self.data_dir, self.benchmark, "faith", self.bert_model_name)
        self.bert_save_model_unfaith = os.path.join(self.data_dir, self.benchmark, "unfaith", self.bert_model_name)

        self.dataset = DatasetES(config)
        self.bert_sample_method = config["es_sample_method"]
        self.model = CrossEncoder(self.bert_pretrain_model, num_labels=1)
        self.logger.info(
            "Use pytorch device: {}".format("cuda" if torch.cuda.is_available() else "cpu")
        )


    def load(self, faith_or_unfaith):
        """Load model."""
        if faith_or_unfaith == "faith":
            print("Loading Faith ES model from:", self.bert_save_model_faith)
            self.bert_save_model = self.bert_save_model_faith
        else:
            print("Loading UnFaith ES model from:", self.bert_save_model_unfaith)
            self.bert_save_model = self.bert_save_model_unfaith
            
        self.model = CrossEncoder(self.bert_save_model)

    def inference_top_k(self, query, evidences, max_evidence):
        """
        Retrieve the top-100 evidences among the retrieved ones,
        for the given AR.
        """
        start = time.time()
        if not evidences:
            return evidences
        mapping = {}

        query_evidence_pairs = list()
        for evidence in evidences:
            # remove noise in evidence texts
            evidence_text = evidence["evidence_text"].replace("\n", " ").replace("\t", " ")
            if evidence_text not in mapping:
                mapping[evidence_text] = list()
            mapping[evidence_text].append(evidence)
        # Compute embedding for both lists
        evidence_texts = list(mapping.keys())
        top_evidences = list()
        for evidence_text in evidence_texts:
            query_evidence_pairs.append([query, evidence_text])

        similarity_scores = self.model.predict(query_evidence_pairs)
        sim_scores_argsort = reversed(np.argsort(similarity_scores))
        scored_evidences = [query_evidence_pairs[idx] for idx in sim_scores_argsort][
            : max_evidence
        ]
        for query, evidence_text in scored_evidences:
            top_evidences += mapping[evidence_text]
        self.logger.info(f"Total time for inference: {time.time() - start} seconds")

        return top_evidences
