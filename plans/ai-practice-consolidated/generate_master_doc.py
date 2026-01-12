#!/usr/bin/env python3
"""
AI Practice Master Document Generator
======================================
중복 제거된 기법 데이터를 기반으로 마스터 문서를 생성합니다.
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def load_techniques(json_path: Path) -> dict:
    """JSON에서 기법 데이터 로드"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_master_document(data: dict, output_path: Path):
    """마스터 문서 생성"""
    techniques = data['techniques']

    # 카테고리별 분류
    by_category = defaultdict(list)
    for t in techniques:
        by_category[t['category']].append(t)

    # 카테고리 순서 (비율 높은 순)
    category_order = [
        'AI-Assisted Development',
        'Prompt Engineering',
        'Agent & Workflow',
        'Tools & Integration',
        'Quality & Security',
        'Learning & Mindset'
    ]

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# AI 활용 기법 마스터 문서\n\n")
        f.write(f"**생성일**: {datetime.now().strftime('%Y-%m-%d')}\n")
        f.write(f"**원본 문서**: 286개 (29 배치)\n")
        f.write(f"**추출 기법**: {data['total_extracted']:,}개\n")
        f.write(f"**중복 제거 후**: {data['total_deduplicated']:,}개\n\n")

        f.write("---\n\n")

        # 개요
        f.write("## 개요\n\n")
        f.write("이 문서는 AI 활용 관련 286개 문서에서 추출된 기법들을 통합하고 정리한 마스터 문서입니다.\n")
        f.write("중복을 제거하고 6개 카테고리로 분류하여 실무에서 활용할 수 있도록 구성했습니다.\n\n")

        # 통계 요약
        f.write("## 통계 요약\n\n")
        f.write("| 카테고리 | 기법 수 | 비율 |\n")
        f.write("|----------|--------|------|\n")
        for cat in category_order:
            if cat in by_category:
                count = len(by_category[cat])
                ratio = count / data['total_deduplicated'] * 100
                f.write(f"| {cat} | {count} | {ratio:.1f}% |\n")
        f.write(f"| **합계** | **{data['total_deduplicated']}** | **100%** |\n\n")

        # 카테고리별 분포 차트 (텍스트 기반)
        f.write("### 분포 시각화\n\n")
        f.write("```\n")
        max_bar = 50
        max_count = max(len(by_category[cat]) for cat in category_order if cat in by_category)
        for cat in category_order:
            if cat in by_category:
                count = len(by_category[cat])
                bar_len = int(count / max_count * max_bar)
                f.write(f"{cat[:25]:<25} {'█' * bar_len} {count}\n")
        f.write("```\n\n")

        f.write("---\n\n")

        # 카테고리별 기법 목록
        f.write("## 카테고리별 기법 목록\n\n")

        for cat in category_order:
            if cat not in by_category:
                continue

            techs = by_category[cat]
            f.write(f"### {cat} ({len(techs)}개)\n\n")

            # 출처가 많은 순으로 정렬 (중요도 추정)
            techs_sorted = sorted(techs, key=lambda x: len(x.get('sources', [])), reverse=True)

            for i, t in enumerate(techs_sorted, 1):
                name = t['name'].title() if t['name'].islower() else t['name']
                f.write(f"#### {i}. {name}\n\n")

                if t.get('description'):
                    f.write(f"**설명**: {t['description']}\n\n")

                if t.get('tools') and len(t['tools']) > 0:
                    tools_str = ', '.join(t['tools'][:5])
                    f.write(f"**관련 도구**: {tools_str}\n\n")

                if t.get('conditions'):
                    f.write(f"**적용 조건**: {t['conditions']}\n\n")

                if t.get('examples') and len(t['examples']) > 0:
                    f.write(f"**예시**: {t['examples'][0]}\n\n")

                if t.get('sources') and len(t['sources']) > 1:
                    f.write(f"*출처: {len(t['sources'])}개 문서*\n\n")

                f.write("---\n\n")

        # TOP 30 핵심 기법
        f.write("## TOP 30 핵심 기법\n\n")
        f.write("출처 문서가 많은 순으로 선정한 핵심 기법입니다.\n\n")

        all_techs_sorted = sorted(techniques, key=lambda x: len(x.get('sources', [])), reverse=True)[:30]

        f.write("| # | 기법명 | 카테고리 | 출처 수 |\n")
        f.write("|---|--------|----------|--------|\n")
        for i, t in enumerate(all_techs_sorted, 1):
            name = t['name'][:40] + "..." if len(t['name']) > 40 else t['name']
            f.write(f"| {i} | {name} | {t['category']} | {len(t.get('sources', []))} |\n")

        f.write("\n---\n\n")

        # 주요 도구별 기법
        f.write("## 주요 도구별 기법\n\n")

        tool_map = defaultdict(list)
        for t in techniques:
            for tool in t.get('tools', []):
                tool_clean = tool.strip().lower()
                if len(tool_clean) > 2:
                    tool_map[tool_clean].append(t['name'])

        # 상위 10개 도구
        top_tools = sorted(tool_map.items(), key=lambda x: len(x[1]), reverse=True)[:10]

        f.write("| 도구 | 관련 기법 수 |\n")
        f.write("|------|------------|\n")
        for tool, techs in top_tools:
            f.write(f"| {tool.title()} | {len(techs)} |\n")

        f.write("\n")

    print(f"마스터 문서 생성 완료: {output_path}")

def main():
    base_path = Path(__file__).parent
    json_path = base_path / "ai-techniques-deduplicated.json"
    output_path = base_path / "AI-Practice-Master.md"

    print("AI Practice Master Document Generator")
    print("=" * 50)

    data = load_techniques(json_path)
    print(f"로드된 기법: {data['total_deduplicated']}개")

    generate_master_document(data, output_path)

if __name__ == "__main__":
    main()
