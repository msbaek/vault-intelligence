#!/usr/bin/env python3
"""
Vault Assistant - Unified CLI for Vault Intelligence System V2

모든 기능을 통합한 명령줄 인터페이스
"""

import sys
import os
import argparse
import yaml
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.core.sentence_transformer_engine import SentenceTransformerEngine
    from src.core.embedding_cache import EmbeddingCache
    from src.core.vault_processor import VaultProcessor
    from src.features.advanced_search import AdvancedSearchEngine, SearchQuery
    from src.features.duplicate_detector import DuplicateDetector
    from src.features.topic_analyzer import TopicAnalyzer
    from src.features.topic_collector import TopicCollector
    from src.features.knowledge_graph import KnowledgeGraphBuilder
except ImportError as e:
    print(f"❌ 모듈 가져오기 실패: {e}")
    print("프로젝트 루트에서 실행하거나 PYTHONPATH를 설정해주세요.")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VaultAssistant:
    """Vault 관리 통합 CLI"""
    
    def __init__(self, vault_path: str, config_path: Optional[str] = None):
        """
        Args:
            vault_path: Obsidian vault 경로
            config_path: 설정 파일 경로
        """
        self.vault_path = Path(vault_path)
        self.project_root = Path(__file__).parent.parent
        self.config = self._load_config(config_path)
        
        # 캐시 디렉토리
        self.cache_dir = self.project_root / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # 핵심 컴포넌트 초기화
        self.search_engine = None
        self.duplicate_detector = None
        self.topic_analyzer = None
        self.topic_collector = None
        self.graph_builder = None
        
        logger.info(f"VaultAssistant 초기화: {vault_path}")
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """설정 파일 로딩"""
        if config_path is None:
            config_path = self.project_root / "config" / "settings.yaml"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"설정 파일 로딩 완료: {config_path}")
            return config
        except Exception as e:
            logger.error(f"설정 파일 로딩 실패: {e}")
            return self._default_config()
    
    def _default_config(self) -> Dict:
        """기본 설정"""
        return {
            "model": {
                "name": "paraphrase-multilingual-mpnet-base-v2",
                "dimension": 768,
                "batch_size": 32
            },
            "search": {
                "default_top_k": 10,
                "similarity_threshold": 0.3
            },
            "duplicates": {
                "similarity_threshold": 0.85,
                "min_word_count": 50
            },
            "clustering": {
                "default_n_clusters": 5,
                "algorithm": "kmeans"
            },
            "collection": {
                "min_documents": 3,
                "group_by_tags": True
            },
            "graph": {
                "similarity_threshold": 0.4,
                "include_tag_nodes": True
            }
        }
    
    def _initialize_components(self):
        """컴포넌트 초기화 (lazy loading)"""
        if self.search_engine is None:
            logger.info("검색 엔진 초기화 중...")
            self.search_engine = AdvancedSearchEngine(
                str(self.vault_path),
                str(self.cache_dir),
                self.config
            )
            
            self.duplicate_detector = DuplicateDetector(self.search_engine, self.config)
            self.topic_analyzer = TopicAnalyzer(self.search_engine, self.config)
            self.topic_collector = TopicCollector(self.search_engine, self.config)
            self.graph_builder = KnowledgeGraphBuilder(self.search_engine, self.config)
    
    def build_index(self, force_rebuild: bool = False) -> bool:
        """검색 인덱스 구축"""
        try:
            self._initialize_components()
            
            def progress_callback(current, total):
                if current % 100 == 0:
                    print(f"진행률: {current}/{total} ({current/total*100:.1f}%)")
            
            print("🔄 검색 인덱스 구축 중...")
            success = self.search_engine.build_index(force_rebuild, progress_callback)
            
            if success:
                print("✅ 인덱스 구축 완료!")
                self._print_index_stats()
            else:
                print("❌ 인덱스 구축 실패!")
            
            return success
            
        except Exception as e:
            logger.error(f"인덱스 구축 실패: {e}")
            print(f"❌ 오류 발생: {e}")
            return False
    
    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        search_type: str = "hybrid",
        threshold: Optional[float] = None,
        output_file: Optional[str] = None
    ) -> bool:
        """문서 검색"""
        try:
            self._initialize_components()
            
            if not self.search_engine.indexed:
                print("❌ 인덱스가 구축되지 않았습니다. 먼저 'index' 명령을 실행하세요.")
                return False
            
            top_k = top_k or self.config['search']['default_top_k']
            threshold = threshold or self.config['search']['similarity_threshold']
            
            print(f"🔍 '{query}' 검색 중 ({search_type})...")
            
            # 검색 타입별 실행
            if search_type == "semantic":
                results = self.search_engine.semantic_search(query, top_k, threshold)
            elif search_type == "keyword":
                results = self.search_engine.keyword_search(query, top_k)
            elif search_type == "hybrid":
                results = self.search_engine.hybrid_search(query, top_k, threshold=threshold)
            else:
                print(f"❌ 알 수 없는 검색 타입: {search_type}")
                return False
            
            if not results:
                print("검색 결과가 없습니다.")
                return True
            
            # 결과 출력
            print(f"\n📋 검색 결과 ({len(results)}개):")
            print("=" * 80)
            
            for result in results:
                print(f"\n{result.rank}. **{result.document.title}**")
                print(f"   📄 경로: {result.document.path}")
                print(f"   📊 유사도: {result.similarity_score:.4f} ({result.match_type})")
                print(f"   📝 단어 수: {result.document.word_count}")
                
                if result.matched_keywords:
                    print(f"   🔍 매칭 키워드: {', '.join(result.matched_keywords)}")
                
                if result.document.tags:
                    print(f"   🏷️ 태그: {', '.join(result.document.tags[:5])}")
                
                if result.snippet:
                    print(f"   💬 미리보기: {result.snippet}")
            
            # 파일 저장
            if output_file:
                self._save_search_results(results, query, output_file)
                print(f"\n💾 결과 저장: {output_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"검색 실패: {e}")
            print(f"❌ 검색 중 오류: {e}")
            return False
    
    def find_duplicates(
        self,
        threshold: Optional[float] = None,
        min_word_count: Optional[int] = None,
        output_file: Optional[str] = None
    ) -> bool:
        """중복 문서 감지"""
        try:
            self._initialize_components()
            
            if not self.search_engine.indexed:
                print("❌ 인덱스가 구축되지 않았습니다. 먼저 'index' 명령을 실행하세요.")
                return False
            
            threshold = threshold or self.config['duplicates']['similarity_threshold']
            min_word_count = min_word_count or self.config['duplicates']['min_word_count']
            
            print(f"🔍 중복 문서 감지 중 (임계값: {threshold})...")
            
            analysis = self.duplicate_detector.find_duplicates(threshold, min_word_count)
            
            print(f"\n📊 중복 분석 결과:")
            print("=" * 60)
            print(f"📁 총 문서: {analysis.total_documents}개")
            print(f"🔗 중복 그룹: {analysis.get_group_count()}개")
            print(f"📋 중복 문서: {analysis.duplicate_count}개")
            print(f"📄 고유 문서: {analysis.unique_count}개")
            print(f"📊 중복률: {analysis.get_duplicate_ratio():.1%}")
            print(f"💾 잠재적 절약: {analysis.potential_savings_mb:.2f}MB")
            
            if analysis.duplicate_groups:
                print(f"\n🔗 중복 그룹 상세:")
                
                for i, group in enumerate(analysis.duplicate_groups):
                    print(f"\n그룹 {i+1} (평균 유사도: {group.average_similarity:.3f}):")
                    print(f"   👑 마스터: {group.master_document.title if group.master_document else 'None'}")
                    
                    for doc in group.documents:
                        marker = "👑" if group.master_document and doc.path == group.master_document.path else "📄"
                        print(f"   {marker} {doc.title} ({doc.word_count} 단어)")
                    
                    # 병합 제안
                    suggestions = self.duplicate_detector.generate_merge_suggestions(group)
                    if 'potential_savings_mb' in suggestions:
                        print(f"   💡 절약 가능: {suggestions['potential_savings_mb']:.2f}MB")
            
            # 파일 저장
            if output_file:
                if self.duplicate_detector.export_analysis(analysis, output_file):
                    print(f"\n💾 분석 결과 저장: {output_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"중복 감지 실패: {e}")
            print(f"❌ 중복 감지 중 오류: {e}")
            return False
    
    def analyze_topics(
        self,
        query: Optional[str] = None,
        n_clusters: Optional[int] = None,
        algorithm: Optional[str] = None,
        output_file: Optional[str] = None,
        visualize: bool = False
    ) -> bool:
        """주제 분석"""
        try:
            self._initialize_components()
            
            if not self.search_engine.indexed:
                print("❌ 인덱스가 구축되지 않았습니다. 먼저 'index' 명령을 실행하세요.")
                return False
            
            n_clusters = n_clusters or self.config['clustering']['default_n_clusters']
            algorithm = algorithm or self.config['clustering']['algorithm']
            
            if query:
                print(f"🔍 '{query}' 주제 분석 중...")
            else:
                print(f"🔍 전체 문서 주제 분석 중...")
            
            analysis = self.topic_analyzer.analyze_topics(query, n_clusters, algorithm)
            
            print(f"\n📊 주제 분석 결과:")
            print("=" * 60)
            print(f"📁 분석 문서: {analysis.total_documents}개")
            print(f"🎯 클러스터: {analysis.get_cluster_count()}개")
            print(f"📈 실루엣 점수: {analysis.silhouette_score:.3f}" if analysis.silhouette_score else "")
            print(f"🤖 알고리즘: {analysis.algorithm}")
            
            if analysis.clusters:
                print(f"\n🎯 클러스터 상세:")
                
                for i, cluster in enumerate(analysis.clusters):
                    print(f"\n클러스터 {i+1}: {cluster.label}")
                    print(f"   📄 문서: {cluster.get_document_count()}개")
                    print(f"   📊 일관성: {cluster.coherence_score:.3f}")
                    print(f"   🔗 평균 유사도: {cluster.get_average_similarity():.3f}")
                    print(f"   📝 총 단어: {cluster.get_total_word_count():,}개")
                    
                    if cluster.keywords:
                        print(f"   🏷️ 키워드: {', '.join(cluster.keywords[:10])}")
                    
                    if cluster.representative_doc:
                        print(f"   👑 대표 문서: {cluster.representative_doc.title}")
                    
                    print("   📋 문서 목록:")
                    for doc in cluster.documents[:5]:  # 상위 5개만 표시
                        print(f"      - {doc.title} ({doc.word_count} 단어)")
                    
                    if len(cluster.documents) > 5:
                        print(f"      ... 외 {len(cluster.documents) - 5}개")
            
            # 파일 저장
            if output_file:
                if self.topic_analyzer.export_analysis(analysis, output_file):
                    print(f"\n💾 분석 결과 저장: {output_file}")
            
            # 시각화
            if visualize:
                viz_file = output_file.replace('.json', '.png') if output_file else "cluster_visualization.png"
                if self.topic_analyzer.visualize_clusters(analysis, viz_file):
                    print(f"📈 시각화 저장: {viz_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"주제 분석 실패: {e}")
            print(f"❌ 주제 분석 중 오류: {e}")
            return False
    
    def collect_topic(
        self,
        topic: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
        output_file: Optional[str] = None,
        format_type: str = "markdown"
    ) -> bool:
        """주제별 문서 수집"""
        try:
            self._initialize_components()
            
            if not self.search_engine.indexed:
                print("❌ 인덱스가 구축되지 않았습니다. 먼저 'index' 명령을 실행하세요.")
                return False
            
            top_k = top_k or 100
            threshold = threshold or self.config['search']['similarity_threshold']
            
            print(f"📚 '{topic}' 주제 문서 수집 중...")
            
            collection = self.topic_collector.collect_topic(
                topic, top_k, threshold, output_file=output_file
            )
            
            print(f"\n📊 수집 결과:")
            print("=" * 50)
            print(f"🎯 주제: {collection.metadata.topic}")
            print(f"📄 수집 문서: {collection.metadata.total_documents}개")
            print(f"📝 총 단어: {collection.metadata.total_word_count:,}개")
            print(f"💾 총 크기: {collection.metadata.total_size_bytes / (1024*1024):.2f}MB")
            print(f"🔍 검색 쿼리: '{collection.metadata.search_query}'")
            
            if collection.metadata.tag_distribution:
                print(f"\n🏷️ 주요 태그:")
                for tag, count in list(collection.metadata.tag_distribution.items())[:10]:
                    print(f"   - {tag}: {count}개")
            
            if collection.grouped_documents:
                print(f"\n📁 그룹별 분포:")
                for group, docs in collection.grouped_documents.items():
                    print(f"   - {group}: {len(docs)}개 문서")
            
            # 기본 출력 파일명 생성
            if not output_file:
                safe_topic = topic.lower().replace(' ', '_').replace('/', '_')
                output_file = f"{safe_topic}_collection.{format_type}"
            
            # 파일 저장
            if self.topic_collector.export_collection(collection, output_file, format_type):
                print(f"\n💾 컬렉션 저장: {output_file}")
            
            # 관련 주제 제안
            suggestions = self.topic_collector.suggest_related_topics(topic, 5)
            if suggestions:
                print(f"\n🔗 관련 주제 제안:")
                for suggested_topic, count in suggestions:
                    print(f"   - {suggested_topic} ({count}회 언급)")
            
            return True
            
        except Exception as e:
            logger.error(f"주제 수집 실패: {e}")
            print(f"❌ 주제 수집 중 오류: {e}")
            return False
    
    def build_graph(
        self,
        similarity_threshold: Optional[float] = None,
        include_tags: bool = True,
        output_file: Optional[str] = None,
        visualize: bool = False
    ) -> bool:
        """지식 그래프 구축"""
        try:
            self._initialize_components()
            
            if not self.search_engine.indexed:
                print("❌ 인덱스가 구축되지 않았습니다. 먼저 'index' 명령을 실행하세요.")
                return False
            
            similarity_threshold = similarity_threshold or self.config['graph']['similarity_threshold']
            
            print(f"🕸️ 지식 그래프 구축 중 (임계값: {similarity_threshold})...")
            
            knowledge_graph = self.graph_builder.build_graph(
                similarity_threshold=similarity_threshold,
                include_tag_nodes=include_tags
            )
            
            print(f"\n📊 지식 그래프 결과:")
            print("=" * 60)
            print(f"🔵 노드: {knowledge_graph.get_node_count()}개")
            print(f"🔗 엣지: {knowledge_graph.get_edge_count()}개")
            print(f"📊 밀도: {knowledge_graph.get_density():.3f}")
            
            # 메트릭 출력
            if knowledge_graph.graph_metrics:
                metrics = knowledge_graph.graph_metrics
                print(f"🔄 연결성: {'연결됨' if metrics.get('is_connected', False) else '분리됨'}")
                print(f"🌐 컴포넌트: {metrics.get('number_of_components', 0)}개")
                print(f"🎯 클러스터링: {metrics.get('average_clustering', 0):.3f}")
            
            # 중심성 점수 (상위 10개)
            if knowledge_graph.centrality_scores:
                print(f"\n🎯 높은 중심성 노드:")
                sorted_centrality = sorted(
                    knowledge_graph.centrality_scores.items(),
                    key=lambda x: x[1], reverse=True
                )[:10]
                
                for node_id, score in sorted_centrality:
                    node = next((n for n in knowledge_graph.nodes if n.id == node_id), None)
                    if node:
                        node_type = "📄" if node.node_type == "document" else "🏷️"
                        print(f"   {node_type} {node.title}: {score:.3f}")
            
            # 커뮤니티 정보
            if knowledge_graph.communities:
                print(f"\n🏘️ 커뮤니티: {len(knowledge_graph.communities)}개")
                for i, community in enumerate(knowledge_graph.communities[:5]):  # 상위 5개만
                    community_nodes = [
                        n.title for n in knowledge_graph.nodes if n.id in community
                    ][:3]
                    print(f"   커뮤니티 {i+1}: {len(community)}개 노드")
                    print(f"      - {', '.join(community_nodes)}...")
            
            # 파일 저장
            if not output_file:
                output_file = "knowledge_graph.json"
            
            if self.graph_builder.export_graph(knowledge_graph, output_file):
                print(f"\n💾 그래프 저장: {output_file}")
            
            # 시각화
            if visualize:
                viz_file = output_file.replace('.json', '.png')
                if self.graph_builder.visualize_graph(knowledge_graph, viz_file):
                    print(f"📈 시각화 저장: {viz_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"지식 그래프 구축 실패: {e}")
            print(f"❌ 지식 그래프 구축 중 오류: {e}")
            return False
    
    def get_stats(self) -> bool:
        """시스템 통계"""
        try:
            print("📊 Vault Intelligence System V2 통계")
            print("=" * 60)
            
            # Vault 정보
            processor = VaultProcessor(str(self.vault_path))
            vault_stats = processor.get_vault_statistics()
            
            print(f"📁 Vault 정보:")
            print(f"   경로: {vault_stats['vault_path']}")
            print(f"   파일: {vault_stats['total_files']}개")
            print(f"   크기: {vault_stats['total_size_mb']}MB")
            
            # 캐시 정보
            cache = EmbeddingCache(str(self.cache_dir))
            cache_stats = cache.get_statistics()
            
            print(f"\n💾 캐시 정보:")
            print(f"   캐시된 임베딩: {cache_stats['total_embeddings']}개")
            print(f"   DB 크기: {cache_stats['db_size'] / (1024*1024):.2f}MB")
            
            # 모델 정보
            if self.search_engine and hasattr(self.search_engine, 'engine'):
                model_info = self.search_engine.engine.get_model_info()
                print(f"\n🤖 모델 정보:")
                print(f"   모델: {model_info['model_name']}")
                print(f"   차원: {model_info['embedding_dimension']}")
                print(f"   장치: {model_info['device']}")
            
            # 검색 엔진 정보
            if self.search_engine and self.search_engine.indexed:
                print(f"\n🔍 검색 엔진:")
                print(f"   인덱싱된 문서: {len(self.search_engine.documents)}개")
                print(f"   임베딩 형태: {self.search_engine.embeddings.shape}")
                print(f"   인덱스 상태: ✅ 구축됨")
            else:
                print(f"\n🔍 검색 엔진:")
                print(f"   인덱스 상태: ❌ 미구축")
            
            # 설정 정보
            print(f"\n⚙️ 현재 설정:")
            print(f"   검색 임계값: {self.config['search']['similarity_threshold']}")
            print(f"   중복 임계값: {self.config['duplicates']['similarity_threshold']}")
            print(f"   기본 클러스터: {self.config['clustering']['default_n_clusters']}개")
            
            return True
            
        except Exception as e:
            logger.error(f"통계 조회 실패: {e}")
            print(f"❌ 통계 조회 중 오류: {e}")
            return False
    
    def _save_search_results(self, results, query: str, output_file: str):
        """검색 결과 저장"""
        try:
            content = f"""---
tags:
  - vault-intelligence/search-results
  - search/{query.lower().replace(' ', '-')}
generated: {datetime.now().isoformat()}
query: "{query}"
---

# "{query}" 검색 결과

생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
검색된 문서: {len(results)}개

## 문서 목록

"""
            
            for result in results:
                content += f"### {result.rank}. [[{result.document.path}]]\n\n"
                content += f"- **제목**: {result.document.title}\n"
                content += f"- **유사도**: {result.similarity_score:.4f} ({result.match_type})\n"
                content += f"- **단어 수**: {result.document.word_count}\n"
                
                if result.document.tags:
                    content += f"- **태그**: {', '.join(result.document.tags)}\n"
                
                if result.matched_keywords:
                    content += f"- **매칭 키워드**: {', '.join(result.matched_keywords)}\n"
                
                if result.snippet:
                    content += f"- **미리보기**: {result.snippet}\n"
                
                content += "\n"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
        except Exception as e:
            logger.error(f"검색 결과 저장 실패: {e}")
    
    def _print_index_stats(self):
        """인덱스 통계 출력"""
        try:
            if self.search_engine and self.search_engine.indexed:
                stats = self.search_engine.get_search_statistics()
                print(f"📊 인덱스 통계:")
                print(f"   문서: {stats['indexed_documents']}개")
                print(f"   임베딩 차원: {stats['embedding_dimension']}")
                print(f"   모델: {stats['model_name']}")
        except:
            pass


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="Vault Intelligence System V2 - Sentence Transformers 기반 지능형 Vault 관리"
    )
    
    # 공통 인자
    parser.add_argument(
        "--vault-path",
        default="/Users/msbaek/DocumentsLocal/msbaek_vault",
        help="Vault 경로"
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
    
    # 서브커맨드
    subparsers = parser.add_subparsers(dest="command", help="사용 가능한 명령어")
    
    # index 명령
    index_parser = subparsers.add_parser("index", help="검색 인덱스 구축")
    index_parser.add_argument("--force", action="store_true", help="강제 재구축")
    
    # search 명령
    search_parser = subparsers.add_parser("search", help="문서 검색")
    search_parser.add_argument("query", help="검색 쿼리")
    search_parser.add_argument("--type", choices=["semantic", "keyword", "hybrid"], 
                              default="hybrid", help="검색 타입")
    search_parser.add_argument("--top-k", type=int, help="결과 개수")
    search_parser.add_argument("--threshold", type=float, help="유사도 임계값")
    search_parser.add_argument("--output", help="결과 저장 파일")
    
    # duplicates 명령
    dup_parser = subparsers.add_parser("duplicates", help="중복 문서 감지")
    dup_parser.add_argument("--threshold", type=float, help="유사도 임계값")
    dup_parser.add_argument("--min-words", type=int, help="최소 단어 수")
    dup_parser.add_argument("--output", help="결과 저장 파일")
    
    # analyze 명령
    analyze_parser = subparsers.add_parser("analyze", help="주제 분석")
    analyze_parser.add_argument("topic", nargs="?", help="분석할 주제 (선택사항)")
    analyze_parser.add_argument("--clusters", type=int, help="클러스터 수")
    analyze_parser.add_argument("--algorithm", choices=["kmeans", "dbscan", "hierarchical"], help="클러스터링 알고리즘")
    analyze_parser.add_argument("--output", help="결과 저장 파일")
    analyze_parser.add_argument("--visualize", action="store_true", help="시각화 생성")
    
    # collect 명령
    collect_parser = subparsers.add_parser("collect", help="주제별 문서 수집")
    collect_parser.add_argument("topic", help="수집할 주제")
    collect_parser.add_argument("--top-k", type=int, help="최대 문서 수")
    collect_parser.add_argument("--threshold", type=float, help="유사도 임계값")
    collect_parser.add_argument("--output", help="결과 저장 파일")
    collect_parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="출력 형식")
    
    # graph 명령
    graph_parser = subparsers.add_parser("graph", help="지식 그래프 구축")
    graph_parser.add_argument("--threshold", type=float, help="유사도 임계값")
    graph_parser.add_argument("--no-tags", action="store_true", help="태그 노드 제외")
    graph_parser.add_argument("--output", help="결과 저장 파일")
    graph_parser.add_argument("--visualize", action="store_true", help="시각화 생성")
    
    # stats 명령
    subparsers.add_parser("stats", help="시스템 통계")
    
    # 인자 파싱
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # VaultAssistant 초기화
    try:
        assistant = VaultAssistant(args.vault_path, args.config)
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        sys.exit(1)
    
    # 명령어 실행
    success = True
    
    if args.command == "index":
        success = assistant.build_index(args.force)
    
    elif args.command == "search":
        success = assistant.search(
            args.query, args.top_k, args.type, args.threshold, args.output
        )
    
    elif args.command == "duplicates":
        success = assistant.find_duplicates(
            args.threshold, args.min_words, args.output
        )
    
    elif args.command == "analyze":
        success = assistant.analyze_topics(
            args.topic, args.clusters, args.algorithm, args.output, args.visualize
        )
    
    elif args.command == "collect":
        success = assistant.collect_topic(
            args.topic, args.top_k, args.threshold, args.output, args.format
        )
    
    elif args.command == "graph":
        success = assistant.build_graph(
            args.threshold, not args.no_tags, args.output, args.visualize
        )
    
    elif args.command == "stats":
        success = assistant.get_stats()
    
    else:
        parser.print_help()
        success = False
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()