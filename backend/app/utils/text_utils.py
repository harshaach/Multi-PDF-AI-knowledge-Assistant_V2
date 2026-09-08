import re
from collections import Counter
from typing import List

import nltk
from nltk.tokenize import sent_tokenize


for resource in ("tokenizers/punkt", "tokenizers/punkt_tab"):
    try:
        nltk.data.find(resource)
    except LookupError:
        nltk.download(resource.split("/")[-1])


def clean_text(text: str) -> str:
    """
    Cleans extracted PDF text by normalizing whitespace
    and removing common PDF extraction artifacts.
    """

    # Normalize tabs and repeated spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove standalone page numbers
    text = re.sub(
        r"(?m)^\s*\d+\s*$",
        "",
        text,
    )

    # Remove excessive blank lines created after cleanup
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def normalize_line(line: str) -> str:
    """
    Normalizes a line so it can be compared across PDF pages.
    """

    line = re.sub(r"[ \t]+", " ", line)

    return line.strip().lower()


def detect_repeated_lines(
    page_texts: List[str],
    minimum_occurrences: int = 3,
) -> set[str]:
    """
    Detects lines that repeatedly occur across PDF pages.

    Repeated lines are commonly PDF headers, footers,
    document titles, or navigation artifacts.

    Only non-empty lines are considered.
    """

    line_counter = Counter()

    for text in page_texts:

        # Count a line at most once per page
        page_lines = set()

        for line in text.splitlines():

            normalized = normalize_line(line)

            if normalized:
                page_lines.add(normalized)

        for line in page_lines:
            line_counter[line] += 1

    repeated_lines = {
        line
        for line, count in line_counter.items()
        if count >= minimum_occurrences
    }

    return repeated_lines


def remove_repeated_lines(
    text: str,
    repeated_lines: set[str],
) -> str:
    """
    Removes detected repeated PDF header/footer lines.
    """

    cleaned_lines = []

    for line in text.splitlines():

        normalized = normalize_line(line)

        if normalized in repeated_lines:
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


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
