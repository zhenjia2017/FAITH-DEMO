import time
from collections import Counter
from faith.library.utils import get_logger
from faith.library.string_library import StringLibrary
from faith.faithful_er.evidence_retrieval.clocq_er import ClocqRetriever
from faith.faithful_er.evidence_pruning.pruning import EvidencePruning
from faith.faithful_er.faithful_evidence_retrieval import FaithfulEvidenceRetrieval
from faith.faithful_er.evidence_scoring.es_module import ESModule
from faith.faithful_er.evidence_scoring.bm25_es.bm25_es import BM25Scoring
from faith.library.temporal_library import TemporalValueAnnotator
from faith.evaluation import answer_presence


class FER(FaithfulEvidenceRetrieval):
    """
    Variant of the FER, which prunes and scores.
    """

    def __init__(self, config, benchmark):
        self.config = config
        self.logger = get_logger(__name__, config)
        self.string_lib = StringLibrary(config)
        self.temporal_value_annotator = TemporalValueAnnotator(config, self.string_lib)
        self.evr = ClocqRetriever(config, self.temporal_value_annotator)
        self.evp = EvidencePruning(config)
        self.evs_bm25 = BM25Scoring(config)
        self.evs_ce = ESModule(config, benchmark)
        self.max_evidence = self.config["evs_max_evidences"]

    def inference_on_instance(self, instance, es_method, sources=["kb", "text", "table", "info"]):
        """Retrieve candidate and prune for generating faithful evidences for TSF."""
        start = time.time()
        self.logger.debug(f"Running ER")
        tsf = instance["structured_temporal_form"]
        faith_or_unfaith = instance["faith_or_unfaith"]
        # tsf is a dictionary
        if isinstance(tsf, dict):
            if "entity" in tsf and "relation" in tsf and "answer_type" in tsf:
                entity = tsf["entity"].strip()
                relation = tsf["relation"].strip()
                answer_type = tsf["answer_type"].strip()
                # for keeping the consistency with the paper, we add answer type for retrieval
                query = f"{entity}{' '}{relation}{' '}{answer_type}"
        else:
            # when without TQU, the input is question itself
            query = tsf

        initial_evidences, question_entities = self.evr.retrieve_evidences(query, sources)
        instance["candidate_evidences"] = initial_evidences
        instance["initial_evidences_length"] = len(initial_evidences)
        instance["initial_evidences_source"] = dict(Counter(evidence["source"] for evidence in initial_evidences if evidence["source"] in sources))
        instance["question_entities"] = question_entities
        self.logger.debug(f"Time taken (ER): {time.time() - start} seconds")
        if "answers" not in instance:
            instance["answers"] = self.string_lib.format_answers(instance)
        initial_hit, initial_answering_evidences = answer_presence(initial_evidences, instance["answers"])
        instance["answer_presence_initial"] = initial_hit
        instance["answer_presence_per_src_initial"] = {
            evidence["source"]: 1 for evidence in initial_answering_evidences
        }

        if faith_or_unfaith == "faith":
            pruned_evidences = self.evp.pruning_evidences(tsf, initial_evidences, sources)
            pruned_hit, pruned_answering_evidences = answer_presence(pruned_evidences, instance["answers"])
            instance["answer_presence_pruning"] = pruned_hit
            instance["answer_presence_per_src_pruning"] = {
                evidence["source"]: 1 for evidence in pruned_answering_evidences
            }
            instance["candidate_evidences"] = pruned_evidences
            instance["pruned_evidences_length"] = len(pruned_evidences)
            instance["pruned_evidences_source"] = dict(Counter(evidence["source"] for evidence in pruned_evidences if evidence["source"] in sources))
        
        elif faith_or_unfaith == "unfaith":
            # do not prune, just copy the initial evidences
            instance["answer_presence_pruning"] = instance["answer_presence_initial"]
            instance["answer_presence_per_src_pruning"] = instance["answer_presence_per_src_initial"]
            instance["pruned_evidences_length"] = instance["initial_evidences_length"]
            instance["pruned_evidences_source"] = instance["initial_evidences_source"]
            
        self.logger.debug(f"Time taken (ER, EP): {time.time() - start} seconds")
        # store the evidences with faithful tag
        if es_method == "bm25":
            top_evidences = self.evs_bm25.get_top_evidences(query, instance["candidate_evidences"], self.max_evidence)
        else:
            top_evidences = self.evs_ce.get_top_evidences(query, instance["candidate_evidences"], self.max_evidence, faith_or_unfaith)
        instance["candidate_evidences"] = top_evidences
        instance["topk_evidences_length"] = len(top_evidences)
        instance["topk_evidences_source"] = dict(Counter(evidence["source"] for evidence in top_evidences if evidence["source"] in sources))
        hit, answering_evidences = answer_presence(top_evidences, instance["answers"])
        instance["answer_presence"] = hit
        instance["answer_presence_per_src"] = {
            evidence["source"]: 1 for evidence in answering_evidences
        }


    def store_cache(self):
        """Store cache of evidence retriever."""
        # We do not store cache of the TSFs
        # (because cache will become too large)
        # -> We still store the cache of the Wikipedia retriever
        self.evr.store_cache()
        self.evr.wiki_retriever.store_dump()
