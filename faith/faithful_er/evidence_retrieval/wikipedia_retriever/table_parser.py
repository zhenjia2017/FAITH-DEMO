import mwparserfromhell as mwp
import re
from wikitables import WikiTable
from wikitables.util import ftag

def normalize_commas(text):
    """Ensure commas are followed by a space."""
    return re.sub(r",(?=\S)", ", ", text)

def extract_tables_from_soup(soup):
    """
    Extract non-infobox tables from HTML soup and return them as a list of tables.
    Only processes tables with class 'wikitable', excluding those with 'infobox'.
    """
    if not soup:
        return []

    # Select only <table> elements with class 'wikitable' and not 'infobox'
    tables = [
        table for table in soup.find_all("table")
        if "wikitable" in table.get("class", []) and "infobox" not in table.get("class", [])
    ]
    return tables

def parse_table_headers(table):
    """
    Extract headers from a table. If headers are not present, generate default ones.
    """
    headers = []
    thead = table.find("thead")
    if thead:
        headers = [th.get_text(strip=True) for th in thead.find_all("th")]
    else:
        first_row = table.find("tr")
        if first_row:
            headers = [th.get_text(strip=True) for th in first_row.find_all(["th", "td"])]
    return headers

def parse_table_rows(table, headers):
    """
    Parse the rows of a table and return them as a list of rows, where each row is a list of cells.
    """
    rows = []
    for tr in table.find_all("tr")[1:]:
        cells = [normalize_commas(td.get_text(" ", strip=True)) for td in tr.find_all(["td", "th"])]
        if cells:
            # Pad cells to match headers length
            while len(cells) < len(headers):
                cells.append("")
            rows.append(cells)
    return rows

def create_evidences_from_table(headers, rows):
    """
    Convert rows of a table into evidence format.
    """
    evidences = []
    for row in rows:
        # Construct evidence text, keeping empty values
        evidence_text = ", ".join(f"{key} is {value}" for key, value in zip(headers, row))
        if evidence_text:
            evidences.append({"evidence_text": evidence_text, "source": "table"})
    return evidences


"""
Separate line, above are by soup, below are by api
--------------------------------------------------
"""


def json_tables_to_evidences(tables, wiki_title):
    """
    Convert the table parsed by wikitables-module to evidences.
    """
    evidences = list()
    # for each table in document
    for table in tables:
        # row-wise table processing
        for row in table.rows:
            # wiki_title will be prepended later to avoid noisy matches
            evidence_text = ", ".join([f"{key} is {value}" for key, value in row.items() if value])

            # create evidence
            evidence = {"evidence_text": evidence_text, "source": "table"}
            if evidence not in evidences:
                evidences.append(evidence)
    return evidences


def extract_wikipedia_tables(wiki_md):
    """
    Retrieve json-tables from the wikipedia page.
    """
    if not wiki_md or not wiki_md.get("revisions"):
        return []

    # load content
    content = wiki_md["revisions"][0]["*"]
    title = wiki_md["title"]

    # extract tables using wikitables-module
    try:
        tables = _import_tables(content, title)
    except:
        tables = []
    return tables


def _import_tables(content, title, lang="en"):
    """
    Extract tables from the given markdown content
    using the wikitables module and mwparser.
    """
    raw_tables = mwp.parse(content).filter_tags(matches=ftag("table"))

    def _table_gen():
        for idx, table in enumerate(raw_tables):
            name = "%s[%s]" % (title, idx)
            yield WikiTable(name, table)

    return list(_table_gen())
