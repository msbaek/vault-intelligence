#!/usr/bin/env python3
"""
Tests for Vault Intelligence Server

Note: These tests focus on API contract rather than search quality
because model loading is slow and not suitable for unit tests.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def test_vault(tmp_path):
    """Create a temporary test vault with sample documents"""
    vault_path = tmp_path / "test_vault"
    vault_path.mkdir()

    # Create test markdown files
    (vault_path / "test_doc1.md").write_text("""---
title: Test Document 1
tags: [test, python, programming]
---

# Test Document 1

This is a test document about Python programming.
Python is a versatile programming language.
It's great for data science and web development.
""", encoding='utf-8')

    (vault_path / "test_doc2.md").write_text("""---
title: Test Document 2
tags: [test, javascript, web]
---

# Test Document 2

This document discusses JavaScript and web development.
JavaScript is essential for modern web applications.
It runs in browsers and on servers with Node.js.
""", encoding='utf-8')

    (vault_path / "test_doc3.md").write_text("""---
title: Test Document 3
tags: [test, data-science, machine-learning]
---

# Test Document 3

Machine learning is transforming data science.
Deep learning models can solve complex problems.
Neural networks are the foundation of modern AI.
""", encoding='utf-8')

    return vault_path


@pytest.fixture
def test_data_dir(tmp_path):
    """Create temporary data directory with config"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create config directory
    config_dir = data_dir / "config"
    config_dir.mkdir()

    # Create cache directory
    cache_dir = data_dir / "cache"
    cache_dir.mkdir()

    # Create minimal settings.yaml
    settings = """
model:
  name: "BAAI/bge-m3"
  dimension: 1024
  batch_size: 2
  max_length: 512
  use_fp16: false
  num_workers: 1

search:
  default_top_k: 10
  similarity_threshold: 0.0
  enable_hybrid_search: true
  text_weight: 0.3
  semantic_weight: 0.7

vault:
  min_word_count: 5
"""

    (config_dir / "settings.yaml").write_text(settings, encoding='utf-8')

    return data_dir


@pytest.fixture
def mock_engine():
    """Create a mock search engine for testing"""
    from src.core.vault_processor import Document
    from src.features.advanced_search import SearchResult
    from datetime import datetime

    # Create mock documents
    mock_docs = [
        Document(
            path="test_doc1.md",
            title="Test Document 1",
            content="Python programming content",
            tags=["test", "python"],
            frontmatter={},
            word_count=20,
            char_count=100,
            file_size=500,
            modified_at=datetime.now(),
            file_hash="hash1"
        ),
        Document(
            path="test_doc2.md",
            title="Test Document 2",
            content="JavaScript web development",
            tags=["test", "javascript"],
            frontmatter={},
            word_count=25,
            char_count=120,
            file_size=600,
            modified_at=datetime.now(),
            file_hash="hash2"
        )
    ]

    # Create mock engine
    engine = Mock()
    engine.documents = mock_docs
    engine.indexed = True

    # Mock build_index to return success
    engine.build_index = Mock(return_value=True)

    # Mock search methods to return SearchResults
    def make_search_results(query, top_k=10, **kwargs):
        return [
            SearchResult(
                document=mock_docs[0],
                similarity_score=0.95,
                match_type="hybrid",
                snippet="Python programming content...",
                rank=1
            ),
            SearchResult(
                document=mock_docs[1],
                similarity_score=0.85,
                match_type="hybrid",
                snippet="JavaScript web development...",
                rank=2
            )
        ][:top_k]

    engine.hybrid_search = Mock(side_effect=make_search_results)
    engine.semantic_search = Mock(side_effect=make_search_results)
    engine.keyword_search = Mock(side_effect=make_search_results)
    engine.colbert_search = Mock(side_effect=make_search_results)
    engine.search_with_reranking = Mock(side_effect=make_search_results)

    return engine


@pytest.fixture
def client(test_vault, test_data_dir, mock_engine):
    """Create FastAPI test client with mocked engine"""
    # Set environment variables for test
    os.environ['VIS_VAULT_PATH'] = str(test_vault)
    os.environ['VIS_DATA_DIR'] = str(test_data_dir)

    # Import after setting env vars
    from src.server import create_app, _state

    # Patch the _init_engine function to return our mock
    with patch('src.server._init_engine', return_value=mock_engine):
        app = create_app()
        client = TestClient(app)

        # Set engine directly - indexed/document_count derived from engine
        _state["engine"] = mock_engine

        yield client

    # Cleanup
    if 'VIS_VAULT_PATH' in os.environ:
        del os.environ['VIS_VAULT_PATH']
    if 'VIS_DATA_DIR' in os.environ:
        del os.environ['VIS_DATA_DIR']


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "indexed" in data
    assert "document_count" in data
    assert isinstance(data["indexed"], bool)
    assert isinstance(data["document_count"], int)

    # After startup, should be indexed
    assert data["indexed"] is True
    assert data["document_count"] > 0


def test_search_returns_results(client):
    """Test search endpoint returns valid results"""
    response = client.get("/search", params={
        "query": "python programming",
        "top_k": 5,
        "search_method": "hybrid"
    })

    assert response.status_code == 200

    data = response.json()
    assert "results" in data
    assert "query" in data
    assert "search_method" in data
    assert "total" in data

    assert data["query"] == "python programming"
    assert data["search_method"] == "hybrid"
    assert isinstance(data["results"], list)
    assert isinstance(data["total"], int)

    # Should have results
    assert data["total"] >= 0

    # Check result structure if we have results
    if data["total"] > 0:
        result = data["results"][0]
        assert "path" in result
        assert "score" in result
        assert "title" in result
        assert "snippet" in result
        assert "rank" in result
        assert "match_type" in result


def test_search_with_different_methods(client):
    """Test different search methods"""
    methods = ["semantic", "keyword", "hybrid"]

    for method in methods:
        response = client.get("/search", params={
            "query": "test",
            "search_method": method,
            "top_k": 3
        })

        assert response.status_code == 200
        data = response.json()
        assert data["search_method"] == method


def test_search_with_threshold(client):
    """Test search with similarity threshold"""
    response = client.get("/search", params={
        "query": "python",
        "threshold": 0.5,
        "top_k": 10
    })

    assert response.status_code == 200
    data = response.json()

    # All results should have score >= threshold (or close due to floating point)
    for result in data["results"]:
        # Allow small floating point tolerance
        assert result["score"] >= 0.49


def test_search_without_index_fails_gracefully(client):
    """Test that search before indexing returns appropriate error"""
    # This test is tricky because lifespan builds index on startup
    # We can test invalid search method instead
    response = client.get("/search", params={
        "query": "test",
        "search_method": "invalid_method"
    })

    assert response.status_code == 400


def test_reindex_endpoint(client):
    """Test reindex endpoint"""
    response = client.post("/reindex", params={"force": False})

    assert response.status_code == 200

    data = response.json()
    assert "document_count" in data
    assert "message" in data
    assert isinstance(data["document_count"], int)
    assert data["document_count"] > 0


def test_reindex_with_force(client):
    """Test forced reindex"""
    response = client.post("/reindex", params={"force": True})

    assert response.status_code == 200

    data = response.json()
    assert data["document_count"] > 0
    assert "Successfully reindexed" in data["message"]


def test_search_top_k_parameter(client):
    """Test that top_k parameter limits results"""
    response = client.get("/search", params={
        "query": "test document",
        "top_k": 2,
        "search_method": "hybrid"
    })

    assert response.status_code == 200

    data = response.json()
    # Should return at most 2 results
    assert len(data["results"]) <= 2


def test_search_result_ranking(client):
    """Test that results are properly ranked"""
    response = client.get("/search", params={
        "query": "machine learning",
        "top_k": 5,
        "search_method": "semantic"
    })

    assert response.status_code == 200

    data = response.json()
    if data["total"] > 1:
        # Check that scores are in descending order
        scores = [r["score"] for r in data["results"]]
        assert scores == sorted(scores, reverse=True)

        # Check that ranks are sequential
        ranks = [r["rank"] for r in data["results"]]
        assert ranks == list(range(1, len(ranks) + 1))


def test_concurrent_searches(client):
    """Test that multiple searches can be handled"""
    queries = ["python", "javascript", "machine learning", "data science"]

    for query in queries:
        response = client.get("/search", params={
            "query": query,
            "top_k": 3
        })
        assert response.status_code == 200


def test_search_result_response_optional_fields():
    """SearchResultResponse는 snippet/match_type 없이도 직렬화 가능해야 한다."""
    from src.server import SearchResultResponse

    minimal = SearchResultResponse(path="ko/한글-문서.md", score=0.85, title="한글 문서", rank=1)
    payload = minimal.model_dump(exclude_none=True)

    assert "snippet" not in payload
    assert "match_type" not in payload
    assert payload["title"] == "한글 문서"
    assert payload["path"] == "ko/한글-문서.md"


def test_search_endpoint_include_index_excludes_snippet(client):
    """include=index 모드에서 snippet/match_type이 응답에서 제외되어야 한다."""
    response = client.get("/search", params={"query": "한글 검색", "include": "index"})

    assert response.status_code == 200
    body = response.json()
    assert body["results"], "검색 결과가 비어있음"
    for r in body["results"]:
        assert r.get("snippet") is None
        assert r.get("match_type") is None
        assert {"path", "score", "title", "rank"}.issubset(r.keys())


def test_search_endpoint_default_include_keeps_snippet(client):
    """include 미지정(기본값) 시 기존 동작 유지 — snippet 포함."""
    response = client.get("/search", params={"query": "python"})

    assert response.status_code == 200
    body = response.json()
    assert body["results"]
    assert body["results"][0].get("snippet") is not None


def test_search_endpoint_include_full_explicit(client):
    """include=full 명시 시에도 snippet 포함."""
    response = client.get("/search", params={"query": "python", "include": "full"})

    assert response.status_code == 200
    assert response.json()["results"][0].get("snippet") is not None


def test_search_endpoint_include_invalid_returns_422(client):
    """잘못된 include 값은 422 반환."""
    response = client.get("/search", params={"query": "x", "include": "garbage"})
    assert response.status_code == 422


def test_get_document_returns_full_content(client):
    """GET /document?path=...로 본문/title 반환."""
    response = client.get("/document", params={"path": "test_doc1.md"})

    assert response.status_code == 200
    body = response.json()
    assert body["path"] == "test_doc1.md"
    assert body["title"] == "Test Document 1"
    assert "Python" in body["content"]
    assert isinstance(body["frontmatter"], dict)
    assert "test" in body["tags"]


def test_get_document_not_found(client):
    """존재하지 않는 path는 404."""
    response = client.get("/document", params={"path": "does-not-exist.md"})
    assert response.status_code == 404


def test_get_document_503_when_not_indexed(client):
    """엔진 미초기화 시 503.

    Note: 현재 client fixture는 항상 mock_engine을 사용하므로
    직접 _state["engine"] = None을 설정해야 함.
    """
    from src.server import _state
    original = _state["engine"]
    _state["engine"] = None
    try:
        response = client.get("/document", params={"path": "test_doc1.md"})
        assert response.status_code == 503
    finally:
        _state["engine"] = original


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
