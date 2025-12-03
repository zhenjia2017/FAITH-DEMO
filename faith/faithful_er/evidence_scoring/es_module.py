import time
import os
from faith.library.utils import get_logger
from faith.faithful_er.evidence_scoring.es_model import ESModel
from faith.faithful_er.faithful_evidence_retrieval import FaithfulEvidenceRetrieval

class ESModule(FaithfulEvidenceRetrieval):
    def __init__(self, config, benchmark):
        self.config = config
        self.benchmark = benchmark
        self.logger = get_logger(__name__, config)
        # create model
        self.bert_model_faith = ESModel(config, benchmark)
        self.bert_model_unfaith = ESModel(config, benchmark)
        self.model_loaded_faith = False
        self.model_loaded_unfaith = False
        
    def get_top_evidences(self, query, evidences, max_evidence, faith_or_unfaith):
        """Run inference on a single question."""
        # load Bert model (if required)
        print ("Faith or UnFaith:", faith_or_unfaith)
        print(self.model_loaded_faith, self.model_loaded_unfaith)
        if faith_or_unfaith == "faith":
            self._load_faith()
            top_evidences = self.bert_model_faith.inference_top_k(query, evidences, max_evidence)
        else:
            self._load_unfaith()
            top_evidences = self.bert_model_unfaith.inference_top_k(query, evidences, max_evidence)
        return top_evidences
    
    def _load_faith(self):
        """Load the bert_model."""
        if not self.model_loaded_faith:
            self.bert_model_faith.load("faith")
            self.model_loaded_faith = True
    
    def _load_unfaith(self):
        """Load the bert_model."""
        if not self.model_loaded_unfaith:
            self.bert_model_unfaith.load("unfaith")
            self.model_loaded_unfaith = True

    def _load(self, faith_or_unfaith):
        """Load the bert_model."""
        # only load if not already done so
        if faith_or_unfaith == "faith" and not self.model_loaded_faith:
            self.bert_model_faith.load("faith")
            self.model_loaded_faith = True
        elif faith_or_unfaith == "unfaith" and not self.model_loaded_unfaith:
            self.bert_model_unfaith.load("unfaith")
            self.model_loaded_unfaith = True
            
        