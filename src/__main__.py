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
        print(f"PyTorch 장치: {device}")
        if torch.cuda.is_available():
            print(f"GPU 메모리: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
    except:
        print("PyTorch: 사용 불가 (TF-IDF 모드)")
    
    print("\n📋 Phase 2 완료 기능:")
    print("- TF-IDF 기반 임베딩 (임시 구현)")
    print("- 고급 검색 (의미적/키워드/하이브리드)")
    print("- 중복 문서 감지")
    print("- 주제별 클러스터링")
    print("- 문서 수집 및 통합")
    print("- SQLite 기반 영구 캐싱")
    print()
    print("📚 문서:")
    print("- 사용자 가이드: docs/USER_GUIDE.md")
    print("- 실전 예제: docs/EXAMPLES.md")
    print()
    print("⚡ 빠른 시작:")
    print("  python -m src search --query 'TDD'")
    print("  python -m src collect --topic '리팩토링'")
    print("  python -m src duplicates")


def run_search(vault_path: str, query: str, top_k: int, threshold: float, config: dict, sample_size: Optional[int] = None):
    """검색 실행"""
    try:
        print(f"🔍 검색 시작: '{query}'")
        if sample_size:
            print(f"📊 샘플링 모드: {sample_size}개 문서만 처리")
        
        # 검색 엔진 초기화
        cache_dir = str(project_root / "cache")
        search_engine = AdvancedSearchEngine(vault_path, cache_dir, config)
        
        if not search_engine.indexed:
            print("📚 인덱스 구축 중...")
            if not search_engine.build_index(sample_size=sample_size):
                print("❌ 인덱스 구축 실패")
                return False
        
        # 하이브리드 검색 수행
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


def run_topic_collection(vault_path: str, topic: str, top_k: int, threshold: float, output_file: str, config: dict):
    """주제별 문서 수집 실행"""
    try:
        print(f"📚 주제 '{topic}' 문서 수집 시작...")
        
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
            output_file=output_file
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


def run_reindex(vault_path: str, force: bool, config: dict, sample_size: Optional[int] = None, 
                include_folders: Optional[list] = None, exclude_folders: Optional[list] = None):
    """전체 재인덱싱 실행"""
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
        
        # 인덱스 구축 (샘플링 지원)
        print("📚 인덱스 구축 중...")
        success = search_engine.build_index(
            force_rebuild=force, 
            progress_callback=progress_callback,
            sample_size=sample_size
        )
        
        if success:
            stats = search_engine.get_search_statistics()
            print(f"\n✅ 재인덱싱 완료!")
            print(f"📊 처리 결과:")
            print(f"  - 인덱싱된 문서: {stats['indexed_documents']:,}개")
            print(f"  - 임베딩 차원: {stats['embedding_dimension']}차원")
            print(f"  - 캐시된 임베딩: {stats['cache_statistics']['total_embeddings']:,}개")
            print(f"  - Vault 크기: {stats['vault_statistics']['total_size_mb']:.1f}MB")
            return True
        else:
            print("❌ 재인덱싱 실패!")
            return False
        
    except Exception as e:
        print(f"❌ 재인덱싱 실패: {e}")
        return False


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="Vault Intelligence System V2 - Sentence Transformers 기반 지능형 검색 시스템"
    )
    
    parser.add_argument(
        "command",
        choices=["init", "test", "info", "search", "duplicates", "collect", "analyze", "reindex"],
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
        
        if run_search(args.vault_path, args.query, args.top_k, args.threshold, config, getattr(args, 'sample_size', None)):
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
        
        if run_topic_collection(args.vault_path, args.topic, args.top_k, args.threshold, args.output, config):
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
                      getattr(args, 'exclude_folders', None)):
            print("✅ 재인덱싱 완료!")
        else:
            print("❌ 재인덱싱 실패!")
            sys.exit(1)


if __name__ == "__main__":
    main()