import os
import time
import logging
import traceback
import argparse

from flask import Flask, render_template, session, request, jsonify
from faith.evaluation import answer_presence
from faith.library.utils import get_config, get_logger, get_result_logger, store_json_with_mkdir
from faith.faith_backend import Pipeline


CONFIG_PATH = "./config/demo/evaluate.yml"
HOST = 'localhost'
PORT = 7899

# Set up logging
logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	handlers=[
		logging.FileHandler("faith_api.log"),
		logging.StreamHandler()
	]
)
logger = logging.getLogger("faith_api")


###################################################
#  FAITH class                                    #
###################################################
class FAITH:
	def __init__(self, config_path=None):
		""" Initialize pipeline for demo. """
		try:
			# Load configuration
			self.config_path = config_path or CONFIG_PATH
			logger.info(f"Loading configuration file: {self.config_path}")
			self.config = get_config(self.config_path)
			
			# Load modules
			logger.info("Initializing FAITH pipeline...")
			self.pipeline_timequestions = Pipeline(self.config, "timequestions")
			logger.info("FAITH pipeline for TimeQuestions initialization complete")
			self.pipeline_tiq = Pipeline(self.config, "tiq")
			logger.info("FAITH pipeline for TIQ initialization complete")
			
			
		except Exception as e:
			logger.error(f"Failed to initialize FAITH: {str(e)}")
			logger.error(traceback.format_exc())
			raise


	def inference(self, request_data):
		""" Run inference on request. """
		try:
			# Load data
			question = request_data["question"]
			sources_str = request_data["sources"]
			reference_time = request_data["reference_time"]
			
			faith_or_unfaith = request_data["faith_or_unfaith"] if "faith_or_unfaith" in request_data else "faith"  # faith, unfaith
      

			iteration = request_data["iteration"] if "iteration" in request_data else 1  # default 2
			gnn_max_output_evidences = request_data["gnn_max_output_evidences"] if "gnn_max_output_evidences" in request_data else [20] 

   			# benchmark option
			benchmark = request_data["benchmark"] if "benchmark" in request_data else "timequestions"  # timequestions, tiq
			# ha method option
			ha_method = request_data["ha_method"] if "ha_method" in request_data else "explaignn"  # explaignn, seq2seq_ha, rag, graph_rag
			# fer method option
			es_method = request_data["es_method"] if "es_method" in request_data else "ce"
  
			logger.info(f"Received question: {question}, sources: {sources_str}, benchmark: {benchmark}, ha_method: {ha_method}, es_method: {es_method}")
			
			#sources_str = "kb" or "text" or "kb_text", etc
			sources = sources_str.split("_") if sources_str else ["kb", "text", "table", "info"]
   			#logger.info(f"Received question: '{question}', sources: '{sources}'")
			# Reformat data
			user_instance = {
				"Id": 1,
				"Question creation date": reference_time,
				"Question": question,
				"faith_or_unfaith": faith_or_unfaith,
				"iteration": iteration,
				"gnn_max_output_evidences": gnn_max_output_evidences,
				"answers": []
			}

			logger.info(f"Starting to process question...{user_instance} with sources: {sources}, benchmark: {benchmark}, es_method: {es_method}, ha_method: {ha_method}")
   
			# Inference
			start_time = time.time()
			if benchmark == "timequestions":
				result = self.pipeline_timequestions.inference_on_instance(user_instance, es_method, ha_method, sources)
			else:
				result = self.pipeline_tiq.inference_on_instance(user_instance, es_method, ha_method, sources)
			elapsed_time = time.time() - start_time
			logger.info(f"Question processing complete, time taken: {elapsed_time:.2f} seconds")

			return result
			
		except Exception as e:
			logger.error(f"Error processing question: {str(e)}")
			logger.error(traceback.format_exc())
			# Return error information
			failure_answer = {
				"Id": 1,
				"Question": request_data.get("question", ""),
				"error": f"Error processing request: {str(e)}",
				"answers": [{"id": "error", "label": f"Error processing request, please check logs for details."}]
			}
			return failure_answer


###################################################
#  Instantiate objects                            #
###################################################
# Parse command line arguments
parser = argparse.ArgumentParser(description='Start FAITH API service')
parser.add_argument('--config', help='Configuration file path')
parser.add_argument('--host', default=HOST, help='Server host')
parser.add_argument('--port', type=int, default=PORT, help='Server port')
args = parser.parse_args()

# Create Flask application
app = Flask(__name__)
app.secret_key = os.urandom(32) # secret key to some random bytes

# Create demo
try:
	logger.info("Initializing FAITH instance...")
	faith = FAITH(config_path=args.config)
	logger.info("FAITH instance initialization complete")
except Exception as e:
	logger.error(f"Unable to initialize FAITH instance: {str(e)}")
	logger.error(traceback.format_exc())
	# Continue running, but service may not work properly
	faith = None


###################################################
#  Define endpoint(s)                             #
###################################################

@app.route("/answer", methods=['POST'])
def answer():
	try:
		if faith is None:
			return jsonify({"error": "FAITH instance not properly initialized, please check logs for details"}), 500
			
		reference_time = time.strftime("%Y-%m-%d", time.localtime())

        # default benchmark option, "timequestions" or "tiq"
		benchmark = "tiq"
		# default ha method option
		ha_method = "explaignn"  # explaignn, text_rag, graph_rag, seq2seq_ha
		# default fer method option
		es_method = "ce" # ce, bm25
  		# default temporal pruning
		faith_or_unfaith = "faith"  # faith, unfaith
    	# default iteration
		iteration = 1  # default 1
		gnn_max_output_evidences = [20, 5, 5]

		request_data = {
			"question": request.json['question'],
			"sources": request.json['sources'] if 'sources' in request.json else "kb_text_table_info",
			"reference_time": reference_time,
            "benchmark": request.json['benchmark'] if 'benchmark' in request.json else benchmark,
            "es_method": request.json['es_method'] if 'es_method' in request.json else es_method,
			"faith_or_unfaith": request.json['faith_or_unfaith'] if 'faith_or_unfaith' in request.json else faith_or_unfaith,
			"iteration": request.json['iteration'] if 'iteration' in request.json else iteration,
			"gnn_max_output_evidences": request.json['gnn_max_output_evidences'] if 'gnn_max_output_evidences' in request.json else gnn_max_output_evidences,
            "ha_method": request.json['ha_method'] if 'ha_method' in request.json else ha_method
		}
		logger.info(f"Received API request: {request_data}")
		
		# Run inference
		res = faith.inference(request_data)
		
		logger.info(f"Model response: {res}")
		
		return jsonify(res)

	except Exception as e:
		logger.error(f"Error processing API request: {str(e)}")
		logger.error(traceback.format_exc())
		return jsonify({"error": str(e), "status": "error"}), 500


###################################################
#  Start Flask Server                             #
###################################################
if __name__ == "__main__":
	app.run(host=args.host, port=args.port)

