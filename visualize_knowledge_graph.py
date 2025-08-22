#!/usr/bin/env python3
"""
지식 그래프 시각화 스크립트 - 캐시된 임베딩 활용
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.features.knowledge_graph import KnowledgeGraphBuilder
from src.features.advanced_search import AdvancedSearchEngine
import yaml
import numpy as np

def main():
    print("🕸️ 지식 그래프 시각화 시작...")
    
    # 설정 로드
    with open('config/settings.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Vault 경로
    vault_path = "/Users/msbaek/DocumentsLocal/msbaek_vault"
    cache_dir = "cache"
    
    # 검색 엔진 초기화
    print("🔍 검색 엔진 초기화 중...")
    engine = AdvancedSearchEngine(vault_path, cache_dir, config)
    
    # 캐시에서 임베딩 로드 (재인덱싱 하지 않음)
    print("📊 캐시에서 임베딩 로드 중...")
    
    # 캐시에서 직접 로드
    from src.core.vault_processor import VaultProcessor
    processor = VaultProcessor(vault_path, config)
    documents = processor.process_all_files()
    
    print(f"📁 총 {len(documents)}개 문서 로드")
    
    # 캐시에서 임베딩 로드
    loaded_count = 0
    for doc in documents[:100]:  # 처음 100개만 시각화용으로 사용
        embedding = engine.cache.get_embedding(doc.path)
        if embedding is not None:
            doc.embedding = embedding
            loaded_count += 1
    
    print(f"✅ {loaded_count}개 문서 임베딩 로드 완료")
    
    # 사용할 문서만 필터링
    valid_docs = [doc for doc in documents[:100] if doc.embedding is not None]
    print(f"📊 시각화용 문서: {len(valid_docs)}개")
    
    if len(valid_docs) < 2:
        print("❌ 시각화할 충분한 문서가 없습니다.")
        return
    
    # engine의 문서 설정
    engine.documents = valid_docs
    engine.indexed = True
    
    # 지식 그래프 구축기 초기화
    graph_builder = KnowledgeGraphBuilder(engine, config)
    
    # 지식 그래프 구축
    print("\n🕸️ 지식 그래프 구축 중...")
    knowledge_graph = graph_builder.build_graph(
        documents=valid_docs,
        similarity_threshold=0.5,  # 적절한 연결 수를 위해 조정
        include_tag_nodes=True
    )
    
    print(f"\n📊 지식 그래프 결과:")
    print(f"- 노드: {knowledge_graph.get_node_count()}개")
    print(f"- 엣지: {knowledge_graph.get_edge_count()}개")
    print(f"- 밀도: {knowledge_graph.get_density():.3f}")
    
    if knowledge_graph.get_node_count() == 0:
        print("❌ 그래프 노드가 없습니다.")
        return
    
    # 시각화 생성
    output_file = "knowledge_graph.png"
    print(f"\n📈 시각화 생성 중...")
    
    if graph_builder.visualize_graph(
        knowledge_graph, 
        output_file=output_file,
        layout='spring',
        node_size_attr='word_count',
        show_labels=True
    ):
        print(f"✅ 시각화 완료: {output_file}")
    else:
        print(f"❌ 시각화 실패 (matplotlib/networkx 필요)")
    
    # JSON 내보내기
    json_file = "knowledge_graph.json"
    if graph_builder.export_graph(knowledge_graph, json_file):
        print(f"💾 그래프 데이터 저장: {json_file}")
    
    # 상세 정보 출력
    if knowledge_graph.centrality_scores:
        print(f"\n🎯 높은 중심성 점수 노드 (상위 5개):")
        sorted_centrality = sorted(
            knowledge_graph.centrality_scores.items(), 
            key=lambda x: x[1], reverse=True
        )[:5]
        
        for node_id, score in sorted_centrality:
            node = next((n for n in knowledge_graph.nodes if n.id == node_id), None)
            if node:
                title = node.title[:40] + "..." if len(node.title) > 40 else node.title
                print(f"  - {title} ({node.node_type}): {score:.3f}")
    
    # 엣지 타입별 통계
    edge_types = {}
    for edge in knowledge_graph.edges:
        edge_types[edge.relationship_type] = edge_types.get(edge.relationship_type, 0) + 1
    
    if edge_types:
        print(f"\n🔗 엣지 타입별 분포:")
        for edge_type, count in edge_types.items():
            print(f"  - {edge_type}: {count}개")
    
    print("\n🎉 지식 그래프 시각화 완료!")
    print(f"📁 생성된 파일:")
    print(f"  - {output_file} (그래프 시각화)")
    print(f"  - {json_file} (그래프 데이터)")

if __name__ == "__main__":
    main()