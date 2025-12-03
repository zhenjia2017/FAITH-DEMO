import os
import sys
import json
import time
import copy
import logging


from faith.library.utils import get_config, get_logger, get_result_logger, store_json_with_mkdir
# tqu
from faith.temporal_qu.seq2seq_tqu_iques import Seq2SeqIQUESTQU
# fer
from faith.faithful_er.fer import FER
# ha
from faith.heterogeneous_answering.graph_neural_network.iterative_gnns import IterativeGNNs


class Pipeline:
    def __init__(self, config, benchmark, tqu = "seq2seq_tqu", fer="fer"):
        """Create the pipeline based on the config."""
        # load config
        self.config = config
        self.logger = get_logger(__name__, config)
        self.result_logger = get_result_logger(config)
        self.fer = self._load_fer(benchmark)
        # load individual modules
        self.tqu = self._load_tqu(benchmark)
        self.name = self.config["name"]
        self.benchmark = benchmark
        self.logger.info("Loading GNNs HA module")
        self.ha_gnn = IterativeGNNs(config, benchmark)
        loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
        print("Loggers", loggers)


    def inference_on_instance(self, instance, es_method, ha_method, sources):
        """Run pipeline on given instance."""
        start = time.time()
        self.tqu.inference_on_instance(instance, es_method, ha_method, sources)

        self.logger.info(f"Time taken (TQU): {time.time() - start} seconds")
        self.logger.info(f"Running FER")
        self.fer.inference_on_instance(instance, es_method, sources)

        self.logger.info(f"Time taken (TQU, FER): {time.time() - start} seconds")
        self.logger.info(f"Running HA")
        if ha_method == "explaignn":
            self.ha_gnn.inference_on_instance_demo(instance, sources)
    
        else:
            raise ValueError(f"Unknown HA method: {ha_method}")

        self.logger.info(f"Time taken (ALL): {time.time() - start} seconds")
        return instance


    def _load_tqu(self, benchmark):
        """Instantiate TQU stage of FAITH pipeline."""
        tqu = "seq2seq_tqu"
        self.logger.info("Loading TQU module")
        if tqu == "seq2seq_tqu":
            return Seq2SeqIQUESTQU(self.config, self, benchmark)
        else:
            raise ValueError(
                f"There is no available module for instantiating the TQU phase called {tqu}."
            )

    def _load_fer(self, benchmark):
        """Instantiate FER stage of FAITH pipeline."""
        self.logger.info("Loading FER module")
        fer = self.config["fer"]
        if fer == "fer":
            return FER(self.config, benchmark)
        else:
            raise ValueError(
                f"There is no available module for instantiating the ERS phase called {fer}."
            )

    
