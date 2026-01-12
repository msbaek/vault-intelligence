#!/usr/bin/env python3
"""
AI Practice Category Documents Generator
=========================================
6개 카테고리별 심층 분석 문서를 생성합니다.
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def load_techniques(json_path: Path) -> dict:
    """JSON에서 기법 데이터 로드"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_category_document(category: str, techniques: list, output_path: Path, total_count: int):
    """카테고리별 심층 분석 문서 생성"""

    # 카테고리별 설명
    category_descriptions = {
        'AI-Assisted Development': """
AI 도구를 활용한 개발 방법론입니다. TDD+AI, Spec-Driven Development, Vibe Coding 등
AI와 함께 코드를 작성하고 검증하는 실천적 기법들을 다룹니다.
""",
        'Prompt Engineering': """
효과적인 프롬프트 작성 기법입니다. STICC, CTA, Few-shot 등 다양한 프롬프팅 패턴과
컨텍스트 엔지니어링 기법을 포함합니다.
""",
        'Agent & Workflow': """
AI 에이전트와 워크플로우 자동화 기법입니다. 서브에이전트 활용, 병렬 처리,
Human-in-the-Loop 패턴 등을 다룹니다.
""",
        'Tools & Integration': """
MCP, Claude Code, Cursor 등 AI 도구의 효과적인 활용법입니다.
도구 설정, 통합, 확장에 관한 기법들을 포함합니다.
""",
        'Quality & Security': """
AI 생성 코드의 품질 보장과 보안 기법입니다. 코드 리뷰, 테스트 자동화,
보안 취약점 검증 등을 다룹니다.
""",
        'Learning & Mindset': """
AI 시대의 학습 방법과 마인드셋입니다. 역량 개발, 팀 협업,
AI 활용 문화 구축에 관한 기법들을 포함합니다.
"""
    }

    # 카테고리별 관련 도구
    category_tools = {
        'AI-Assisted Development': ['Claude Code', 'Cursor', 'GitHub Copilot', 'Jest', 'pytest'],
        'Prompt Engineering': ['ChatGPT', 'Claude', 'Cursor', 'LangChain'],
        'Agent & Workflow': ['Claude Code', 'Cursor', 'LangGraph', 'CrewAI'],
        'Tools & Integration': ['MCP', 'Claude Code', 'Cursor', 'VS Code', 'IDE'],
        'Quality & Security': ['SonarQube', 'ESLint', 'OWASP', 'Snyk'],
        'Learning & Mindset': ['Notion', 'Obsidian', 'Documentation Tools']
    }

    # 기법들을 출처 수로 정렬
    techniques_sorted = sorted(techniques, key=lambda x: len(x.get('sources', [])), reverse=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        # 헤더
        f.write(f"# {category} 심층 분석\n\n")
        f.write(f"**생성일**: {datetime.now().strftime('%Y-%m-%d')}\n")
        f.write(f"**기법 수**: {len(techniques)}개\n")
        f.write(f"**전체 비율**: {len(techniques) / total_count * 100:.1f}%\n\n")

        # 개요
        f.write("## 개요\n\n")
        f.write(category_descriptions.get(category, "").strip())
        f.write("\n\n")

        f.write("---\n\n")

        # 핵심 기법 TOP 10
        f.write("## 핵심 기법 TOP 10\n\n")
        top_10 = techniques_sorted[:10]
        f.write("| # | 기법명 | 출처 수 | 주요 도구 |\n")
        f.write("|---|--------|--------|----------|\n")
        for i, t in enumerate(top_10, 1):
            name = t['name'][:35] + "..." if len(t['name']) > 35 else t['name']
            tools = ', '.join(t.get('tools', [])[:2]) or '-'
            f.write(f"| {i} | {name} | {len(t.get('sources', []))} | {tools} |\n")
        f.write("\n")

        # 기법 관계도 (Mermaid)
        f.write("## 기법 관계도\n\n")
        f.write("```mermaid\nmindmap\n")
        f.write(f"  root(({category[:20]}))\n")

        # 상위 기법들을 그룹화
        groups = defaultdict(list)
        for t in techniques_sorted[:20]:
            # 간단한 키워드 기반 그룹화
            name_lower = t['name'].lower()
            if any(kw in name_lower for kw in ['tdd', 'test', '테스트']):
                groups['테스트 기반'].append(t['name'][:20])
            elif any(kw in name_lower for kw in ['prompt', '프롬프트']):
                groups['프롬프트 기법'].append(t['name'][:20])
            elif any(kw in name_lower for kw in ['agent', '에이전트']):
                groups['에이전트 활용'].append(t['name'][:20])
            elif any(kw in name_lower for kw in ['mcp', 'tool', '도구']):
                groups['도구 통합'].append(t['name'][:20])
            elif any(kw in name_lower for kw in ['spec', '명세', 'document']):
                groups['명세 기반'].append(t['name'][:20])
            else:
                groups['기타'].append(t['name'][:20])

        for group_name, items in list(groups.items())[:5]:
            f.write(f"    {group_name}\n")
            for item in items[:3]:
                f.write(f"      {item}\n")
        f.write("```\n\n")

        # 실무 적용 체크리스트
        f.write("## 실무 적용 체크리스트\n\n")

        checklists = {
            'AI-Assisted Development': [
                "[ ] CLAUDE.md 파일에 프로젝트 규칙 정의",
                "[ ] TDD 사이클에 AI 통합 (Red: 개발자, Green/Blue: AI)",
                "[ ] Spec-First 접근법 적용 (코드 전 명세 작성)",
                "[ ] AI 생성 코드 리뷰 프로세스 수립",
                "[ ] 테스트 커버리지 목표 설정 및 모니터링"
            ],
            'Prompt Engineering': [
                "[ ] STICC 또는 CTA 프레임워크 적용",
                "[ ] 컨텍스트 엔지니어링 가이드라인 수립",
                "[ ] 프롬프트 라이브러리 구축",
                "[ ] 불확실성 지도(Uncertainty Map) 활용",
                "[ ] 메타 프롬프트로 프롬프트 품질 개선"
            ],
            'Agent & Workflow': [
                "[ ] 서브에이전트 역할 분리 정의",
                "[ ] Human-in-the-Loop 체크포인트 설정",
                "[ ] 병렬 처리 워크플로우 구성",
                "[ ] 에이전트 모니터링 대시보드 구축",
                "[ ] 롤백 전략 수립"
            ],
            'Tools & Integration': [
                "[ ] 필수 MCP 서버 선별 및 연결",
                "[ ] IDE 통합 설정 최적화",
                "[ ] 토큰 사용량 모니터링",
                "[ ] 도구 간 워크플로우 자동화",
                "[ ] 정기적 도구 업데이트 및 평가"
            ],
            'Quality & Security': [
                "[ ] AI 생성 코드 보안 리뷰 필수화",
                "[ ] 자동화된 품질 게이트 설정",
                "[ ] 의존성 승인 워크플로우 구축",
                "[ ] 정기 보안 감사 일정 수립",
                "[ ] 시니어 검토 프로세스 의무화"
            ],
            'Learning & Mindset': [
                "[ ] 팀 AI 활용 가이드라인 수립",
                "[ ] 정기 AI 도구 교육 일정 수립",
                "[ ] 베스트 프랙티스 공유 채널 운영",
                "[ ] 학습 시간 할당",
                "[ ] 실험 문화 장려"
            ]
        }

        for item in checklists.get(category, ["[ ] 체크리스트 항목 추가 필요"]):
            f.write(f"- {item}\n")
        f.write("\n")

        # 학습 경로
        f.write("## 학습 경로\n\n")

        f.write("### 입문 (1-2주)\n\n")
        for t in techniques_sorted[:5]:
            f.write(f"- **{t['name']}**: {t.get('description', '')[:80]}...\n")
        f.write("\n")

        f.write("### 중급 (3-4주)\n\n")
        for t in techniques_sorted[5:10]:
            f.write(f"- **{t['name']}**: {t.get('description', '')[:80]}...\n")
        f.write("\n")

        f.write("### 고급 (5주+)\n\n")
        for t in techniques_sorted[10:15]:
            f.write(f"- **{t['name']}**: {t.get('description', '')[:80]}...\n")
        f.write("\n")

        f.write("---\n\n")

        # 관련 도구
        f.write("## 관련 도구\n\n")
        for tool in category_tools.get(category, []):
            f.write(f"- {tool}\n")
        f.write("\n")

        # 전체 기법 목록
        f.write("## 전체 기법 목록\n\n")
        f.write(f"<details>\n<summary>{len(techniques)}개 기법 펼치기</summary>\n\n")
        for i, t in enumerate(techniques_sorted, 1):
            f.write(f"{i}. **{t['name']}**: {t.get('description', '')[:100]}\n")
        f.write("\n</details>\n")

    print(f"  생성: {output_path.name}")

def main():
    base_path = Path(__file__).parent
    json_path = base_path / "ai-techniques-deduplicated.json"
    output_dir = base_path / "categories"
    output_dir.mkdir(exist_ok=True)

    print("AI Practice Category Documents Generator")
    print("=" * 50)

    data = load_techniques(json_path)
    techniques = data['techniques']
    total_count = data['total_deduplicated']

    # 카테고리별 분류
    by_category = defaultdict(list)
    for t in techniques:
        by_category[t['category']].append(t)

    # 파일명 매핑
    category_files = {
        'AI-Assisted Development': 'category-01-ai-assisted-development.md',
        'Prompt Engineering': 'category-02-prompt-engineering.md',
        'Agent & Workflow': 'category-03-agent-workflow.md',
        'Tools & Integration': 'category-04-tools-integration.md',
        'Quality & Security': 'category-05-quality-security.md',
        'Learning & Mindset': 'category-06-learning-mindset.md'
    }

    for category, filename in category_files.items():
        if category in by_category:
            output_path = output_dir / filename
            generate_category_document(category, by_category[category], output_path, total_count)

    print(f"\n완료! {len(category_files)}개 카테고리 문서 생성됨")

if __name__ == "__main__":
    main()
