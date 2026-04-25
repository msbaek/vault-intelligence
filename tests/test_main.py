#!/usr/bin/env python3
"""Tests for CLI argument parsing."""
import pytest
import sys
from unittest.mock import patch


def test_search_titles_only_flag():
    """--titles-only 플래그 파싱."""
    from src.__main__ import _build_parser
    parser = _build_parser()
    args = parser.parse_args(["search", "한글 쿼리", "--titles-only"])
    assert args.titles_only is True
    assert args.full_content is False


def test_search_full_content_flag():
    """--full-content 플래그 파싱."""
    from src.__main__ import _build_parser
    parser = _build_parser()
    args = parser.parse_args(["search", "x", "--full-content"])
    assert args.full_content is True
    assert args.titles_only is False


def test_search_default_no_flags():
    """기본값: 두 플래그 모두 False."""
    from src.__main__ import _build_parser
    parser = _build_parser()
    args = parser.parse_args(["search", "x"])
    assert args.titles_only is False
    assert args.full_content is False


def test_search_titles_and_full_mutually_exclusive():
    """--titles-only와 --full-content는 동시 사용 불가."""
    from src.__main__ import _build_parser
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["search", "x", "--titles-only", "--full-content"])
