import copy
import json
import numpy as np
import os
import sys
import time
import torch
import random

from faith.heterogeneous_answering.graph_neural_network.graph_neural_network import GNNModule
from faith.heterogeneous_answering.heterogeneous_answering import HeterogeneousAnswering
from faith.library.utils import get_config, get_logger, store_json_with_mkdir

SEED = 7
START_DATE = time.strftime("%y-%m-%d_%H-%M", time.localtime())

gnn_inference_default = [{
            "gnn_encoder": "alternating_encoder_cross_SR",
            "gnn_add_entity_type": True,
            "gnn_model_file": "gnn-pruning-ignn-100-00-10.bin",
            "gnn_max_evidences": 100,
            "gnn_max_entities": 400,
            "gnn_max_output_evidences": 20},
                         
            {
            "gnn_encoder": "full_encoder_cross_SR",
            "gnn_add_entity_type": True,
            "gnn_model_file": "gnn-answering-ignn-100-05-05.bin",
            "gnn_max_evidences": 20,
            "gnn_max_entities": 80,
            "gnn_max_output_evidences": 5}]

            
class IterativeGNNs(HeterogeneousAnswering):
    def __init__(self, config, benchmark):
        super(IterativeGNNs, self).__init__(config)
        self.logger = get_logger(__name__, config)

        self.configs = []
        self.gnns = []
        self.gnn_inference_config = []
        self.model_loaded_faith = False
        self.model_loaded_unfaith = False
        self.benchmark = benchmark

        # reproducibility
        random_seed = SEED
        random.seed(random_seed)
        torch.manual_seed(random_seed)
        np.random.seed(random_seed)
        if not self.model_loaded_faith:
            self.load_faith_demo(gnn_inference_default)
            self.gnn_inference_config = copy.deepcopy(gnn_inference_default)
        

        self.logger.info(f"Config: {json.dumps(self.config, indent=4)}")

    def _prepare_config_for_iteration(self, config_at_i):
        """
        Construct a standard GNN config for the given iteration, from the multi GNN config.
        """
        config_for_iteration = self.config.copy()
        for key, value in config_at_i.items():
            config_for_iteration[key] = value
        return config_for_iteration


    def _prepare_config_for_iteration_demo(self, iteration, gnn_max_output_evidences):
        """
        Construct a standard GNN config for gnn_inference.
        """
        # if iteration is 0, only answering
        # if iteration is 1, graph reduce from 100 to a number A, greater than 5 and less than 100 + answering
        # if iteration is 2, graph reduce from 100 to a number A, greater than 5 and less than 100, then reduce from the number A to B,  greater than 5 and less than A, + answering 
        # if iteration is 3, graph reduce from 100 to a number A, greater than 5 and less than 100, then reduce from the number A to B,  greater than 5 and less than A, + answering
        gnn_inference = []
        if iteration == 0:
            gnn_inference.append({
            "gnn_encoder": "full_encoder_cross_SR",
            "gnn_add_entity_type": True,
            "gnn_model_file": "gnn-answering-ignn-100-05-05.bin",
            "gnn_max_evidences": 100,
            "gnn_max_entities": 400,
            "gnn_max_output_evidences": 5})
            
        elif iteration == 1:
            gnn_inference.append({
            "gnn_encoder": "alternating_encoder_cross_SR",
            "gnn_add_entity_type": True,
            "gnn_model_file": "gnn-pruning-ignn-100-00-10.bin",
            "gnn_max_evidences": 100,
            "gnn_max_entities": 400,
            "gnn_max_output_evidences": gnn_max_output_evidences[0]})
            
            gnn_inference.append({
            "gnn_encoder": "full_encoder_cross_SR",
            "gnn_add_entity_type": True,
            "gnn_model_file": "gnn-answering-ignn-100-05-05.bin",
            "gnn_max_evidences": gnn_max_output_evidences[0],
            "gnn_max_entities": gnn_max_output_evidences[0] * 4,
            "gnn_max_output_evidences": 5})
        
        elif iteration == 2:        
            gnn_inference.append({
            "gnn_encoder": "alternating_encoder_cross_SR",
            "gnn_add_entity_type": True,
            "gnn_model_file": "gnn-pruning-ignn-100-00-10.bin",
            "gnn_max_evidences": 100,
            "gnn_max_entities": 400,
            "gnn_max_output_evidences": gnn_max_output_evidences[0]})
            
            gnn_inference.append({
            "gnn_encoder": "alternating_encoder_cross_SR",
            "gnn_add_entity_type": True,
            "gnn_model_file": "gnn-pruning-ignn-100-00-10.bin",
            "gnn_max_evidences": gnn_max_output_evidences[0],
            "gnn_max_entities": gnn_max_output_evidences[0] * 4,
            "gnn_max_output_evidences": gnn_max_output_evidences[1]})
            
            gnn_inference.append({
            "gnn_encoder": "full_encoder_cross_SR",
            "gnn_add_entity_type": True,
            "gnn_model_file": "gnn-answering-ignn-100-05-05.bin",
            "gnn_max_evidences": gnn_max_output_evidences[1],
            "gnn_max_entities": gnn_max_output_evidences[1] * 4,
            "gnn_max_output_evidences": 5})
        
        elif iteration == 3:        
            gnn_inference.append({
            "gnn_encoder": "alternating_encoder_cross_SR",
            "gnn_add_entity_type": True,
            "gnn_model_file": "gnn-pruning-ignn-100-00-10.bin",
            "gnn_max_evidences": 100,
            "gnn_max_entities": 400,
            "gnn_max_output_evidences": gnn_max_output_evidences[0]})
            
            gnn_inference.append({
            "gnn_encoder": "alternating_encoder_cross_SR",
            "gnn_add_entity_type": True,
            "gnn_model_file": "gnn-pruning-ignn-100-00-10.bin",
            "gnn_max_evidences": gnn_max_output_evidences[0],
            "gnn_max_entities": gnn_max_output_evidences[0] * 4,
            "gnn_max_output_evidences": gnn_max_output_evidences[1]})
            
            gnn_inference.append({
            "gnn_encoder": "alternating_encoder_cross_SR",
            "gnn_add_entity_type": True,
            "gnn_model_file": "gnn-pruning-ignn-100-00-10.bin",
            "gnn_max_evidences": gnn_max_output_evidences[1],
            "gnn_max_entities": gnn_max_output_evidences[1] * 4,
            "gnn_max_output_evidences": gnn_max_output_evidences[2]})
            
            gnn_inference.append({
            "gnn_encoder": "full_encoder_cross_SR",
            "gnn_add_entity_type": True,
            "gnn_model_file": "gnn-answering-ignn-100-05-05.bin",
            "gnn_max_evidences": gnn_max_output_evidences[2],
            "gnn_max_entities": gnn_max_output_evidences[2] * 4,
            "gnn_max_output_evidences": 5})

        return gnn_inference
    
    
    def inference_on_instance_demo(self, instance, sources=("kb", "text", "table", "info"), train=False):

        gnn_inference = self._prepare_config_for_iteration_demo(instance["iteration"], instance["gnn_max_output_evidences"])
        print (gnn_inference)
        print (self.gnn_inference_config)
        
            
        if self.gnn_inference_config and gnn_inference != self.gnn_inference_config:
            for i in range(len(self.gnn_inference_config)):
                GNNModule._unload_model(self.gnns[i])

            self.model_loaded_faith = False
            self.model_loaded_unfaith = False
        
        self.gnn_inference_config = gnn_inference
                
        """Run inference on a single instance."""
        faith_or_unfaith = instance["faith_or_unfaith"]
        if faith_or_unfaith == "faith" and self.model_loaded_unfaith:
            self.model_loaded_unfaith = False
            for i in range(len(gnn_inference)):
                GNNModule._unload_model(self.gnns[i])
        
        elif faith_or_unfaith == "unfaith" and self.model_loaded_faith:
            self.model_loaded_faith = False
            for i in range(len(gnn_inference)):
                GNNModule._unload_model(self.gnns[i])
        
        if faith_or_unfaith == "faith" and not self.model_loaded_faith:
            self.load_faith_demo(gnn_inference)
            
        elif faith_or_unfaith == "unfaith" and not self.model_loaded_unfaith:
            self.load_unfaith_demo(gnn_inference)
        
        for i in range(len(gnn_inference)):
            self.gnns[i].inference_on_instance(instance)
            instance[f"iterative_{i}_scored_evidences"] = instance["scored_evidences"]
            instance[f"iterative_{i}_top_evidences"] = instance["candidate_evidences"]
            del instance["scored_evidences"]
        return instance
    

    def load_faith_demo(self, gnn_inference):
        """Load models."""
        # initialize and load GNNs
        if not self.model_loaded_faith:
            # initialize and load GNNs
            self.configs = [
                self._prepare_config_for_iteration(config_at_i)
                for config_at_i in gnn_inference
            ]
            self.gnns = [
                GNNModule(self.configs[i], self.benchmark, iteration=i + 1)
                for i in range(len(gnn_inference))
            ]
            for gnn in self.gnns:
                gnn.load_faith()

            # remember that model is loaded
            self.model_loaded_faith = True
        
    def load_unfaith_demo(self, gnn_inference):
        """Load models."""
        # initialize and load GNNs
        if not self.model_loaded_unfaith:
            # initialize and load GNNs
            self.configs = [
                self._prepare_config_for_iteration(config_at_i)
                for config_at_i in gnn_inference
            ]
            self.gnns = [
                GNNModule(self.configs[i], self.benchmark, iteration=i + 1)
                for i in range(len(gnn_inference))
            ]
            for gnn in self.gnns:
                gnn.load_unfaith()

            # remember that model is loaded
            self.model_loaded_unfaith = True
        
            
    def inference_on_instance(self, instance, sources=("kb", "text", "table", "info"), train=False):

        if not self.model_loaded:
            self.load()

        """Run inference on a single instance."""
        for i in range(len(self.config["gnn_inference"])):
            self.gnns[i].inference_on_instance(instance)
            instance[f"iterative_{i}_scored_evidences"] = instance["scored_evidences"]
            instance[f"iterative_{i}_top_evidences"] = instance["candidate_evidences"]
            del instance["scored_evidences"]
        return instance


    
    # def inference_on_instance(self, instance, sources=("kb", "text", "table", "info"), train=False):

    #     faith_or_unfaith = instance["faith_or_unfaith"]
    #     if faith_or_unfaith == "faith" and not self.model_loaded_faith:
    #         self.load("faith")

    #     """Run inference on a single instance."""
    #     for i in range(len(self.config["gnn_inference"])):
    #         self.gnns[i].inference_on_instance(instance)
    #         instance[f"iterative_{i}_scored_evidences"] = instance["scored_evidences"]
    #         instance[f"iterative_{i}_top_evidences"] = instance["candidate_evidences"]
    #         del instance["scored_evidences"]
    #     return instance


    # def get_supporting_evidences(self, turn):
    #     """
    #     Get the supporting evidences for the answer.
    #     This function overwrites the model-agnostic implementation in
    #     the HeterogeneousAnswering class. The (top) evidences used in the
    #     final GNN layer are used as supporting evidences.
    #     """
    #     return turn["candidate_evidences"]

    # def get_answering_evidences(self, turn, turn_idx, turns_before_iteration):
    #     """
    #     Get the neighboring evidences of the answer in the initial graph,
    #     i.e. the answering evidences.
    #     """
    #     num_explaining_evidences = self.config["ha_max_supporting_evidences"]
    #     top_evidences = turns_before_iteration[0][turn_idx]["candidate_evidences"]
    #     if not turn["ranked_answers"]:
    #         return []
    #     answer_entity = turn["ranked_answers"][0]["answer"]
    #     answering_evidences = [
    #         ev
    #         for ev in top_evidences
    #         if answer_entity["id"] in [item["id"] for item in ev["wikidata_entities"]]
    #     ]
    #     answering_evidences = sorted(answering_evidences, key=lambda j: j["score"], reverse=True)

    #     # pad evidences to same number
    #     evidences_captured = set([evidence["evidence_text"] for evidence in answering_evidences])
    #     if len(answering_evidences) < num_explaining_evidences:
    #         additional_evidences = sorted(top_evidences, key=lambda j: j["score"], reverse=True)
    #         for ev in additional_evidences:
    #             if len(answering_evidences) == num_explaining_evidences:
    #                 break
    #             if not ev["evidence_text"] in evidences_captured:
    #                 answering_evidences.append(ev)
    #                 evidences_captured.add(ev["evidence_text"])

    #     return answering_evidences
    
    
    

    def load(self, gnn_inference):
        """Load models."""
        if not self.model_loaded_faith:
            # initialize and load GNNs
            self.configs = [
                self._prepare_config_for_iteration(config_at_i)
                for config_at_i in gnn_inference
            ]
            self.gnns = [
                GNNModule(self.configs[i], self.benchmark, iteration=i + 1)
                for i in range(len(gnn_inference))
            ]
            for gnn in self.gnns:
                gnn.load("faith")

            # remember that model is loaded
            self.model_loaded_faith = True
            
        elif faith_or_unfaith == "unfaith" and not self.model_loaded_unfaith:
            # initialize and load GNNs
            self.configs = [
                self._prepare_config_for_iteration(config_at_i)
                for config_at_i in self.config["gnn_inference"]
            ]
            self.gnns = [
                GNNModule(self.configs[i], self.benchmark, iteration=i + 1)
                for i in range(len(self.config["gnn_inference"]))
            ]
            for gnn in self.gnns:
                gnn.load("unfaith")

            # remember that model is loaded
            self.model_loaded_unfaith = True


def main():
    if len(sys.argv) < 2:
        raise Exception(
            "python faith/heterogeneous_answering/graph_neural_network/iterative_gnns.py --<FUNCTION> <PATH_TO_CONFIG> [<SOURCES_STR>]"
        )

    function = sys.argv[1]
    config_path = sys.argv[2]
    sources_str = sys.argv[3] if len(sys.argv) > 3 else "kb_text_table_info"
    config = get_config(config_path)

    if function == "--train":
        # train
        gnn = IterativeGNNs(config)
        sources = sources_str.split("_")
        gnn.train(sources=sources)

    elif function == "--test":
        gnn = IterativeGNNs(config)
        sources = sources_str.split("_")
        gnn.test(sources=sources)

    elif function == "--inference":
        gnn = IterativeGNNs(config)
        sources = sources_str.split("_")
        gnn.inference(sources=sources)

    elif function == "--dev":
        gnn = IterativeGNNs(config)
        sources = sources_str.split("_")
        gnn.dev(sources=sources)


if __name__ == "__main__":
    main()
