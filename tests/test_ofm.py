"""Tests for OFM utilities.

SSOT: ~/.claude/commands/obsidian/ofm-rules.md
Rule: wikilink is vault-relative path, no .md extension.
"""
import re
from datetime import datetime
from src.utils.ofm import to_wikilink, format_frontmatter_timestamp


VAULT = "/fake/vault"


# --- to_wikilink ---

def test_absolute_path_stripped_to_vault_relative():
    result = to_wikilink(f"{VAULT}/997-BOOKS/개발자로 살아남기.md", VAULT)
    assert result == "[[997-BOOKS/개발자로 살아남기]]"


def test_md_extension_removed():
    result = to_wikilink(f"{VAULT}/001-INBOX/TDD.md", VAULT)
    assert result == "[[001-INBOX/TDD]]"


def test_nested_directory():
    result = to_wikilink(f"{VAULT}/003-RESOURCES/oop/SOLID.md", VAULT)
    assert result == "[[003-RESOURCES/oop/SOLID]]"


def test_alias_appended():
    result = to_wikilink(f"{VAULT}/997-BOOKS/Clean Code.md", VAULT, alias="클린코드")
    assert result == "[[997-BOOKS/Clean Code|클린코드]]"


def test_already_vault_relative_with_extension():
    result = to_wikilink("001-INBOX/TDD.md", VAULT)
    assert result == "[[001-INBOX/TDD]]"


def test_no_extension_input():
    result = to_wikilink(f"{VAULT}/001-INBOX/TDD", VAULT)
    assert result == "[[001-INBOX/TDD]]"


def test_top_level_file():
    result = to_wikilink(f"{VAULT}/README.md", VAULT)
    assert result == "[[README]]"


# --- format_frontmatter_timestamp ---

def test_timestamp_fixed_datetime():
    dt = datetime(2026, 5, 21, 10, 30)
    assert format_frontmatter_timestamp(dt) == "2026-05-21 10:30"


def test_timestamp_no_arg_returns_string():
    ts = format_frontmatter_timestamp()
    assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", ts)


def test_timestamp_not_wikilink():
    ts = format_frontmatter_timestamp(datetime(2026, 5, 21, 10, 30))
    assert "[[" not in ts
    assert "]]" not in ts


def test_already_vault_relative_no_extension():
    result = to_wikilink("001-INBOX/TDD", VAULT)
    assert result == "[[001-INBOX/TDD]]"


def test_empty_alias_ignored():
    result = to_wikilink(f"{VAULT}/001-INBOX/TDD.md", VAULT, alias="")
    assert result == "[[001-INBOX/TDD]]"
