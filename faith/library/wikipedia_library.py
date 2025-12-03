"""
Library for different string and path functions
for the Wikipedia retriever.
"""
import requests
import string

def format_wiki_path(value):
    """Reformat Wikipedia entity link."""
    return value.replace("/wiki/", "")


def is_wikipedia_path(value):
    """Check if the value is a Wikipedia entity."""
    if not value:
        return False
    elif not value.startswith("/wiki"):
        return False
    elif value.startswith("/wiki/File:"):
        return False
    elif "Category:" in value:
        return False
    elif "Special:" in value:
        return False
    return True


def is_local_wikipedia_path(value, checked_urls=None):
    """
    Check if a value is a valid local Wikipedia entity link
    by constructing the full URL and checking if it exists.

    Uses an optional cache dictionary (checked_urls) to avoid
    repeated HTTP requests for the same URL.
    """
    if not value:
        return False
    if value.startswith("http") or value.startswith("#"):
        return False
    if "File:" in value or "Category:" in value or "Special:" in value:
        return False

    first_letter = value[0].upper()
    if first_letter not in string.ascii_uppercase:
        return False

    base_url = "http://localhost:60001/raw/wikipedia_en_all_nopic_2024-06/content/A"
    full_url = f"{base_url}/{value}"

    if checked_urls is not None:
        if full_url in checked_urls:
            return checked_urls[full_url]

    try:
        response = requests.head(full_url, timeout=0.1)
        exists = response.status_code == 200
    except requests.RequestException:
        exists = False

    if checked_urls is not None:
        checked_urls[full_url] = exists

    return exists



def _wiki_title_to_path(wiki_title):
    wiki_path = wiki_title.replace(" ", "_")
    wiki_path = wiki_path.replace("'", "%27")
    wiki_path = wiki_path.replace("-", "_")
    return wiki_path


def _wiki_path_to_title(wiki_path):
    wiki_title = wiki_path.replace("_", " ")
    wiki_title = wiki_title.replace("%27", "'")
    wiki_title = wiki_title.replace("%20", " ")
    wiki_title = wiki_title.replace("%28", "(")
    wiki_title = wiki_title.replace("%29", ")")
    wiki_title = wiki_title.replace("%2C", ",")
    wiki_title = wiki_title.replace("%21", "!")
    wiki_title = wiki_title.replace("%24", "$")
    wiki_title = wiki_title.replace("%25", "%")
    return wiki_title
