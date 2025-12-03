import os
import sys

from ehtqa.library.utils import get_config, get_logger
from ehtqa.faithful_er.faithful_evidence_retrieval import FaithfulEvidenceRetrieval
from ehtqa.faithful_er.evidence_scoring.bm25_es import BM25Scoring
#from ehtqa.faithful_er.evidence_pruning.pruning import EvidencePruning

class ClocqBM25(FaithfulEvidenceRetrieval):
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__, config)

        #self.evp = EvidencePruning(config)
        #self.evs = BM25Scoring(config)

    def inference_on_turn(self, intance, sources=["kb", "text", "table", "info"]):
        """Retrieve best evidences for STF."""
        structured_representation = intance["structured_temporal_form"]
        evidences, _ = self.evr.retrieve_evidences(structured_representation, sources)
        #if self.config["evr_prune"]:
        #    evidences, _ = self.evp.prune_evidences(evidences, structured_representation, sources)
        #top_evidences = self.evs.get_top_evidences(structured_representation, evidences)
        intance["candidate_evidences"] = evidences
        #intance["top_evidences"] = top_evidences
        #return top_evidences

        return evidences

    def store_cache(self):
        """Store cache of evidence retriever."""
        self.evr.store_cache()


#######################################################################################################################
#######################################################################################################################
if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise Exception("python convinse/evidence_retrieval_scoring/clocq_bm25.py <PATH_TO_CONFIG>")

    # load config
    config_path = sys.argv[1]
    config = get_config(config_path)
    ers = ClocqBM25(config)

    # inference: add predictions to data
    input_dir = config["path_to_annotated"]
    output_dir = config["path_to_intermediate_results"]

    qu = config["qu"]
    method_name = config["name"]

    source_combinations = config["source_combinations"]

    for sources in source_combinations:
        sources_string = "_".join(sources)

        input_path = os.path.join(input_dir, qu, f"train_qu-{method_name}.json")
        if os.path.exists(input_path):
            output_path = os.path.join(
                output_dir, qu, "clocq_bm25", sources_string, f"train_ers-{method_name}.jsonl"
            )
            ers.inference_on_data_split(input_path, output_path, sources)

        input_path = os.path.join(input_dir, qu, f"dev_qu-{method_name}.json")
        if os.path.exists(input_path):
            output_path = os.path.join(
                output_dir, qu, "clocq_bm25", sources_string, f"dev_ers-{method_name}.jsonl"
            )
            ers.inference_on_data_split(input_path, output_path, sources)

        input_path = os.path.join(input_dir, qu, f"test_qu-{method_name}.json")
        output_path = os.path.join(output_dir, qu, "clocq_bm25", sources_string, f"test_ers-{method_name}.jsonl")
        ers.inference_on_data_split(input_path, output_path, sources)

    # store results in cache
    ers.store_cache()
