import os
import re
import requests
import spacy
import json
import time
import pickle
from pathlib import Path

from filelock import FileLock
from bs4 import BeautifulSoup
from urllib.parse import quote, unquote

# from library.utils import get_config, get_logger
# import library.wikipedia_library as wiki


from faith.library.utils import get_config, get_logger
import faith.library.wikipedia_library as wiki

from faith.faithful_er.evidence_retrieval.wikipedia_retriever.text_parser import (
    # api
    extract_text_snippets,
    # soup
    extract_clean_text_from_html, create_evidences_from_text,
)
from faith.faithful_er.evidence_retrieval.wikipedia_retriever.table_parser import (
    # api
    extract_wikipedia_tables, json_tables_to_evidences,
    # soup
    create_evidences_from_table, parse_table_rows, parse_table_headers, extract_tables_from_soup,
)
from faith.faithful_er.evidence_retrieval.wikipedia_retriever.infobox_parser import (
    InfoboxParser,
    infobox_to_evidences,
)
from faith.faithful_er.evidence_retrieval.wikipedia_retriever.evidence_annotator import (
    EvidenceAnnotator,
)


API_URL = "http://en.wikipedia.org/w/api.php"
PARAMS = {
    "prop": "extracts|revisions",
    "format": "json",
    "action": "query",
    "explaintext": "",
    "rvprop": "content",
}


LOCAL_URL = "http://localhost:60001/content/wikipedia_en_all_nopic_2024-06/A"

class WikipediaRetriever:
    def __init__(self, config, temporal_value_annotator):
        self.config = config
        self.logger = get_logger(__name__, config)

        # whether Wikipedia evidences are retrieved on the fly (i.e. from the Wikipedia API)
        self.use_cache = config["er_wikipedia_use_cache"]
        self.on_the_fly = config["er_on_the_fly"]
        # # initialize dump
        if self.use_cache:
            self.path_to_dump = os.path.join(config["path_to_data"], self.config["er_wikipedia_dump"])
            self._init_wikipedia_dump()
            self.dump_changed = False

        if self.on_the_fly:
            # open dicts
            with open(config["path_to_wikidata_mappings"], "rb") as fp:
                self.wikidata_mappings = pickle.load(fp)
            with open(config["path_to_wikipedia_mappings"], "rb") as fp:
                self.wikipedia_mappings = pickle.load(fp)

            # initialize evidence annotator (used for (text)->Wikipedia->Wikidata)
            self.annotator = EvidenceAnnotator(config, self.wikidata_mappings, temporal_value_annotator)

            # load nlp pipeline
            self.nlp = spacy.blank("en")
            self.nlp.add_pipe("sentencizer")
        self.logger.debug("WikipediaRetriever successfully initialized!")

    def retrieve_wp_evidences(self, question_entity):
        """
        Retrieve evidences from Wikipedia for the given Wikipedia title.
        Always returns the full set of evidences (text, table, infobox).
        Filtering is done via filter_evidences function.
        """
        question_entity_id = question_entity["id"]
        if self.use_cache and question_entity_id in self.wikipedia_dump:
            self.logger.debug(f"Found Wikipedia evidences in dump!")
            return self.wikipedia_dump.get(question_entity_id)

        if not self.on_the_fly:
            self.logger.debug(
                f"No Wikipedia evidences in dump, but on-the-fly retrieval not active!"
            )
            return []

        # get Wikipedia title
        wiki_path = self.wikipedia_mappings.get(question_entity_id)
        #print(wiki_path)
        if not wiki_path:
            # print(f"No Wikipedia link found for this Wikidata ID: {question_entity_id}.")
            self.logger.debug(
                f"No Wikipedia link found for this Wikidata ID: {question_entity_id}."
            )
            if self.use_cache:
                self.wikipedia_dump[question_entity_id] = []  # remember
            return []
        self.logger.debug(f"Retrieving Wikipedia evidences for: {wiki_path}.")
        self.dump_changed = True

        # retrieve Wikipedia soup
        wiki_title = wiki._wiki_path_to_title(wiki_path)
        #print(wiki_title)

        soup = self._retrieve_soup(wiki_title)
        #print(soup)

        if soup is None:
            print("No wikipedia page retrieved!!")
            if self.use_cache:
                self.wikipedia_dump[question_entity_id] = []  # remember
            return []


        # extract anchors
        doc_anchor_dict = self._build_document_anchor_dict(soup)

        # retrieve evidences (without change)
        infobox_evidences = self._retrieve_infobox_entries(wiki_title, soup, doc_anchor_dict)
        #print(infobox_evidences)

        # table by api
        #table_records_api = self._retrieve_table_records_api(wiki_title, wiki_md)
        # table by soup
        table_records = self._retrieve_table_records(soup)
        #print (table_records)

        # # Save as json
        # with open("table_api.json", "w", encoding="utf-8") as file:
        #     json.dump(table_records_api, file, ensure_ascii=False, indent=4)
        # with open("table.json", "w", encoding="utf-8") as file:
        #     json.dump(table_records, file, ensure_ascii=False, indent=4)

        # text by api
        #text_snippets_api = self._retrieve_text_snippets_api(wiki_title, wiki_md)
        # text by soup
        text_snippets = self._retrieve_text_snippets(soup)

        # # Save as json
        # with open("text_snippets_api.json", "w", encoding="utf-8") as file:
        #     json.dump(text_snippets_api, file, ensure_ascii=False, indent=4)
        # with open("text_snippets.json", "w", encoding="utf-8") as file:
        #     json.dump(text_snippets, file, ensure_ascii=False, indent=4)

        # prune e.g. too long evidences
        evidences = infobox_evidences + table_records + text_snippets
        

        # # add `retrieved_for_entity` information
        for evidence in evidences:
            question_entity["wikipedia_title"] = wiki_title
            question_entity["wikipedia_path"] = wiki._wiki_title_to_path(wiki_title) 
            evidence["retrieved_for_entity"] = [question_entity]
        ## add wikidata entities (for table and text)
        # evidences with no wikidata entities (except for the wiki_path) are dropped
        evidences = self.annotator.annotate_wikidata_entities(wiki_path, evidences, doc_anchor_dict)
        evidences = self.filter_and_clean_evidences(evidences)
        
        # # store result in dump
        if self.use_cache:
            self.wikipedia_dump[question_entity_id] = evidences

        self.logger.debug(f"Evidences successfully retrieved for {question_entity_id}.")
        return evidences

    def filter_and_clean_evidences(self, evidences):
        """
        Drop evidences which do not suffice specific
        criteria. E.g. such evidences could be too
        short, long, or contain too many symbols.
        """
        filtered_evidences = list()
        for evidence in evidences:
            evidence_text = evidence["evidence_text"]
            ## clean evidence
            evidence_text = self.clean_evidence(evidence_text)
            if evidence["tempinfo"]:
                evidence["evidence_text"] = evidence_text
                filtered_evidences.append(evidence)
                continue
            ## filter evidences
            # too short
            if len(evidence_text) < self.config["evr_min_evidence_length"]:
                continue
            # too long
            if len(evidence_text) > self.config["evr_max_evidence_length"]:
                continue
            # ratio of letters very low
            letters = sum(c.isalpha() for c in evidence_text)
            if letters < len(evidence_text) / 2:
                continue

            filtered_evidences.append(evidence)

        return filtered_evidences

    def clean_evidence(self, evidence_text):
        """Clean the given evidence text."""
        evidence_text = re.sub(r"\[[0-9]*\]", "", evidence_text)
        return evidence_text

    def _retrieve_infobox_entries(self, wiki_title, soup, doc_anchor_dict):
        """
        Retrieve infobox entries for the given Wikipedia entity.
        """
        # get infobox (only one infobox possible)

        infoboxes = soup.find_all("table", {"class": "infobox"})
        if not infoboxes:
            return []
        infobox = infoboxes[0]

        # parse infobox content
        p = InfoboxParser(doc_anchor_dict)
        infobox_html = str(infobox)
        p.feed(infobox_html)

        # transform parsed infobox to evidences
        infobox_parsed = p.tables[0]

        evidences = infobox_to_evidences(infobox_parsed, wiki_title)

        return evidences

    def _retrieve_table_records(self, soup):
        """
        Extract non-infobox tables from HTML soup and convert them to evidences.
        Only process tables with class containing 'wikitable', excluding those with 'infobox'.
        """
        tables = extract_tables_from_soup(soup)
        evidences = []

        for table in tables:
            headers = parse_table_headers(table)
            rows = parse_table_rows(table, headers)
            table_evidences = create_evidences_from_table(headers, rows)
            evidences.extend(table_evidences)

        return evidences

    def _retrieve_table_records_api(self, wiki_title, wiki_md):
        """
        Retrieve table records for the given Wikipedia entity.
        """
        # extract wikipedia tables
        tables = extract_wikipedia_tables(wiki_md)

        # extract evidences from tables
        evidences = json_tables_to_evidences(tables, wiki_title)
        return evidences

    def _retrieve_text_snippets(self, soup):
        """
        Extract clean text snippets from Wikipedia HTML soup, skipping irrelevant elements.
        """
        # Extract clean text blocks from HTML
        text_blocks = extract_clean_text_from_html(soup)

        # Generate evidence from the text blocks
        evidences = create_evidences_from_text(text_blocks, self.nlp)

        return evidences

    def _retrieve_text_snippets_api(self, wiki_title, wiki_md):
        """
        Retrieve text snippets for the given Wikidata entity.
        """
        evidences = extract_text_snippets(wiki_md, wiki_title, self.nlp)
        return evidences

    def _build_document_anchor_dict(self, soup):
        """
        Establishes a dictionary that maps from Wikipedia text
        to the Wikipedia entity (=link). Is used to map to
        Wikidata entities (via Wikipedia) later.
        Format: text -> Wikidata entity.
        """
        # prune navigation bar
        for div in soup.find_all("div", {"class": "navbox"}):
            div.decompose()

        # go through links
        anchor_dict = dict()
        # Use cache to avoid repeated requests
        checked_urls = dict()
        for tag in soup.find_all("a"):
            # anchor text
            text = tag.text.strip()
            if len(text) < 3:
                continue
            # duplicate anchor text (keep first)
            # -> later ones can be more specific/incorrect
            if anchor_dict.get(text):
                continue

            # wiki title (=entity)
            href = tag.attrs.get("href")
            # if not wiki.is_wikipedia_path(href):
            #     continue
            if not wiki.is_local_wikipedia_path(href, checked_urls):
                continue
            wiki_path = wiki.format_wiki_path(href)

            anchor_dict[text] = wiki_path
        return anchor_dict

    def safequote(self, string):
        """
        Try to UTF-8 encode and percent-quote string
        """
        if string is None:
            return
        try:
            return quote(string.encode("utf-8"))
        except UnicodeDecodeError:
            return quote(string)

    def parse(self, title, link):
        """
        Returns Mediawiki action=parse query string
        """
        endpoint = "/w/api.php"
        # API_URL
        qry = self.PARSE.substitute(
            WIKI="https://en.wikipedia.org", ENDPOINT=endpoint, PAGE=self.safequote(title)
        )

        return qry

    def _retrieve_soup(self, wiki_title):
        """
        Retrieve Wikipedia html for the given Wikipedia Title.
        """
        wiki_path = wiki._wiki_title_to_path(wiki_title)
        # link = f"https://en.wikipedia.org/wiki/{wiki_path}"
        link = f"{LOCAL_URL}/{wiki_path}"
        #print (link)
        try:
            page = requests.get(link)
            soup = BeautifulSoup(page.text, features="html.parser")
        except:
            return None
        return soup

    def _retrieve_markdown(self, wiki_title):
        """
        Retrieve the content of the given wikipedia title.
        """
        params = PARAMS.copy()
        params["titles"] = wiki_title
        try:
            # make request
            r = requests.get(API_URL, params=params)
            res = r.json()
            pages = res["query"]["pages"]
            page = list(pages.values())[0]
        except:
            return None
        return page

    def _init_wikipedia_dump(self):
        """
        Initialize the Wikipedia dump. The consists of a mapping
        from Wikidata IDs to Wikipedia evidences in the expected format.
        """
        if os.path.isfile(self.path_to_dump):
            # remember version read initially
            self.logger.info(f"Loading Wikipedia dump from path {self.path_to_dump}.")
            with FileLock(f"{self.path_to_dump}.lock"):
                self.dump_version = self._read_dump_version()
                self.logger.debug(self.dump_version)
                self.wikipedia_dump = self._read_dump()
            self.logger.info(f"Wikipedia dump successfully loaded.")
        else:
            self.logger.info(
                f"Could not find an existing Wikipedia dump at path {self.path_to_dump}."
            )
            self.logger.info("Populating Wikipedia dump from scratch!")
            self.wikipedia_dump = {}
            self._write_dump(self.wikipedia_dump)
            self._write_dump_version()

    def store_dump(self):
        """Store the Wikipedia dumo to disk."""
        if not self.use_cache:  # store only if Wikipedia dump in use
            return
        if not self.dump_changed:  # store only if Wikipedia dump  changed
            return
        # check if the Wikipedia dump  was updated by other processes
        if self._read_dump_version() == self.dump_version:
            # no updates: store and update version
            self.logger.info(f"Writing Wikipedia dump at path {self.path_to_dump}.")
            with FileLock(f"{self.path_to_dump}.lock"):
                self._write_dump(self.wikipedia_dump)
                self._write_dump_version()
        else:
            # update! read updated version and merge the dumps
            self.logger.info(f"Merging Wikipedia dump at path {self.path_to_dump}.")
            with FileLock(f"{self.path_to_dump}.lock"):
                # read updated version
                updated_dump = self._read_dump()
                # overwrite with changes in current process (most recent)
                updated_dump.update(self.wikipedia_dump)
                # store
                self._write_dump(updated_dump)
                self._write_dump_version()

    def _read_dump(self):
        """
        Read the current version of the dump.
        This can be different from the version used in this file,
        given that multiple processes may access it simultaneously.
        """
        # read file content from wikipedia dump shared across QU methods
        with open(self.path_to_dump, "rb") as fp:
            wikipedia_dump = pickle.load(fp)
        return wikipedia_dump

    def _write_dump(self, dump):
        """Store the dump."""
        dump_dir = os.path.dirname(self.path_to_dump)
        Path(dump_dir).mkdir(parents=True, exist_ok=True)
        with open(self.path_to_dump, "wb") as fp:
            pickle.dump(dump, fp)
        return dump

    def _read_dump_version(self):
        """Read the dump version (hashed timestamp of last update) from a dedicated file."""
        if not os.path.isfile(f"{self.path_to_dump}.version"):
            self._write_dump_version()
        with open(f"{self.path_to_dump}.version", "r") as fp:
            dump_version = fp.readline().strip()
        return dump_version

    def _write_dump_version(self):
        """Write the current dump version (hashed timestamp of current update)."""
        with open(f"{self.path_to_dump}.version", "w") as fp:
            version = str(time.time())
            fp.write(version)
        self.dump_version = version
        
        
import sys
from faith.library.string_library import StringLibrary
from faith.library.temporal_library import TemporalValueAnnotator

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise Exception("python faith/faithful_er/evidence_retrieval/wikipedia_retriever/wikipedia_retriever.py config/tiq/evaluate_soup_er.yml")

    # load config
    config_path = sys.argv[1]
    config = get_config(config_path)
    print(1)
    string_lib = StringLibrary(config)
    print(2)
    temporal_value_annotator = TemporalValueAnnotator(config, string_lib)
    print(3)
    retriever = WikipediaRetriever(config, temporal_value_annotator)
    print(4)
    question_entity = {"id": "Q11696"}
    question_entity_id = question_entity["id"]
    evidences = retriever.retrieve_wp_evidences(question_entity)
    file_name = f"{question_entity_id}.json"
    
    output_dir = "/JZ/FAITH/debug_outputs"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = os.path.join(output_dir, file_name)
    with open(output_path, "w") as fp:
        fp.write(json.dumps(evidences, indent=4))
