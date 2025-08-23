#!/usr/bin/env python3
"""
Vault Intelligence System V2 - Main Entry Point

CLI 인터페이스와 초기화 스크립트
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from typing import Optional

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.core.sentence_transformer_engine import SentenceTransformerEngine
    from src.core.embedding_cache import EmbeddingCache
    from src.core.vault_processor import VaultProcessor
    from src.features.advanced_search import AdvancedSearchEngine, SearchQuery
    from src.features.duplicate_detector import DuplicateDetector
    from src.features.topic_collector import TopicCollector
    from src.features.topic_analyzer import TopicAnalyzer
    from src.features.semantic_tagger import SemanticTagger, TaggingResult
    from src.features.moc_generator import MOCGenerator
    import yaml
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"❌ 모듈 가져오기 실패: {e}")
    print("필수 의존성이 누락되었습니다.")
    DEPENDENCIES_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_config(config_path: str = None) -> dict:
    """설정 파일 로딩"""
    if config_path is None:
        config_path = project_root / "config" / "settings.yaml"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"설정 파일 로딩 완료: {config_path}")
        return config
    except Exception as e:
        logger.error(f"설정 파일 로딩 실패: {e}")
        return {}


def check_dependencies() -> bool:
    """필수 의존성 확인"""
    print("🔍 의존성 확인 중...")
    
    if not DEPENDENCIES_AVAILABLE:
        print("❌ 핵심 모듈을 가져올 수 없습니다.")
        return False
    
    missing_deps = []
    
    # 기타 필수 라이브러리 확인
    try:
        import numpy
        print(f"✅ NumPy: {numpy.__version__}")
    except ImportError:
        missing_deps.append("numpy")
    
    try:
        import sklearn
        print(f"✅ Scikit-learn: {sklearn.__version__}")
    except ImportError:
        missing_deps.append("scikit-learn")
    
    try:
        import yaml
        print(f"✅ PyYAML 사용 가능")
    except ImportError:
        missing_deps.append("pyyaml")
    
    if missing_deps:
        print(f"❌ 누락된 의존성: {', '.join(missing_deps)}")
        print("다음 명령어로 설치하세요:")
        print(f"pip install {' '.join(missing_deps)}")
        return False
    
    print("✅ 모든 의존성이 설치되었습니다!")
    return True


def initialize_system(vault_path: str, config: dict) -> bool:
    """시스템 초기화"""
    print("🚀 시스템 초기화 중...")
    
    try:
        # Vault 경로 확인
        vault_path = Path(vault_path)
        if not vault_path.exists():
            print(f"❌ Vault 경로가 존재하지 않습니다: {vault_path}")
            return False
        
        print(f"📁 Vault 경로: {vault_path}")
        
        # 캐시 디렉토리 생성
        cache_dir = project_root / "cache"
        cache_dir.mkdir(exist_ok=True)
        print(f"💾 캐시 디렉토리: {cache_dir}")
        
        # 모델 디렉토리 생성
        models_dir = project_root / "models"
        models_dir.mkdir(exist_ok=True)
        print(f"🤖 모델 디렉토리: {models_dir}")
        
        # Sentence Transformer 엔진 초기화 테스트
        print("🧠 Sentence Transformer 엔진 테스트 중...")
        engine = SentenceTransformerEngine(
            model_name=config.get('model', {}).get('name', 'paraphrase-multilingual-mpnet-base-v2'),
            cache_dir=str(models_dir),
            device=config.get('model', {}).get('device')
        )
        
        # TF-IDF 엔진의 경우 테스트 문서로 훈련 필요
        print("📚 TF-IDF 엔진 훈련 중...")
        test_docs = [
            "테스트 문서 1: TDD는 테스트 주도 개발입니다.",
            "테스트 문서 2: 리팩토링은 코드 개선 기법입니다.",
            "테스트 문서 3: 클린코드는 읽기 쉬운 코드를 의미합니다."
        ]
        engine.fit_documents(test_docs)
        
        # 테스트 임베딩 생성
        test_text = "테스트 임베딩 생성"
        test_embedding = engine.encode_text(test_text)
        print(f"✅ 테스트 임베딩 차원: {len(test_embedding)}")
        
        # 캐시 시스템 초기화
        print("💾 캐시 시스템 초기화 중...")
        cache = EmbeddingCache(str(cache_dir))
        cache_stats = cache.get_statistics()
        print(f"📊 캐시 통계: {cache_stats['total_embeddings']}개 임베딩")
        
        # Vault 프로세서 초기화
        print("📚 Vault 프로세서 초기화 중...")
        processor = VaultProcessor(
            str(vault_path),
            excluded_dirs=config.get('vault', {}).get('excluded_dirs'),
            file_extensions=config.get('vault', {}).get('file_extensions')
        )
        
        vault_stats = processor.get_vault_statistics()
        print(f"📈 Vault 통계: {vault_stats['total_files']}개 파일, "
              f"{vault_stats['total_size_mb']}MB")
        
        print("✅ 시스템 초기화 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 시스템 초기화 실패: {e}")
        logger.exception("초기화 중 상세 오류:")
        return False


def run_tests():
    """테스트 실행"""
    print("🧪 시스템 테스트 실행 중...")
    
    success_count = 0
    total_tests = 3
    
    # 엔진 테스트
    print("\n1️⃣ Sentence Transformer 엔진 테스트")
    try:
        from src.core.sentence_transformer_engine import test_engine
        if test_engine():
            success_count += 1
    except Exception as e:
        print(f"엔진 테스트 실패: {e}")
    
    # 캐시 테스트
    print("\n2️⃣ 임베딩 캐시 테스트")
    try:
        from src.core.embedding_cache import test_cache
        if test_cache():
            success_count += 1
    except Exception as e:
        print(f"캐시 테스트 실패: {e}")
    
    # 프로세서 테스트
    print("\n3️⃣ Vault 프로세서 테스트")
    try:
        from src.core.vault_processor import test_processor
        if test_processor():
            success_count += 1
    except Exception as e:
        print(f"프로세서 테스트 실패: {e}")
    
    print(f"\n📊 테스트 결과: {success_count}/{total_tests} 통과")
    return success_count == total_tests


def show_system_info():
    """시스템 정보 표시"""
    print("ℹ️ Vault Intelligence System V2")
    print("=" * 50)
    print(f"프로젝트 경로: {project_root}")
    print(f"Python 버전: {sys.version}")
    
    try:
        import torch
        device = "CUDA" if torch.cuda.is_available() else "CPU"
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device = "MPS (Metal)"
        print(f"PyTorch 장치: {device}")
        if torch.cuda.is_available():
            print(f"GPU 메모리: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
    except:
        print("PyTorch: 사용 불가")
    
    # 캐시 상태 확인
    try:
        from .core.embedding_cache import EmbeddingCache
        cache_dir = str(project_root / "cache")
        cache = EmbeddingCache(cache_dir)
        
        print("\n💾 캐시 상태:")
        stats = cache.get_statistics()
        print(f"- Dense 임베딩: {stats.get('total_embeddings', 0):,}개")
        
        colbert_stats = cache.get_colbert_statistics()
        print(f"- ColBERT 임베딩: {colbert_stats.get('total_colbert_embeddings', 0):,}개")
        print(f"- 캐시 DB 크기: {stats.get('db_size', 0) / (1024*1024):.1f}MB")
        
    except Exception as e:
        print(f"\n💾 캐시 상태: 확인 불가 ({e})")
    
    print("\n🎯 완료된 기능 (Phase 1-7):")
    print("- BGE-M3 기반 Dense + Sparse + ColBERT 검색")
    print("- Cross-encoder 재순위화 (BGE Reranker V2-M3)")
    print("- 쿼리 확장 (동의어 + HyDE)")
    print("- 중복 문서 감지 및 그룹화")
    print("- 주제별 클러스터링 및 분석")
    print("- 지식 그래프 및 관련 문서 추천")
    print("- 자동 태깅 시스템")
    print("- ColBERT 증분 캐싱 시스템 (신규!)")
    print()
    print("⚡ ColBERT 검색 명령어:")
    print("  python -m src reindex --with-colbert     # ColBERT 포함 인덱싱")
    print("  python -m src reindex --colbert-only     # ColBERT만 인덱싱")
    print("  python -m src search --query 'TDD' --search-method colbert")
    print()
    print("⚡ 기본 명령어:")
    print("  python -m src search --query 'TDD'")
    print("  python -m src collect --topic '리팩토링'")
    print("  python -m src duplicates")


def run_search(vault_path: str, query: str, top_k: int, threshold: float, config: dict, sample_size: Optional[int] = None, use_reranker: bool = False, search_method: str = "hybrid", use_expansion: bool = False, include_synonyms: bool = True, include_hyde: bool = True, use_centrality: bool = False, centrality_weight: float = 0.2):
    """검색 실행"""
    try:
        print(f"🔍 검색 시작: '{query}'")
        if sample_size:
            print(f"📊 샘플링 모드: {sample_size}개 문서만 처리")
        if use_reranker:
            print("🎯 재순위화 모드 활성화")
        if use_expansion:
            print("📝 쿼리 확장 모드 활성화")
            expand_features = []
            if include_synonyms:
                expand_features.append("동의어")
            if include_hyde:
                expand_features.append("HyDE")
            print(f"   확장 기능: {', '.join(expand_features)}")
        if use_centrality:
            print(f"🎯 중심성 부스팅 활성화 (가중치: {centrality_weight})")
        
        # 검색 엔진 초기화
        cache_dir = str(project_root / "cache")
        search_engine = AdvancedSearchEngine(vault_path, cache_dir, config)
        
        if not search_engine.indexed:
            print("📚 인덱스 구축 중...")
            if not search_engine.build_index(sample_size=sample_size):
                print("❌ 인덱스 구축 실패")
                return False
        
        # 검색 수행 (확장, 재순위화, 중심성 부스팅 옵션 포함)
        if use_centrality:
            # 중심성 부스팅 검색
            results = search_engine.search_with_centrality_boost(
                query=query,
                search_method=search_method,
                top_k=top_k,
                centrality_weight=centrality_weight,
                threshold=threshold
            )
        elif use_expansion:
            # 쿼리 확장을 포함한 검색
            results = search_engine.expanded_search(
                query=query,
                search_method=search_method,
                top_k=top_k,
                threshold=threshold,
                include_synonyms=include_synonyms,
                include_hyde=include_hyde
            )
        elif use_reranker:
            # 재순위화를 포함한 고급 검색
            results = search_engine.search_with_reranking(
                query=query, 
                search_method=search_method,
                initial_k=top_k * 3,  # 3배수 후보 검색
                final_k=top_k, 
                threshold=threshold,
                use_reranker=True
            )
        else:
            # 기존 검색 방법
            if search_method == "semantic":
                results = search_engine.semantic_search(query, top_k=top_k, threshold=threshold)
            elif search_method == "keyword":
                results = search_engine.keyword_search(query, top_k=top_k)
            elif search_method == "colbert":
                results = search_engine.colbert_search(query, top_k=top_k, threshold=threshold)
            else:  # hybrid
                results = search_engine.hybrid_search(query, top_k=top_k, threshold=threshold)
        
        if not results:
            print("❌ 검색 결과가 없습니다.")
            return False
        
        print(f"\n📄 검색 결과 ({len(results)}개):")
        print("-" * 80)
        
        for result in results:
            print(f"{result.rank}. {result.document.title}")
            print(f"   경로: {result.document.path}")
            print(f"   유사도: {result.similarity_score:.4f}")
            print(f"   타입: {result.match_type}")
            if result.matched_keywords:
                print(f"   키워드: {', '.join(result.matched_keywords)}")
            if result.snippet:
                print(f"   내용: {result.snippet[:100]}...")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ 검색 실패: {e}")
        return False


def run_duplicate_detection(vault_path: str, config: dict):
    """중복 문서 감지 실행"""
    try:
        print("🔍 중복 문서 감지 시작...")
        
        # 검색 엔진 초기화
        cache_dir = str(project_root / "cache")
        search_engine = AdvancedSearchEngine(vault_path, cache_dir, config)
        
        if not search_engine.indexed:
            print("📚 인덱스 구축 중...")
            if not search_engine.build_index():
                print("❌ 인덱스 구축 실패")
                return False
        
        # 중복 감지기 초기화
        detector = DuplicateDetector(search_engine, config)
        
        # 중복 분석 수행
        analysis = detector.find_duplicates()
        
        print(f"\n📊 중복 분석 결과:")
        print("-" * 50)
        print(f"전체 문서: {analysis.total_documents}개")
        print(f"중복 그룹: {analysis.get_group_count()}개")
        print(f"중복 문서: {analysis.duplicate_count}개")
        print(f"고유 문서: {analysis.unique_count}개")
        print(f"중복 비율: {analysis.get_duplicate_ratio():.1%}")
        
        if analysis.duplicate_groups:
            print(f"\n📋 중복 그룹 상세:")
            for group in analysis.duplicate_groups[:5]:  # 상위 5개만 표시
                print(f"\n그룹 {group.id}:")
                print(f"  문서 수: {group.get_document_count()}개")
                print(f"  평균 유사도: {group.average_similarity:.4f}")
                for doc in group.documents:
                    print(f"    - {doc.path} ({doc.word_count}단어)")
        
        return True
        
    except Exception as e:
        print(f"❌ 중복 감지 실패: {e}")
        return False


def run_topic_collection(vault_path: str, topic: str, top_k: int, threshold: float, output_file: str, config: dict, use_expansion: bool = False, include_synonyms: bool = True, include_hyde: bool = True):
    """주제별 문서 수집 실행"""
    try:
        print(f"📚 주제 '{topic}' 문서 수집 시작...")
        if use_expansion:
            expand_features = []
            if include_synonyms:
                expand_features.append("동의어")
            if include_hyde:
                expand_features.append("HyDE")
            print(f"📝 쿼리 확장 모드 활성화: {', '.join(expand_features)}")
        
        # 검색 엔진 초기화
        cache_dir = str(project_root / "cache")
        search_engine = AdvancedSearchEngine(vault_path, cache_dir, config)
        
        if not search_engine.indexed:
            print("📚 인덱스 구축 중...")
            if not search_engine.build_index():
                print("❌ 인덱스 구축 실패")
                return False
        
        # 주제 수집기 초기화
        collector = TopicCollector(search_engine, config)
        
        # 주제별 문서 수집
        collection = collector.collect_topic(
            topic=topic,
            top_k=top_k,
            threshold=threshold,
            output_file=output_file,
            use_expansion=use_expansion,
            include_synonyms=include_synonyms,
            include_hyde=include_hyde
        )
        
        print(f"\n📊 수집 결과:")
        print("-" * 50)
        print(f"주제: {collection.metadata.topic}")
        print(f"수집 문서: {collection.metadata.total_documents}개")
        print(f"총 단어수: {collection.metadata.total_word_count:,}개")
        print(f"총 크기: {collection.metadata.total_size_bytes / 1024:.1f}KB")
        
        if collection.metadata.tag_distribution:
            print(f"\n🏷️ 태그 분포:")
            for tag, count in sorted(collection.metadata.tag_distribution.items(), 
                                   key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {tag}: {count}개")
        
        if collection.metadata.directory_distribution:
            print(f"\n📁 디렉토리 분포:")
            for dir_path, count in sorted(collection.metadata.directory_distribution.items(), 
                                       key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {dir_path}: {count}개")
        
        if output_file:
            print(f"\n💾 결과가 {output_file}에 저장되었습니다.")
        
        return True
        
    except Exception as e:
        print(f"❌ 주제 수집 실패: {e}")
        return False


def run_topic_analysis(vault_path: str, output_file: str, config: dict):
    """주제 분석 실행"""
    try:
        print("🔍 주제 분석 시작...")
        
        # 검색 엔진 초기화
        cache_dir = str(project_root / "cache")
        search_engine = AdvancedSearchEngine(vault_path, cache_dir, config)
        
        if not search_engine.indexed:
            print("📚 인덱스 구축 중...")
            if not search_engine.build_index():
                print("❌ 인덱스 구축 실패")
                return False
        
        # 주제 분석기 초기화
        analyzer = TopicAnalyzer(search_engine, config)
        
        # 주제 분석 수행 (새로운 주제 기반 방식 사용)
        print("🎯 주제 기반 분석을 시작합니다...")
        analysis = analyzer.analyze_topics_by_predefined_subjects(min_docs_per_topic=5)
        
        print(f"\n📊 주제 분석 결과:")
        print("-" * 50)
        print(f"분석 문서: {analysis.total_documents}개")
        print(f"발견 클러스터: {analysis.get_cluster_count()}개")
        print(f"클러스터링 방법: {analysis.algorithm}")
        if analysis.silhouette_score is not None:
            print(f"실루엣 점수: {analysis.silhouette_score:.3f}")
        
        if analysis.clusters:
            print(f"\n🏷️ 주요 클러스터들:")
            for i, cluster in enumerate(analysis.clusters[:10]):  # 상위 10개만 표시
                print(f"\n클러스터 {i+1}: {cluster.label}")
                print(f"  문서 수: {cluster.get_document_count()}개")
                print(f"  주요 키워드: {', '.join(cluster.keywords[:5]) if cluster.keywords else '없음'}")
                if cluster.coherence_score is not None:
                    print(f"  일관성 점수: {cluster.coherence_score:.3f}")
                if cluster.representative_doc:
                    print(f"  대표 문서: {cluster.representative_doc.title[:50]}")
        
        # 결과를 파일로 저장 (옵션)
        if output_file:
            # 파일 확장자에 따라 다른 형식으로 저장
            if output_file.lower().endswith('.md'):
                if analyzer.export_markdown_report(analysis, output_file):
                    print(f"\n💾 마크다운 보고서가 {output_file}에 저장되었습니다.")
                else:
                    print(f"\n❌ 마크다운 보고서 저장 실패: {output_file}")
            else:
                if analyzer.export_analysis(analysis, output_file):
                    print(f"\n💾 JSON 분석 결과가 {output_file}에 저장되었습니다.")
                else:
                    print(f"\n❌ 분석 결과 저장 실패: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ 주제 분석 실패: {e}")
        return False


def run_related_documents(vault_path: str, file_path: str, top_k: int, config: dict, 
                         include_centrality: bool = True, similarity_threshold: float = 0.3):
    """관련 문서 추천 실행"""
    try:
        print(f"🔗 '{file_path}' 관련 문서 찾기...")
        
        # 검색 엔진 초기화
        cache_dir = str(project_root / "cache")
        search_engine = AdvancedSearchEngine(vault_path, cache_dir, config)
        
        if not search_engine.indexed:
            print("📚 인덱스 구축 중...")
            if not search_engine.build_index():
                print("❌ 인덱스 구축 실패")
                return False
        
        # 관련 문서 찾기
        related_results = search_engine.get_related_documents(
            document_path=file_path,
            top_k=top_k,
            include_centrality_boost=include_centrality,
            similarity_threshold=similarity_threshold
        )
        
        if not related_results:
            print("❌ 관련 문서를 찾을 수 없습니다.")
            return False
        
        print(f"\n📄 관련 문서 ({len(related_results)}개):")
        print("-" * 80)
        
        for result in related_results:
            print(f"{result.rank}. {result.document.title}")
            print(f"   경로: {result.document.path}")
            print(f"   관련도: {result.similarity_score:.4f}")
            print(f"   타입: {result.match_type}")
            if result.document.tags:
                print(f"   태그: {', '.join(result.document.tags)}")
            if result.snippet:
                print(f"   내용: {result.snippet[:100]}...")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ 관련 문서 찾기 실패: {e}")
        return False


def run_knowledge_gap_analysis(vault_path: str, config: dict, output_file: str = None,
                              similarity_threshold: float = 0.3, min_connections: int = 2):
    """지식 공백 분석 실행"""
    try:
        print("🔍 지식 공백 분석 시작...")
        
        # 검색 엔진 초기화
        cache_dir = str(project_root / "cache")
        search_engine = AdvancedSearchEngine(vault_path, cache_dir, config)
        
        if not search_engine.indexed:
            print("📚 인덱스 구축 중...")
            if not search_engine.build_index():
                print("❌ 인덱스 구축 실패")
                return False
        
        # 지식 공백 분석 수행
        analysis = search_engine.analyze_knowledge_gaps(
            similarity_threshold=similarity_threshold,
            min_connections=min_connections
        )
        
        if not analysis:
            print("❌ 분석 결과가 없습니다.")
            return False
        
        summary = analysis.get('summary', {})
        
        print(f"\n📊 지식 공백 분석 결과:")
        print("-" * 50)
        print(f"전체 문서: {summary.get('total_documents', 0)}개")
        print(f"고립 문서: {summary.get('isolated_count', 0)}개")
        print(f"약한 연결 문서: {summary.get('weakly_connected_count', 0)}개")
        print(f"고립 태그: {summary.get('isolated_tag_count', 0)}개")
        print(f"고립률: {summary.get('isolation_rate', 0):.1%}")
        
        # 고립된 문서들 상세 정보
        isolated_docs = analysis.get('isolated_documents', [])
        if isolated_docs:
            print(f"\n🏝️ 고립된 문서들:")
            for doc in isolated_docs[:10]:  # 상위 10개만 표시
                print(f"  - {doc['title']} ({doc['word_count']}단어)")
                if doc['tags']:
                    print(f"    태그: {', '.join(doc['tags'])}")
        
        # 약한 연결 문서들
        weak_docs = analysis.get('weakly_connected_documents', [])
        if weak_docs:
            print(f"\n🔗 약한 연결 문서들:")
            for doc in weak_docs[:10]:  # 상위 10개만 표시
                print(f"  - {doc['title']} ({doc['connections']}개 연결, {doc['word_count']}단어)")
                if doc['tags']:
                    print(f"    태그: {', '.join(doc['tags'])}")
        
        # 고립된 태그들
        isolated_tags = analysis.get('isolated_tags', {})
        if isolated_tags:
            print(f"\n🏷️ 고립된 태그들 (상위 10개):")
            for tag, docs in list(isolated_tags.items())[:10]:
                print(f"  - {tag}: {', '.join(docs)}")
        
        # 태그 분포 (상위 태그들)
        tag_dist = analysis.get('tag_distribution', {})
        if tag_dist:
            print(f"\n📈 주요 태그 분포:")
            sorted_tags = sorted(tag_dist.items(), key=lambda x: len(x[1]), reverse=True)
            for tag, docs in sorted_tags[:10]:
                print(f"  - {tag}: {len(docs)}개 문서")
        
        # 결과를 파일로 저장 (옵션)
        if output_file:
            try:
                import json
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)
                print(f"\n💾 분석 결과가 {output_file}에 저장되었습니다.")
            except Exception as e:
                print(f"\n❌ 파일 저장 실패: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 지식 공백 분석 실패: {e}")
        return False


def run_reindex(vault_path: str, force: bool, config: dict, sample_size: Optional[int] = None, 
                include_folders: Optional[list] = None, exclude_folders: Optional[list] = None,
                with_colbert: bool = False, colbert_only: bool = False):
    """전체 재인덱싱 실행 (ColBERT 지원)"""
    try:
        print("🔄 전체 재인덱싱 시작...")
        if force:
            print("⚠️ 강제 모드: 기존 캐시를 무시하고 모든 문서를 재처리합니다.")
        if sample_size:
            print(f"📊 샘플링 모드: {sample_size}개 문서만 처리합니다.")
        if include_folders:
            print(f"📁 폴더 필터: {', '.join(include_folders)} 포함")
        if exclude_folders:
            print(f"🚫 폴더 제외: {', '.join(exclude_folders)}")
        if with_colbert:
            print("🎯 ColBERT 인덱싱 포함")
        if colbert_only:
            print("🎯 ColBERT만 재인덱싱 (Dense 임베딩 제외)")
        
        # 검색 엔진 초기화 (폴더 필터링 설정)
        cache_dir = str(project_root / "cache")
        
        # 임시로 vault 설정에 폴더 필터 추가
        temp_config = config.copy()
        if include_folders or exclude_folders:
            temp_config['vault'] = temp_config.get('vault', {}).copy()
            if include_folders:
                temp_config['vault']['include_folders'] = include_folders
            if exclude_folders:
                temp_config['vault']['exclude_folders'] = exclude_folders
        
        search_engine = AdvancedSearchEngine(vault_path, cache_dir, temp_config)
        
        # 진행률 표시 함수
        def progress_callback(current, total):
            percentage = (current / total) * 100
            print(f"📊 진행률: {current}/{total} ({percentage:.1f}%)")
        
        # Dense 임베딩 인덱스 구축 (colbert_only가 아닌 경우)
        if not colbert_only:
            print("📚 Dense 임베딩 인덱스 구축 중...")
            success = search_engine.build_index(
                force_rebuild=force, 
                progress_callback=progress_callback,
                sample_size=sample_size
            )
            
            if not success:
                print("❌ Dense 임베딩 인덱싱 실패!")
                return False
        
        # ColBERT 인덱싱
        if with_colbert or colbert_only:
            print("🎯 ColBERT 인덱싱 시작...")
            try:
                from .features.colbert_search import ColBERTSearchEngine
                
                colbert_config = temp_config.get('colbert', {})
                colbert_engine = ColBERTSearchEngine(
                    model_name=colbert_config.get('model_name', 'BAAI/bge-m3'),
                    device=colbert_config.get('device', temp_config.get('model', {}).get('device')),
                    use_fp16=colbert_config.get('use_fp16', True),
                    cache_folder=colbert_config.get('cache_folder', temp_config.get('model', {}).get('cache_folder')),
                    max_length=colbert_config.get('max_length', temp_config.get('model', {}).get('max_length', 4096)),
                    cache_dir=cache_dir,
                    enable_cache=colbert_config.get('enable_cache', True)
                )
                
                if colbert_engine.is_available():
                    # 문서 로드 (search_engine에서 가져오기)
                    if hasattr(search_engine, 'documents') and search_engine.documents:
                        documents = search_engine.documents
                    else:
                        # 문서를 직접 로드
                        from .core.vault_processor import VaultProcessor
                        vault_config = temp_config.get('vault', {})
                        vault_processor = VaultProcessor(
                            vault_path=vault_path,
                            excluded_dirs=vault_config.get('excluded_dirs', None),
                            excluded_files=vault_config.get('excluded_files', None), 
                            file_extensions=vault_config.get('file_extensions', None)
                        )
                        documents = vault_processor.process_files()
                        if sample_size:
                            documents = documents[:sample_size]
                    
                    colbert_success = colbert_engine.build_index(
                        documents=documents,
                        batch_size=colbert_config.get('batch_size', 8),
                        max_documents=colbert_config.get('max_documents', None),
                        force_rebuild=force
                    )
                    
                    if colbert_success:
                        print(f"✅ ColBERT 인덱싱 완료!")
                    else:
                        print("⚠️ ColBERT 인덱싱 실패, 계속 진행...")
                else:
                    print("⚠️ ColBERT 엔진을 사용할 수 없습니다.")
                    
            except Exception as e:
                print(f"⚠️ ColBERT 인덱싱 중 오류: {e}")
        
        # 결과 통계 출력
        if not colbert_only:
            stats = search_engine.get_search_statistics()
            print(f"\n✅ 재인덱싱 완료!")
            print(f"📊 Dense 임베딩 결과:")
            print(f"  - 인덱싱된 문서: {stats['indexed_documents']:,}개")
            print(f"  - 임베딩 차원: {stats['embedding_dimension']}차원")
            print(f"  - 캐시된 임베딩: {stats['cache_statistics']['total_embeddings']:,}개")
            print(f"  - Vault 크기: {stats['vault_statistics']['total_size_mb']:.1f}MB")
        
        # ColBERT 캐시 통계
        if with_colbert or colbert_only:
            try:
                from .core.embedding_cache import EmbeddingCache
                cache = EmbeddingCache(cache_dir)
                colbert_stats = cache.get_colbert_statistics()
                if colbert_stats.get('total_colbert_embeddings', 0) > 0:
                    print(f"🎯 ColBERT 캐시 결과:")
                    print(f"  - ColBERT 임베딩: {colbert_stats['total_colbert_embeddings']:,}개")
                    print(f"  - 평균 토큰 수: {colbert_stats['avg_tokens']}개")
                    print(f"  - 캐시 파일 크기: {colbert_stats['total_file_size']:,} bytes")
            except Exception as e:
                logger.debug(f"ColBERT 통계 조회 실패: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 재인덱싱 실패: {e}")
        return False


def run_tagging(vault_path: str, target: str, recursive: bool, dry_run: bool, 
               force: bool, batch_size: int, config: dict):
    """자동 태깅 실행"""
    try:
        print(f"🏷️ 자동 태깅 시작: {target}")
        if dry_run:
            print("🔍 드라이런 모드: 실제 변경 없이 미리보기만 수행합니다.")
        if force:
            print("⚠️ 강제 모드: 기존 태그를 무시하고 새로 생성합니다.")
        if recursive:
            print("📁 재귀 모드: 하위 폴더의 모든 파일을 포함합니다.")
        
        # 의미적 태깅 시스템 초기화
        tagger = SemanticTagger(vault_path, config)
        
        # target 경로 처리 및 vault 내 검색
        vault_base = Path(vault_path)
        target_path = None
        
        # 1. 절대 경로인 경우
        if Path(target).is_absolute():
            target_path = Path(target)
            if target_path.exists():
                print(f"📄 절대 경로로 파일 확인: {target_path}")
            else:
                print(f"❌ 절대 경로 파일이 존재하지 않습니다: {target}")
                return False
        
        # 2. 상대 경로인 경우 (vault 기준) - 먼저 확인
        elif "/" in target:
            candidate_path = vault_base / target
            if candidate_path.exists():
                target_path = candidate_path
                print(f"📁 Vault 상대 경로로 확인: {target}")
            else:
                print(f"❌ Vault 내 상대 경로가 존재하지 않습니다: {target}")
                return False
        
        # 3. 파일명만 제공된 경우 - vault 전체에서 검색
        else:
            print(f"🔍 '{target}' 파일을 vault에서 검색 중...")
            found_files = []
            
            # .md 확장자가 없으면 추가해서도 검색
            search_patterns = [target]
            if not target.endswith('.md'):
                search_patterns.append(f"{target}.md")
            
            for pattern in search_patterns:
                # vault 전체에서 파일명 검색 (대소문자 구분 없음)
                for md_file in vault_base.rglob("*.md"):
                    if md_file.name.lower() == pattern.lower():
                        found_files.append(md_file)
                    elif pattern.lower() in md_file.name.lower():
                        found_files.append(md_file)
            
            if not found_files:
                print(f"❌ '{target}' 파일을 vault에서 찾을 수 없습니다.")
                print(f"   검색 경로: {vault_base}")
                return False
            elif len(found_files) == 1:
                target_path = found_files[0]
                rel_path = target_path.relative_to(vault_base)
                print(f"✅ 파일 발견: {rel_path}")
            else:
                print(f"📋 '{target}' 관련 파일이 {len(found_files)}개 발견되었습니다:")
                for i, file_path in enumerate(found_files[:10], 1):  # 최대 10개만 표시
                    rel_path = file_path.relative_to(vault_base)
                    print(f"  {i}. {rel_path}")
                
                if len(found_files) <= 10:
                    # 첫 번째 파일을 기본 선택
                    target_path = found_files[0]
                    rel_path = target_path.relative_to(vault_base)
                    print(f"🎯 첫 번째 파일을 선택: {rel_path}")
                else:
                    print(f"   ... 및 {len(found_files) - 10}개 더")
                    print("❌ 너무 많은 파일이 발견되었습니다. 더 구체적인 파일명을 제공해주세요.")
                    return False
        
        # vault 내부 경로인지 확인
        try:
            if target_path:
                relative_path = target_path.resolve().relative_to(vault_base.resolve())
                print(f"📁 Vault 내부 경로 확인: {relative_path}")
        except ValueError:
            print(f"⚠️ 경고: Vault 외부 경로입니다: {target_path}")
        
        if not target_path or not target_path.exists():
            print(f"❌ 최종 대상 경로가 존재하지 않습니다: {target_path}")
            return False
        
        results = []
        
        # 단일 파일 태깅
        if target_path.is_file():
            if target.lower().endswith('.md'):
                print(f"📄 단일 파일 태깅: {target_path.name}")
                result = tagger.tag_document(str(target_path), dry_run=dry_run)
                results.append(result)
            else:
                print("❌ 마크다운 파일(.md)만 태깅 가능합니다.")
                return False
        
        # 폴더 배치 태깅
        elif target_path.is_dir():
            print(f"📁 폴더 배치 태깅: {target_path}")
            results = tagger.tag_folder(
                str(target_path), 
                recursive=recursive, 
                dry_run=dry_run
            )
        
        else:
            print("❌ 유효하지 않은 대상 경로입니다.")
            return False
        
        # 결과 출력
        if results:
            successful = sum(1 for r in results if r.success)
            total = len(results)
            
            print(f"\n📊 태깅 결과:")
            print("-" * 50)
            print(f"처리 파일: {total}개")
            print(f"성공: {successful}개")
            print(f"실패: {total - successful}개")
            print(f"성공률: {successful/total*100:.1f}%")
            
            # 상세 결과 표시 (최대 10개)
            print(f"\n📋 상세 결과 (상위 {min(10, len(results))}개):")
            for i, result in enumerate(results[:10]):
                print(f"\n{i+1}. {Path(result.file_path).name}")
                if result.success:
                    print(f"   ✅ 성공 (처리시간: {result.processing_time:.2f}초)")
                    print(f"   기존 태그: {len(result.original_tags)}개")
                    print(f"   생성 태그: {len(result.generated_tags)}개")
                    
                    if result.generated_tags:
                        print(f"   새 태그:")
                        for category, tags in result.categorized_tags.items():
                            if tags:
                                print(f"     {category}: {', '.join(tags)}")
                    
                    # 신뢰도 높은 태그들
                    high_confidence_tags = [
                        tag for tag, score in result.confidence_scores.items()
                        if score > 0.7
                    ]
                    if high_confidence_tags:
                        print(f"   고신뢰도 태그: {', '.join(high_confidence_tags)}")
                else:
                    print(f"   ❌ 실패: {result.error_message}")
            
            return successful == total
        
        else:
            print("❌ 처리할 파일이 없습니다.")
            return False
        
    except Exception as e:
        print(f"❌ 자동 태깅 실패: {e}")
        logger.exception("태깅 중 상세 오류:")
        return False


def display_tagging_result(result: TaggingResult):
    """단일 태깅 결과 표시"""
    print(f"\n📄 태깅 결과: {Path(result.file_path).name}")
    print("-" * 50)
    
    if result.success:
        print(f"✅ 성공 (처리시간: {result.processing_time:.2f}초)")
        print(f"기존 태그: {result.original_tags if result.original_tags else '없음'}")
        print(f"생성 태그: {len(result.generated_tags)}개")
        
        if result.categorized_tags:
            print("\n🎯 카테고리별 태그:")
            for category, tags in result.categorized_tags.items():
                if tags:
                    print(f"  {category}: {', '.join(tags)}")
        
        if result.confidence_scores:
            print(f"\n📊 신뢰도 점수:")
            sorted_scores = sorted(
                result.confidence_scores.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            for tag, score in sorted_scores[:5]:  # 상위 5개
                print(f"  {tag}: {score:.3f}")
    else:
        print(f"❌ 실패: {result.error_message}")


def run_moc_generation(
    vault_path: str,
    topic: str,
    top_k: int,
    threshold: float,
    output_file: Optional[str],
    config: dict,
    include_orphans: bool = False,
    use_expansion: bool = True
):
    """MOC 생성 실행"""
    try:
        print(f"📚 '{topic}' MOC 생성 시작...")
        
        # 검색 엔진 초기화
        cache_dir = str(project_root / "cache")
        search_engine = AdvancedSearchEngine(vault_path, cache_dir, config)
        
        if not search_engine.indexed:
            print("📚 인덱스 구축 중...")
            if not search_engine.build_index():
                print("❌ 인덱스 구축 실패")
                return False
        
        # MOC 생성기 초기화
        moc_generator = MOCGenerator(search_engine, config)
        
        # 출력 파일명 자동 생성 (지정되지 않은 경우)
        if not output_file:
            safe_topic = topic.replace(' ', '-').replace('/', '-')
            output_file = f"MOC-{safe_topic}.md"
        
        # MOC 생성
        moc_data = moc_generator.generate_moc(
            topic=topic,
            top_k=top_k,
            threshold=threshold,
            include_orphans=include_orphans,
            use_expansion=use_expansion,
            output_file=output_file
        )
        
        print(f"\n📊 MOC 생성 결과:")
        print("-" * 50)
        print(f"주제: {moc_data.topic}")
        print(f"총 문서: {moc_data.total_documents}개")
        print(f"핵심 문서: {len(moc_data.core_documents)}개")
        print(f"카테고리: {len(moc_data.categories)}개")
        print(f"학습 경로: {len(moc_data.learning_path)}단계")
        print(f"관련 주제: {len(moc_data.related_topics)}개")
        print(f"최근 업데이트: {len(moc_data.recent_updates)}개")
        print(f"문서 관계: {len(moc_data.relationships)}개")
        
        if moc_data.categories:
            print(f"\n📋 카테고리별 문서 분포:")
            for category in moc_data.categories:
                print(f"  {category.name}: {len(category.documents)}개 문서")
        
        if moc_data.learning_path:
            print(f"\n🛤️ 학습 경로:")
            for step in moc_data.learning_path:
                print(f"  {step.step}. {step.title} ({step.difficulty_level}) - {len(step.documents)}개 문서")
        
        if output_file:
            print(f"\n💾 MOC 파일이 {output_file}에 저장되었습니다.")
            
        return True
        
    except Exception as e:
        print(f"❌ MOC 생성 실패: {e}")
        logger.exception("MOC 생성 중 상세 오류:")
        return False


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="Vault Intelligence System V2 - Sentence Transformers 기반 지능형 검색 시스템"
    )
    
    parser.add_argument(
        "command",
        choices=["init", "test", "info", "search", "duplicates", "collect", "analyze", "reindex", "related", "analyze-gaps", "tag", "generate-moc"],
        help="실행할 명령어"
    )
    
    parser.add_argument(
        "--vault-path",
        default="/Users/msbaek/DocumentsLocal/msbaek_vault",
        help="Vault 경로 (기본값: /Users/msbaek/DocumentsLocal/msbaek_vault)"
    )
    
    parser.add_argument(
        "--config",
        help="설정 파일 경로"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="상세 로그 출력"
    )
    
    # Phase 2 기능 관련 인자들
    parser.add_argument(
        "--query",
        help="검색 쿼리"
    )
    
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="상위 K개 결과 (기본값: 10)"
    )
    
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.3,
        help="유사도 임계값 (기본값: 0.3)"
    )
    
    parser.add_argument(
        "--rerank",
        action="store_true",
        help="재순위화 활성화 (BGE Reranker V2-M3 사용)"
    )
    
    parser.add_argument(
        "--search-method",
        choices=["semantic", "keyword", "hybrid", "colbert"],
        default="hybrid",
        help="검색 방법 (기본값: hybrid)"
    )
    
    parser.add_argument(
        "--expand",
        action="store_true",
        help="쿼리 확장 활성화 (동의어 + HyDE)"
    )
    
    parser.add_argument(
        "--no-synonyms",
        action="store_true",
        help="동의어 확장 비활성화"
    )
    
    parser.add_argument(
        "--no-hyde",
        action="store_true",
        help="HyDE 확장 비활성화"
    )
    
    parser.add_argument(
        "--topic",
        help="수집할 주제"
    )
    
    parser.add_argument(
        "--output",
        help="출력 파일 경로"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="강제 전체 재인덱싱 (기존 캐시 무시)"
    )
    
    parser.add_argument(
        "--sample-size",
        type=int,
        help="샘플링할 문서 수 (대규모 vault 성능 최적화용)"
    )
    
    parser.add_argument(
        "--include-folders",
        nargs="+",
        help="포함할 폴더 목록 (폴더별 점진적 색인)"
    )
    
    parser.add_argument(
        "--exclude-folders", 
        nargs="+",
        help="제외할 폴더 목록"
    )
    
    parser.add_argument(
        "--file",
        help="관련 문서를 찾을 기준 파일 (related 명령어용)"
    )
    
    parser.add_argument(
        "--with-centrality",
        action="store_true",
        help="중심성 점수를 검색 랭킹에 반영"
    )
    
    parser.add_argument(
        "--centrality-weight",
        type=float,
        default=0.2,
        help="중심성 점수 가중치 (0.0-1.0, 기본값: 0.2)"
    )
    
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.3,
        help="관련성 판정 유사도 임계값 (기본값: 0.3)"
    )
    
    parser.add_argument(
        "--min-connections",
        type=int,
        default=2,
        help="최소 연결 수 (이보다 적으면 약한 연결로 판정, 기본값: 2)"
    )
    
    # ColBERT 인덱싱 관련 인자들
    parser.add_argument(
        "--with-colbert",
        action="store_true",
        help="ColBERT 인덱싱 포함 (reindex 명령어용)"
    )
    
    parser.add_argument(
        "--colbert-only",
        action="store_true",
        help="ColBERT만 재인덱싱 (Dense 임베딩 제외)"
    )
    
    # 태깅 관련 인자들 (Phase 7)
    parser.add_argument(
        "--target",
        help="태깅할 대상 파일 또는 폴더 경로"
    )
    
    parser.add_argument(
        "--recursive",
        action="store_true", 
        help="하위 폴더 포함 (폴더 태깅 시)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 변경 없이 미리보기"
    )
    
    parser.add_argument(
        "--tag-force",
        action="store_true",
        help="기존 태그 무시하고 재생성"
    )
    
    parser.add_argument(
        "--batch-size", 
        type=int,
        default=10,
        help="배치 처리 크기 (기본값: 10)"
    )
    
    # MOC 생성 관련 인자들
    parser.add_argument(
        "--include-orphans",
        action="store_true",
        help="연결되지 않은 문서도 MOC에 포함"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 설정 로딩
    config = load_config(args.config)
    
    # 명령어 실행
    if args.command == "info":
        show_system_info()
    
    elif args.command == "test":
        if not check_dependencies():
            sys.exit(1)
        
        if run_tests():
            print("✅ 모든 테스트 통과!")
        else:
            print("❌ 일부 테스트 실패!")
            sys.exit(1)
    
    elif args.command == "init":
        if not check_dependencies():
            sys.exit(1)
        
        if initialize_system(args.vault_path, config):
            print("\n🎉 Vault Intelligence System V2 초기화 완료!")
            print("\n다음 단계:")
            print("1. python -m src search --query 'TDD'     # 검색 테스트")
            print("2. python -m src duplicates               # 중복 감지")  
            print("3. python -m src collect --topic 'TDD'   # 주제 수집")
            print("4. python -m src analyze                  # 주제 분석")
        else:
            print("❌ 초기화 실패!")
            sys.exit(1)
    
    # Phase 2 기능들
    elif args.command == "search":
        if not check_dependencies():
            sys.exit(1)
        
        if not args.query:
            print("❌ 검색 쿼리가 필요합니다. --query 옵션을 사용하세요.")
            sys.exit(1)
        
        if run_search(
            args.vault_path, 
            args.query, 
            args.top_k, 
            args.threshold, 
            config, 
            getattr(args, 'sample_size', None),
            use_reranker=args.rerank,
            search_method=args.search_method,
            use_expansion=args.expand,
            include_synonyms=not args.no_synonyms,
            include_hyde=not args.no_hyde,
            use_centrality=args.with_centrality,
            centrality_weight=args.centrality_weight
        ):
            print("✅ 검색 완료!")
        else:
            print("❌ 검색 실패!")
            sys.exit(1)
    
    elif args.command == "duplicates":
        if not check_dependencies():
            sys.exit(1)
        
        if run_duplicate_detection(args.vault_path, config):
            print("✅ 중복 감지 완료!")
        else:
            print("❌ 중복 감지 실패!")
            sys.exit(1)
    
    elif args.command == "collect":
        if not check_dependencies():
            sys.exit(1)
        
        if not args.topic:
            print("❌ 수집할 주제가 필요합니다. --topic 옵션을 사용하세요.")
            sys.exit(1)
        
        if run_topic_collection(
            args.vault_path, 
            args.topic, 
            args.top_k, 
            args.threshold, 
            args.output, 
            config,
            use_expansion=args.expand,
            include_synonyms=not args.no_synonyms,
            include_hyde=not args.no_hyde
        ):
            print("✅ 주제 수집 완료!")
        else:
            print("❌ 주제 수집 실패!")
            sys.exit(1)
    
    elif args.command == "analyze":
        if not check_dependencies():
            sys.exit(1)
        
        if run_topic_analysis(args.vault_path, args.output, config):
            print("✅ 주제 분석 완료!")
        else:
            print("❌ 주제 분석 실패!")
            sys.exit(1)
    
    elif args.command == "reindex":
        if not check_dependencies():
            sys.exit(1)
        
        if run_reindex(args.vault_path, args.force, config, 
                      getattr(args, 'sample_size', None),
                      getattr(args, 'include_folders', None),
                      getattr(args, 'exclude_folders', None),
                      getattr(args, 'with_colbert', False),
                      getattr(args, 'colbert_only', False)):
            print("✅ 재인덱싱 완료!")
        else:
            print("❌ 재인덱싱 실패!")
            sys.exit(1)
    
    elif args.command == "related":
        if not check_dependencies():
            sys.exit(1)
        
        if not args.file:
            print("❌ 기준 파일이 필요합니다. --file 옵션을 사용하세요.")
            sys.exit(1)
        
        if run_related_documents(
            args.vault_path,
            args.file,
            args.top_k,
            config,
            include_centrality=True,  # 항상 중심성 점수 포함
            similarity_threshold=args.similarity_threshold
        ):
            print("✅ 관련 문서 찾기 완료!")
        else:
            print("❌ 관련 문서 찾기 실패!")
            sys.exit(1)
    
    elif args.command == "analyze-gaps":
        if not check_dependencies():
            sys.exit(1)
        
        if run_knowledge_gap_analysis(
            args.vault_path,
            config,
            output_file=args.output,
            similarity_threshold=args.similarity_threshold,
            min_connections=args.min_connections
        ):
            print("✅ 지식 공백 분석 완료!")
        else:
            print("❌ 지식 공백 분석 실패!")
            sys.exit(1)
    
    elif args.command == "tag":
        if not check_dependencies():
            sys.exit(1)
        
        # 태깅 대상 확인
        if args.target:
            target_path = args.target
        elif args.query:  # 검색 쿼리가 있으면 현재 디렉토리에서 해당 파일 찾기
            target_path = f"./*{args.query}*.md"
        else:
            print("❌ 태깅 대상이 필요합니다.")
            print("사용법:")
            print("  # 파일명으로 검색하여 태깅")
            print("  python -m src tag --target spring-tdd")
            print("  python -m src tag --target my-file.md")
            print("")
            print("  # vault 상대 경로로 태깅")
            print("  python -m src tag --target 003-RESOURCES/books/clean-code.md")
            print("  python -m src tag --target 003-RESOURCES/ --recursive")
            print("")
            print("  # 전체 vault 태깅 (주의!)")
            print("  python -m src tag --target . --recursive --dry-run")
            print("")
            print("  # 강제 재태깅")
            print("  python -m src tag --target my-file --tag-force")
            sys.exit(1)
        
        if run_tagging(
            vault_path=args.vault_path,
            target=target_path,
            recursive=args.recursive,
            dry_run=args.dry_run,
            force=args.tag_force,
            batch_size=args.batch_size,
            config=config
        ):
            print("✅ 자동 태깅 완료!")
        else:
            print("❌ 자동 태깅 실패!")
            sys.exit(1)
    
    elif args.command == "generate-moc":
        if not check_dependencies():
            sys.exit(1)
        
        if not args.topic:
            print("❌ MOC 생성할 주제가 필요합니다. --topic 옵션을 사용하세요.")
            print("사용법:")
            print("  python -m src generate-moc --topic 'TDD'")
            print("  python -m src generate-moc --topic 'TDD' --output 'TDD-MOC.md'")
            print("  python -m src generate-moc --topic 'TDD' --top-k 50 --include-orphans")
            sys.exit(1)
        
        if run_moc_generation(
            vault_path=args.vault_path,
            topic=args.topic,
            top_k=args.top_k,
            threshold=args.threshold,
            output_file=args.output,
            config=config,
            include_orphans=args.include_orphans,
            use_expansion=args.expand
        ):
            print("✅ MOC 생성 완료!")
        else:
            print("❌ MOC 생성 실패!")
            sys.exit(1)


if __name__ == "__main__":
    main()