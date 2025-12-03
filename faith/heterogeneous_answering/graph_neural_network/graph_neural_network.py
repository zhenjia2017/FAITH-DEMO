import json
import numpy as np
import os
import time
import torch, gc
from pathlib import Path
from torch.utils.data import DataLoader
from tqdm import tqdm
import random

import faith.heterogeneous_answering.graph_neural_network.dataset_gnn as dataset
from faith.heterogeneous_answering.graph_neural_network.gnn_factory import GNNFactory
from faith.heterogeneous_answering.heterogeneous_answering import HeterogeneousAnswering
from faith.library.utils import get_logger

START_DATE = time.strftime("%y-%m-%d_%H-%M", time.localtime())
random_integer = random.randint(1, 1000)
torch.autograd.set_detect_anomaly(True)

class GNNModule(HeterogeneousAnswering):
    def __init__(self, config, benchmark, iteration=None):
        super(GNNModule, self).__init__(config)
        self.logger = (
            get_logger(f"{__name__}_{iteration}", config)
            if iteration
            else get_logger(__name__, config)
        )

        self.gnn = GNNFactory.get_gnn(config)
        total_params = sum(p.numel() for p in self.gnn.parameters() if p.requires_grad)
        self.logger.info(f"Initialized model with {total_params} parameters.")
        self.model_loaded_faith = False
        self.model_loaded_unfaith = False

        self.data_path = self.config["path_to_data"]
        self.benchmark = benchmark
        
        self.model_dir_faith = os.path.join(self.data_path, self.benchmark, "faith", self.config["gnn_model_dir"])
        self.model_dir_unfaith = os.path.join(self.data_path, self.benchmark, "unfaith", self.config["gnn_model_dir"])
        self.gnn_model_path_faith = os.path.join(self.model_dir_faith, self.config["gnn_model_file"])
        self.gnn_model_path_unfaith = os.path.join(self.model_dir_unfaith, self.config["gnn_model_file"])

        
    def inference_on_instances(self, turns, sources=("kb", "text", "table", "info"), train=False):
        """Run inference on a multiple turns."""
        self.logger.info("Running inference_on_instances function!")
        #self.load()

        with torch.no_grad(), tqdm(total=len(turns)) as p_bar:
            batch_size = self.config["gnn_eval_batch_size"]

            # run inference
            instances = dataset.DatasetGNN.prepare_turns(self.config, turns, train=False)
            start_index = 0

            while start_index < len(instances):
                end_index = min(start_index + batch_size, len(instances))
                batch_instances = instances[start_index:end_index]
                batch = dataset.collate_fn(batch_instances)
                # move data to gpu (if possible)
                GNNModule._move_to_cuda(batch)
                # run model
                output = self.gnn(batch, train=False)
                
                for i, _ in enumerate(batch_instances):
                    instance_index = start_index + i
                    turn = turns[instance_index]

                    # store
                    turn["ranked_answers"] = output["answer_predictions"][i]["ranked_answers"]

                    # add top-evidences within iterative GNN
                    if "gnn_max_output_evidences" in self.config:
                        print (self.config["gnn_max_output_evidences"])
                        top_evidences = output["evidence_predictions"][i]["top_evidences"]
                        scored_evidences = output["evidence_predictions"][i]["scored_evidences"]
                        # change the code to record the evidences in each turn
                        turn["scored_evidences"] = list(scored_evidences)
                        turn["top_evidences"] = list(top_evidences)
                        turn["candidate_evidences"] = list(top_evidences)
                    #else:
                    #    del turn["candidate_evidences"]

                    # obtain metrics
                    if "answers" in turn:  # e.g. for demo answers are not known
                        turn["p_at_1"] = output["qa_metrics"][i]["p_at_1"]
                        turn["mrr"] = output["qa_metrics"][i]["mrr"]
                        turn["h_at_5"] = output["qa_metrics"][i]["h_at_5"]
                        turn["answer_presence"] = output["qa_metrics"][i]["answer_presence"]

                    # delete other information
                    if "question_entities" in turn:
                        del turn["question_entities"]
                    if "silver_SR" in turn:
                        del turn["silver_SR"]
                    if "silver_relevant_turns" in turn:
                        del turn["silver_relevant_turns"]
                    if "silver_answering_evidences" in turn:
                        del turn["silver_answering_evidences"]
                    if "instance" in turn:
                        del turn["instance"]
                start_index += batch_size
                p_bar.update(batch_size)
        
        return turns

    def inference_on_instance(self, turn, sources=("kb", "text", "table", "info"), train=False):
        """Run inference on a single turn."""
        return self.inference_on_instances([turn], sources, train)[0]

    @staticmethod
    def _move_to_cuda(obj):
        if torch.cuda.is_available():
            for key, value in obj.items():
                if not type(obj[key]) is torch.Tensor:
                    continue
                obj[key] = obj[key].cuda()

    @staticmethod
    def _unload_model(model):
        del model
        gc.collect()
        torch.cuda.empty_cache()

    def load_faith(self):
        """Load the model."""
        self.gnn_model_path = self.gnn_model_path_faith
        print("Loading GNN model from:", self.gnn_model_path)
        if torch.cuda.is_available():
            self.gnn.load_state_dict(torch.load(self.gnn_model_path))
            #self.gnn.load_state_dict(torch.load(self.gnn_model_path), strict=False)
        else:
            self.gnn.load_state_dict(torch.load(self.gnn_model_path, map_location="cpu"))
        self.gnn.eval()
        self.model_loaded_faith = True
    
    def load_unfaith(self):
        self.gnn_model_path = self.gnn_model_path_unfaith
        print("Loading GNN model from:", self.gnn_model_path)
        if torch.cuda.is_available():
            self.gnn.load_state_dict(torch.load(self.gnn_model_path))
            #self.gnn.load_state_dict(torch.load(self.gnn_model_path), strict=False)
        else:
            self.gnn.load_state_dict(torch.load(self.gnn_model_path, map_location="cpu"))
        self.gnn.eval()
        self.model_loaded_unfaith = True
            
            
    def load(self):
        """Load the model."""
        if not self.model_loaded:
            print("Loading GNN model from:", self.gnn_model_path)
            if torch.cuda.is_available():
                self.gnn.load_state_dict(torch.load(self.gnn_model_path))
                #self.gnn.load_state_dict(torch.load(self.gnn_model_path), strict=False)
            else:
                self.gnn.load_state_dict(torch.load(self.gnn_model_path, map_location="cpu"))
            self.gnn.eval()
            self.model_loaded = True
        
