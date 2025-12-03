import os
import json
import time
from pathlib import Path
from tqdm import tqdm
from faith.library.utils import get_config, get_logger
from faith.library.string_library import StringLibrary
from faith.evaluation import answer_presence


class FaithfulEvidenceRetrieval:
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__, self.config)
        self.tsf_delimiter = self.config["tsf_delimiter"]
        self.string_lib = StringLibrary(config)

    def inference_on_data(self, input_data, es_method, sources=["kb", "text", "table", "info"]):
        """Run model on data and add predictions."""
        # model inference on given data
        for instance in tqdm(input_data):
            self.inference_on_instance(instance, es_method, sources)
        return input_data

    def inference_on_instance(self, instance, es_method, sources=["kb", "text", "table", "info"]):
        """Retrieve candidate and prune for generating faithful evidences for TSF."""
        raise Exception("This is an abstract function which should be overwritten in a derived class!")


    def store_cache(self):
        """Store cache of evidence retriever."""
        raise Exception(
            "This is an abstract function which should be overwritten in a derived class!"
        )

    def evaluate_retrieval_results_res_stage(self, results_path, stage="initial",
                                             sources=['kb', 'info', 'table', 'text']):
        """
                Evaluate the results of the retrieval phase, for
                each source, and for each category.
                """
        # score
        if stage == "scoring":
            return self.evaluate_retrieval_results_res(results_path, sources=sources)

        if stage == "pruning" and self.faith_or_unfaith == "unfaith":
            return self.evaluate_retrieval_results_res(results_path, sources=sources)

        answer_presences = list()
        source_to_ans_pres = {source: 0 for source in sources}
        source_to_ans_pres.update({"all": 0})
        category_to_ans_pres = {"explicit": [], "ordinal": [], "implicit": [], "temp.ans": [], "all": []}

        total_source_num = {source: [] for source in sources}
        total_source_num.update({"all": []})

        with open(results_path, "r") as fp:
            data = json.load(fp)
            for instance in tqdm(data):
                source_to_evidence_num = {source: 0 for source in sources}
                category_slot = [item.lower() for item in instance["Temporal question type"]]

                for source in sources:
                    total_source_num[source].append(source_to_evidence_num[source])
                    total_source_num["all"].append(source_to_evidence_num[source])

                hit = instance[f"answer_presence_{stage}"]
                answer_presence_per_src = instance[f"answer_presence_per_src_{stage}"]

                category_to_ans_pres["all"] += [hit]

                for category in category_to_ans_pres.keys():
                    if category in category_slot:
                        category_to_ans_pres[category] += [hit]

                answer_presences += [hit]

                for src, ans_presence in answer_presence_per_src.items():
                    source_to_ans_pres[src] += ans_presence
                # aggregate overall answer presence for validation
                if len(answer_presence_per_src.items()):
                    source_to_ans_pres["all"] += 1

        # print results
        res_path = results_path.replace(".jsonl", f"-retrieval_{stage}.res")
        with open(res_path, "w") as fp:
            fp.write(f"evaluation result:\n")
            avg_answer_presence = sum(answer_presences) / len(answer_presences)
            fp.write(f"Avg. answer presence: {avg_answer_presence}\n")
            answer_presence_per_src = {
                src: (num / len(answer_presences)) for src, num in source_to_ans_pres.items()
            }
            fp.write(f"Answer presence per source: {answer_presence_per_src}")

            fp.write("\n")
            fp.write("\n")
            category_answer_presence_per_src = {
                category: (sum(num) / len(num)) for category, num in category_to_ans_pres.items() if len(num) != 0
            }
            fp.write(f"Category Answer presence per source: {category_answer_presence_per_src}")

    def evaluate_retrieval_results(self, results_path, sources=['kb', 'info', 'table', 'text']):
        """
        Evaluate the results of the retrieval phase, for
        each source, and for each category.
        """
        # score
        answer_presences = list()
        source_to_ans_pres = {source: 0 for source in sources}
        source_to_ans_pres.update({"all": 0})
        category_to_ans_pres = {"ordinal": [], "explicit": [], "implicit": [], "temp.ans": [], "all": []}
        category_to_evi_num = {"ordinal": [], "explicit": [], "implicit": [], "temp.ans": [], "all": []}

        total_source_num = {source: [] for source in sources}
        total_source_num.update({"all": []})

        # process data
        data_num = 0
        with open(results_path, 'r') as fp:
            for line in tqdm(fp):
                try:
                    instance = json.loads(line)
                    data_num += 1
                except:
                    print("error when loads line!")
                    continue
                candidate_evidences = instance["candidate_evidences"]
                source_to_evidence_num = {source: 0 for source in sources}
                category_slot = [item.lower() for item in instance["Temporal question type"]]
                for evidence in candidate_evidences:
                    source_to_evidence_num[evidence["source"]] += 1

                for source in sources:
                    total_source_num[source].append(source_to_evidence_num[source])
                    total_source_num["all"].append(source_to_evidence_num[source])

                hit, answering_evidences = answer_presence(candidate_evidences, instance["answers"])

                answer_presence_per_src = {
                    evidence["source"]: 1 for evidence in answering_evidences
                }

                category_to_ans_pres["all"] += [hit]
                category_to_evi_num["all"] += [len(candidate_evidences)]
                for category in category_to_ans_pres.keys():
                    if category in category_slot:
                        category_to_evi_num[category] += [len(candidate_evidences)]
                        category_to_ans_pres[category] += [hit]

                answer_presences += [hit]

                for src, ans_presence in answer_presence_per_src.items():
                    source_to_ans_pres[src] += ans_presence
                # aggregate overall answer presence for validation
                if len(answer_presence_per_src.items()):
                    source_to_ans_pres["all"] += 1

        # save results
        res_path = results_path.replace(".jsonl", ".res")
        with open(res_path, "w") as fp:

            fp.write(f"evaluation result: for instances of {data_num}\n")
            for source in total_source_num:
                fp.write(f"source: {source}\n")
                fp.write(f"Avg. evidence number: {sum(total_source_num[source]) / len(total_source_num[source])}\n")
                sorted_source_num = total_source_num[source]
                sorted_source_num.sort()
                fp.write(f"Max. evidence number: {sorted_source_num[-1]}\n")
                fp.write(f"Min. evidence number: {sorted_source_num[0]}\n")

            avg_answer_presence = sum(answer_presences) / len(answer_presences)
            fp.write(f"Avg. answer presence: {avg_answer_presence}\n")
            answer_presence_per_src = {
                src: (num / len(answer_presences)) for src, num in source_to_ans_pres.items()
            }
            fp.write(f"Answer presence per source: {answer_presence_per_src}")

            fp.write("\n")
            fp.write("\n")
            category_answer_presence_per_src = {
                category: (sum(num) / len(num)) for category, num in category_to_ans_pres.items() if len(num) != 0
            }
            fp.write(f"Category Answer presence per source: {category_answer_presence_per_src}")

            for category in category_to_evi_num:
                fp.write("\n")
                try:
                    fp.write(f"category: {category}\n")
                    fp.write(
                        f"Avg. evidence number: {sum(category_to_evi_num[category]) / len(category_to_evi_num[category])}\n")
                    sorted_category_num = category_to_evi_num[category]
                    sorted_category_num.sort()
                    fp.write(f"Max. evidence number: {sorted_category_num[-1]}\n")
                    fp.write(f"Min. evidence number: {sorted_category_num[0]}\n")
                except:
                    fp.write(f"category: {category} not in the corpus\n")
                    continue

    def evaluate_retrieval_results_res(self, results_path, sources=['kb', 'info', 'table', 'text']):
        """
                Evaluate the results of the retrieval phase, for
                each source, and for each category.
                """
        # score
        answer_presences = list()
        source_to_ans_pres = {source: 0 for source in sources}
        source_to_ans_pres.update({"all": 0})
        category_to_ans_pres = {"explicit": [], "ordinal": [], "implicit": [], "temp.ans": [], "all": []}
        category_to_evi_num = {"explicit": [], "ordinal": [], "implicit": [], "temp.ans": [], "all": []}

        total_source_num = {source: [] for source in sources}
        total_source_num.update({"all": []})

        with open(results_path, "r") as fp:
            data = json.load(fp)
            for instance in tqdm(data):
                candidate_evidences = instance["candidate_evidences"]
                source_to_evidence_num = {source: 0 for source in sources}
                if type(instance["Temporal question type"]) != list:
                    instance["Temporal question type"] = [instance["Temporal question type"]]
                category_slot = [item.lower() for item in instance["Temporal question type"]]
                # if "ordinal" in category_slot: continue
                for evidence in candidate_evidences:
                    source_to_evidence_num[evidence["source"]] += 1

                for source in sources:
                    total_source_num[source].append(source_to_evidence_num[source])
                    total_source_num["all"].append(source_to_evidence_num[source])

                hit, answering_evidences = answer_presence(candidate_evidences, instance["answers"])

                answer_presence_per_src = {
                    evidence["source"]: 1 for evidence in answering_evidences
                }

                category_to_ans_pres["all"] += [hit]
                category_to_evi_num["all"] += [len(candidate_evidences)]
                for category in category_to_ans_pres.keys():
                    if category in category_slot:
                        category_to_evi_num[category] += [len(candidate_evidences)]
                        category_to_ans_pres[category] += [hit]

                answer_presences += [hit]

                for src, ans_presence in answer_presence_per_src.items():
                    source_to_ans_pres[src] += ans_presence
                # aggregate overall answer presence for validation
                if len(answer_presence_per_src.items()):
                    source_to_ans_pres["all"] += 1

        # print results
        res_path = results_path.replace(".jsonl", "-retrieval.res")
        with open(res_path, "w") as fp:
            fp.write(f"evaluation result:\n")
            for source in total_source_num:
                fp.write(f"source: {source}\n")
                fp.write(f"Avg. evidence number: {sum(total_source_num[source]) / len(total_source_num[source])}\n")
                sorted_source_num = total_source_num[source]
                sorted_source_num.sort()
                fp.write(f"Max. evidence number: {sorted_source_num[-1]}\n")
                fp.write(f"Min. evidence number: {sorted_source_num[0]}\n")

            avg_answer_presence = sum(answer_presences) / len(answer_presences)
            fp.write(f"Avg. answer presence: {avg_answer_presence}\n")
            answer_presence_per_src = {
                src: (num / len(answer_presences)) for src, num in source_to_ans_pres.items()
            }
            fp.write(f"Answer presence per source: {answer_presence_per_src}")

            fp.write("\n")
            fp.write("\n")
            category_answer_presence_per_src = {
                category: (sum(num) / len(num)) for category, num in category_to_ans_pres.items() if len(num) != 0
            }
            fp.write(f"Category Answer presence per source: {category_answer_presence_per_src}")

            for category in category_to_evi_num:
                fp.write("\n")
                try:
                    fp.write(f"category: {category}\n")
                    fp.write(
                        f"Avg. evidence number: {sum(category_to_evi_num[category]) / len(category_to_evi_num[category])}\n")
                    sorted_category_num = category_to_evi_num[category]
                    sorted_category_num.sort()
                    fp.write(f"Max. evidence number: {sorted_category_num[-1]}\n")
                    fp.write(f"Min. evidence number: {sorted_category_num[0]}\n")
                except:
                    fp.write(f"category: {category} not in the corpus\n")
                    continue

    def evaluate_scoring_results(self, results_path, sources=['kb', 'info', 'table', 'text']):
        """
        Evaluate the results of the retrieval phase, for
        each source, and for each category.
        """
        # score
        answer_presences = list()
        source_to_ans_pres = {source: 0 for source in sources}
        source_to_ans_pres.update({"all": 0})
        category_to_ans_pres = {"explicit": [], "implicit": [], "temp.ans": [], "all": []}
        category_to_evi_num = {"explicit": [], "implicit": [], "temp.ans": [], "all": []}

        total_source_num = {source: [] for source in sources}
        total_source_num.update({"all": []})

        # process data
        with open(results_path, "r") as fp:
            data = json.load(fp)
            for instance in tqdm(data):
                candidate_evidences = instance["candidate_evidences"]
                source_to_evidence_num = {source: 0 for source in sources}
                category_slot = [item.lower() for item in instance["Temporal question type"]]
                if "ordinal" in category_slot: continue
                for evidence in candidate_evidences:
                    source_to_evidence_num[evidence["source"]] += 1

                for source in sources:
                    total_source_num[source].append(source_to_evidence_num[source])
                    total_source_num["all"].append(source_to_evidence_num[source])

                hit, answering_evidences = answer_presence(candidate_evidences, instance["answers"])

                answer_presence_per_src = {
                    evidence["source"]: 1 for evidence in answering_evidences
                }

                category_to_ans_pres["all"] += [hit]
                category_to_evi_num["all"] += [len(candidate_evidences)]
                for category in category_to_ans_pres.keys():
                    if category in category_slot:
                        category_to_evi_num[category] += [len(candidate_evidences)]
                        category_to_ans_pres[category] += [hit]

                answer_presences += [hit]

                for src, ans_presence in answer_presence_per_src.items():
                    source_to_ans_pres[src] += ans_presence
                # aggregate overall answer presence for validation
                if len(answer_presence_per_src.items()):
                    source_to_ans_pres["all"] += 1

        # print results
        res_path = results_path.replace(".jsonl", "-scoring-remove-ordinal.res")
        with open(res_path, "w") as fp:
            fp.write(f"evaluation result:\n")
            for source in total_source_num:
                fp.write(f"source: {source}\n")
                if len(total_source_num[source]) > 0:
                    fp.write(f"Avg. evidence number: {sum(total_source_num[source]) / len(total_source_num[source])}\n")
                    sorted_source_num = total_source_num[source]
                    sorted_source_num.sort()
                    fp.write(f"Max. evidence number: {sorted_source_num[-1]}\n")
                    fp.write(f"Min. evidence number: {sorted_source_num[0]}\n")

            avg_answer_presence = sum(answer_presences) / len(answer_presences)
            fp.write(f"Avg. answer presence: {avg_answer_presence}\n")
            answer_presence_per_src = {
                src: (num / len(answer_presences)) for src, num in source_to_ans_pres.items()
            }
            fp.write(f"Answer presence per source: {answer_presence_per_src}")

            fp.write("\n")
            fp.write("\n")
            category_answer_presence_per_src = {
                category: (sum(num) / len(num)) for category, num in category_to_ans_pres.items() if len(num) != 0
            }
            fp.write(f"Category Answer presence per source: {category_answer_presence_per_src}")

            for category in category_to_evi_num:
                fp.write(f"category: {category}\n")
                fp.write(
                    f"Avg. evidence number: {sum(category_to_evi_num[category]) / len(category_to_evi_num[category])}\n")
                sorted_category_num = category_to_evi_num[category]
                sorted_category_num.sort()
                fp.write(f"Max. evidence number: {sorted_category_num[-1]}\n")
                fp.write(f"Min. evidence number: {sorted_category_num[0]}\n")


