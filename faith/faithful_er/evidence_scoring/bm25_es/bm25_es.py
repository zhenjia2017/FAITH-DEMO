import json

from rank_bm25 import BM25Okapi

class BM25Scoring:
    def __init__(self, config):
        with open(config["path_to_stopwords"], "r") as fp:
            self.stopwords = fp.read().split("\n")
        self.max_evidences = config["evs_max_evidences"]

    def get_top_evidences(self, structured_representation, evidences, max_evidences=None):
        """
        Retrieve the top-1000 evidences among the retrieved ones,
        for the given AR.
        """

        def _tokenize(string):
            """Function to tokenize string (word-level)."""
            string = string.replace(",", " ")
            string = string.strip()
            return [word.lower() for word in string.split() if not word in self.stopwords]

        def _get_evidence(tokenized_corpus, index, mapping, scores):
            evidence = mapping[" ".join(tokenized_corpus[index])]
            evidence["score"] = scores[index]
            return evidence

        if not evidences:
            return evidences

        if isinstance(structured_representation, dict):
            if "entity" in structured_representation and "relation" in structured_representation and "answer_type" in structured_representation:
                entity = structured_representation["entity"].strip()
                relation = structured_representation["relation"].strip()
                ans_type = structured_representation["answer_type"].strip()
                query = f"{entity} {relation} {ans_type}"
        else:
            query = structured_representation

        max_evs = max_evidences if max_evidences else self.max_evidences

        # tokenize
        mapping = {
            " ".join(_tokenize(evidence["evidence_text"])): evidence for evidence in evidences
        }
        tokenized_sr = _tokenize(query)

        # create corpus
        tokenized_corpus = [_tokenize(evidence["evidence_text"]) for evidence in evidences]
        bm25_module = BM25Okapi(tokenized_corpus)

        # scoring
        scores = bm25_module.get_scores(tokenized_sr)

        # retrieve top-k
        ranked_indices = sorted(
            range(len(tokenized_corpus)), key=lambda i: scores[i], reverse=True
        )[:max_evs]

        scored_evidences = [
            _get_evidence(tokenized_corpus, index, mapping, scores)
            for i, index in enumerate(ranked_indices)
        ]
        return scored_evidences
