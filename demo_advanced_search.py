#!/usr/bin/env python3
"""
고급 검색 기능 데모 스크립트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.features.advanced_search import AdvancedSearchEngine, SearchQuery
from src.core.sentence_transformer_engine import SentenceTransformerEngine
from src.core.embedding_cache import EmbeddingCache
from src.core.vault_processor import VaultProcessor
import yaml

def load_config():
    """설정 로딩"""
    config_path = project_root / "config" / "settings.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def demo_search_types():
    """다양한 검색 타입 데모"""
    print("🔍 고급 검색 기능 데모")
    print("=" * 50)
    
    # 설정 로딩
    config = load_config()
    
    # 검색 엔진 초기화
    vault_path = "/Users/msbaek/DocumentsLocal/msbaek_vault"
    cache_dir = str(project_root / "cache")
    
    engine = AdvancedSearchEngine(vault_path, cache_dir, config)
    
    if not engine.indexed:
        print("📚 인덱스가 없습니다. 기존 캐시를 로드합니다...")
        engine.load_index()
    
    # 1. 의미적 검색 (Semantic Search)
    print("\n1️⃣ 의미적 검색 (TF-IDF 기반)")
    print("-" * 30)
    query = "코드 품질 향상"
    results = engine.semantic_search(query, top_k=3, threshold=0.1)
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.document.title}")
        print(f"   경로: {result.document.path}")
        print(f"   유사도: {result.similarity_score:.4f}")
        print()
    
    # 2. 키워드 검색 (Keyword Search)
    print("\n2️⃣ 키워드 검색")
    print("-" * 30)
    query = "TDD 테스트"
    results = engine.keyword_search(query, top_k=3)
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.document.title}")
        print(f"   경로: {result.document.path}")
        print(f"   키워드 점수: {result.similarity_score:.2f}")
        print(f"   매칭 키워드: {result.matched_keywords}")
        print()
    
    # 3. 하이브리드 검색 (의미적 + 키워드)
    print("\n3️⃣ 하이브리드 검색 (추천)")
    print("-" * 30)
    query = "클린 코드 원칙"
    results = engine.hybrid_search(
        query, 
        top_k=3, 
        semantic_weight=0.7,  # 의미적 검색 가중치
        keyword_weight=0.3    # 키워드 검색 가중치
    )
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.document.title}")
        print(f"   경로: {result.document.path}")
        print(f"   통합 점수: {result.similarity_score:.4f}")
        print(f"   검색 타입: {result.match_type}")
        if result.matched_keywords:
            print(f"   키워드: {result.matched_keywords}")
        if result.snippet:
            print(f"   스니펫: {result.snippet[:80]}...")
        print()
    
    # 4. 고급 검색 (필터링 포함)
    print("\n4️⃣ 고급 검색 (필터링)")
    print("-" * 30)
    
    from datetime import datetime, timedelta
    
    # 복잡한 검색 쿼리 생성
    search_query = SearchQuery(
        text="아키텍처 설계",
        min_word_count=100,  # 최소 100단어 이상
        max_word_count=2000, # 최대 2000단어 이하
        exclude_paths=["ATTACHMENTS/", ".git/"]  # 특정 경로 제외
    )
    
    results = engine.advanced_search(search_query)
    
    print(f"필터링된 결과: {len(results)}개")
    for i, result in enumerate(results[:3], 1):
        print(f"{i}. {result.document.title}")
        print(f"   경로: {result.document.path}")
        print(f"   단어수: {result.document.word_count}")
        print(f"   점수: {result.similarity_score:.4f}")
        print()
    
    # 5. 검색 엔진 통계
    print("\n📊 검색 엔진 통계")
    print("-" * 30)
    stats = engine.get_search_statistics()
    print(f"인덱싱된 문서: {stats['indexed_documents']:,}개")
    print(f"임베딩 차원: {stats['embedding_dimension']}차원")
    print(f"모델: {stats['model_name']}")
    print(f"캐시 임베딩: {stats['cache_statistics']['total_embeddings']:,}개")
    print(f"Vault 크기: {stats['vault_statistics']['total_size_mb']:.1f}MB")

if __name__ == "__main__":
    demo_search_types()