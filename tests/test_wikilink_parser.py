import pytest
from src.features.wikilink_parser import WikilinkParser


def test_extract_wikilinks_basic():
    content = "See [[Document A]] and [[Document B|별칭]]."
    parser = WikilinkParser("/fake/vault")
    links = parser.extract_from_content(content)
    assert links == ["Document A", "Document B"]


def test_extract_wikilinks_with_heading():
    content = "See [[Document A#heading]]."
    parser = WikilinkParser("/fake/vault")
    links = parser.extract_from_content(content)
    assert links == ["Document A"]


def test_extract_wikilinks_empty():
    content = "No links here."
    parser = WikilinkParser("/fake/vault")
    links = parser.extract_from_content(content)
    assert links == []
