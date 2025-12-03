import re

def _filter_noise_from_html(text):
    """
    Filter out unwanted elements like references, citations, and extra spaces.
    """
    text = re.sub(r"\[\d+\]", "", text)  # remove citation numbers
    text = re.sub(r"\[[a-zA-Z]+\]", "", text)  # remove links
    text = re.sub(r"\[citation needed\]", "", text, flags=re.IGNORECASE)  # remove citation needed
    text = re.sub(r"\s+", " ", text)  # collapse multiple spaces
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)  # remove space before punctuation
    text = re.sub(r"([.,;:!?])(?=\w)", r"\1 ", text)  # ensure space after punctuation
    return text.strip()

def extract_clean_text_from_html(soup):
    """
    Extract clean text from HTML soup, skipping irrelevant elements like infoboxes, TOC, etc.
    """
    if soup is None:
        return []

    content_div = soup.find("div", {"class": "mw-parser-output"})
    if not content_div:
        return []

    # Remove irrelevant elements: sup.reference, infoboxes, toc
    for tag in content_div.find_all(["sup", "table", "div"], recursive=True):
        if tag.name == "sup" and "reference" in tag.get("class", []):
            tag.decompose()
        elif tag.name == "table" and "infobox" in tag.get("class", []):
            tag.decompose()
        elif tag.name == "div" and ("infobox" in tag.get("class", []) or tag.get("id") == "toc"):
            tag.decompose()

    # Stop parsing after certain headings (e.g., References, Notes, etc.)
    stop_headings = ["references", "notes", "citations", "see also", "external links", "further reading"]
    for heading in content_div.find_all(["h2", "h3"]):
        if any(stop in heading.get_text(strip=True).lower() for stop in stop_headings):
            # Remove all content after this heading
            for sibling in heading.find_all_next():
                sibling.decompose()
            break

    # Collect the paragraphs and list items
    text_blocks = []
    for elem in content_div.find_all(["p", "li"], recursive=True):
        text = elem.get_text(" ", strip=True)
        if text and len(text) > 20:  # Only keep meaningful blocks
            text_blocks.append(text)

    return text_blocks

def create_evidences_from_text(text_blocks, nlp):
    """
    Process text blocks into sentences and convert them to evidence objects.
    """
    evidences = []
    for block in text_blocks:
        clean_block = _filter_noise_from_html(block)
        doc = nlp(clean_block)
        for sent in doc.sents:
            sentence_text = sent.text.strip()
            if sentence_text:
                evidences.append({
                    "evidence_text": sentence_text,
                    "source": "text",
                })
    return evidences


"""
Separate line, above are by soup, below are by api
--------------------------------------------------
"""

def extract_text_snippets(wiki_md, wiki_title, nlp):
    """
    Extract text snippets from the given
    markdown text.
    """
    if not wiki_md or not wiki_md.get("extract"):
        return []

    # load content
    content = wiki_md["extract"]
    # remove noise and load doc
    clean_content = _filter_noise(content)
    doc = nlp(clean_content)

    # split the given document into sentences
    evidences = list()
    for sent in doc.sents:
        # drop empty sentences
        if not sent.text.strip():
            continue

        # wiki_title will be prepended later to avoid noisy matches
        evidence_text = sent.text.strip()

        # create evidence object
        evidence = {
            # entities are added later by EvidenceAnnotator
            "evidence_text": evidence_text,
            "source": "text",
        }

        if evidence not in evidences:
            evidences.append(evidence)

    return evidences


def _filter_noise(wiki_content):
    """
    Filter headings and whitespaces from the document.
    """
    # remove sections
    content = wiki_content.split("== Citations ==")[0]
    content = wiki_content.split("== Footnotes ==")[0]
    content = wiki_content.split("== References ==")[0]
    content = wiki_content.split("== Further reading ==")[0]
    # clean text
    content = re.sub(r"==.*?==+", "", content)
    content = content.replace("\n", " ")
    while "  " in content:
        content = content.replace("  ", " ")
    return content
