import re
from typing import List

import nltk
from nltk.tokenize import sent_tokenize

# Download tokenizer once (only if not already available)
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")


def clean_text(text: str) -> str:
    """
    Cleans extracted PDF text by normalizing whitespace.
    """

    # Remove extra spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def split_into_paragraphs(text: str) -> List[str]:
    """
    Splits text into paragraphs.
    """

    paragraphs = [
        paragraph.strip()
        for paragraph in text.split("\n\n")
        if paragraph.strip()
    ]

    return paragraphs


def split_into_sentences(paragraph: str) -> List[str]:
    """
    Splits a paragraph into sentences.
    """

    return sent_tokenize(paragraph)