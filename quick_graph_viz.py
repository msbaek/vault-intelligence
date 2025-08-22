#!/usr/bin/env python3
"""
간단한 지식 그래프 시각화 - 매우 작은 샘플
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.features.knowledge_graph import test_knowledge_graph

def main():
    print("🕸️ 테스트용 지식 그래프 시각화...")
    
    # 테스트 함수 실행 (임시 vault와 샘플 문서 사용)
    success = test_knowledge_graph()
    
    if success:
        print("\n✅ 테스트용 지식 그래프 시각화 완료!")
        print("📁 생성된 파일들을 확인해보세요:")
        print("  - knowledge_graph.json (그래프 데이터)")
        print("  - knowledge_graph.png (시각화, matplotlib 있는 경우)")
    else:
        print("❌ 시각화 실패")

if __name__ == "__main__":
    main()