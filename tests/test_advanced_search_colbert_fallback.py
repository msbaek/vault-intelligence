"""normalize_search_method 폴백 동작 테스트 (ColBERT 제거, 2026-08-13)"""
import logging
from src.features.advanced_search import normalize_search_method


def test_colbert_falls_back_to_hybrid():
    assert normalize_search_method("colbert") == "hybrid"


def test_colbert_fallback_logs_warning(caplog):
    with caplog.at_level(logging.WARNING, logger="src.features.advanced_search"):
        normalize_search_method("colbert")
    assert any("colbert" in record.message.lower() for record in caplog.records)


def test_other_methods_pass_through_unchanged():
    for method in ["semantic", "keyword", "hybrid"]:
        assert normalize_search_method(method) == method
