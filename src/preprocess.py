import re
import unicodedata
import html

# regex patterns
URL_RE = re.compile(r'https?://\S+|www\.\S+')
HTML_TAG_RE = re.compile(r'<[^>]+>')
MULTI_WS_RE = re.compile(r'\s+')

# keep only these punctuation marks (remove emojis and weird unicode)
BASIC_CHARS_RE = re.compile(r"[^0-9a-zA-Z\s\.\,\!\?\-\—\'\"]+")

def clean_text(text: str) -> str:
    """
    Clean text for safe processing:
    - Normalize unicode
    - Unescape HTML entities
    - Remove HTML tags
    - Remove URLs
    - Strip non-basic characters
    - Lowercase
    - Collapse whitespace
    """
    if not text:
        return ""

    # normalize unicode
    text = unicodedata.normalize("NFKC", str(text))

    # unescape & remove html tags
    text = html.unescape(text)
    text = HTML_TAG_RE.sub(" ", text)

    # remove URLs
    text = URL_RE.sub(" ", text)

    # remove emoji / non-basic chars (keep .,!? and quotes)
    text = BASIC_CHARS_RE.sub(" ", text)

    # lowercase
    text = text.lower()

    # collapse whitespace
    text = MULTI_WS_RE.sub(" ", text).strip()

    return text


def safe_shorten(text: str, max_chars: int = 1500) -> str:
    """
    Useful when sending long text to LLM.
    Truncates safely at word boundary.
    """
    if not text or len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    # avoid cutting in the middle of word
    last_space = cut.rfind(" ")
    if last_space != -1:
        cut = cut[:last_space]
    return cut + "..."


def extract_lead(text: str, sentences: int = 2) -> str:
    """
    Extract first 1-2 sentences (approx).
    Helps LLM focus on main claim.
    """
    if not text:
        return ""
    # naive sentence split
    parts = re.split(r'(?<=[.!?])\s+', text)
    return " ".join(parts[:sentences]).strip()