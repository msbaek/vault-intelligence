#!/usr/bin/env python3
"""TOP 30 핵심 기법을 Obsidian 노트로 생성하는 스크립트"""

import json
from pathlib import Path
from datetime import datetime

# 경로 설정
JSON_PATH = Path(__file__).parent / "ai-techniques-deduplicated.json"
OUTPUT_DIR = Path.home() / "DocumentsLocal/msbaek_vault/003-RESOURCES/AI/AI-Practice-Techniques/techniques"

# 카테고리별 태그 매핑
CATEGORY_TAGS = {
    "AI-Assisted Development": "ai/practice/development",
    "Prompt Engineering": "ai/practice/prompt-engineering",
    "Agent & Workflow": "ai/practice/agent",
    "Tools & Integration": "ai/practice/tools",
    "Quality & Security": "ai/practice/quality",
    "Learning & Mindset": "ai/practice/learning"
}

def load_techniques():
    """JSON에서 기법 로드"""
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['techniques']

def select_top_30(techniques):
    """출처 수 기준 TOP 30 선정"""
    # sources 배열 길이로 정렬 (여러 출처에서 언급된 기법이 더 중요)
    sorted_techniques = sorted(
        techniques,
        key=lambda t: len(t.get('sources', [])),
        reverse=True
    )
    return sorted_techniques[:30]

def sanitize_filename(name):
    """파일명에 안전한 문자열로 변환"""
    # 특수문자 제거 및 공백을 하이픈으로
    safe_chars = []
    for c in name.lower():
        if c.isalnum() or c in ' -_':
            safe_chars.append(c)
        elif c in '()[]':
            continue
        else:
            safe_chars.append(' ')

    result = ''.join(safe_chars)
    result = '-'.join(result.split())  # 연속 공백 처리
    return result[:50]  # 최대 50자

def generate_note(technique, rank):
    """단일 기법에 대한 Obsidian 노트 생성"""
    name = technique['name']
    description = technique.get('description', '')
    category = technique.get('category', 'AI-Assisted Development')
    tools = technique.get('tools', [])
    sources = technique.get('sources', [])
    examples = technique.get('examples', [])
    conditions = technique.get('conditions', '')
    cautions = technique.get('cautions', '')
    insights = technique.get('insights', [])

    # 태그 구성
    tags = [
        CATEGORY_TAGS.get(category, "ai/practice"),
        "type/technique",
        "status/permanent"
    ]

    # 도구별 태그 추가
    tool_tag_map = {
        "Claude": "tools/claude",
        "Claude Code": "tools/claude-code",
        "ChatGPT": "tools/chatgpt",
        "Cursor": "tools/cursor",
        "GitHub Copilot": "tools/copilot",
        "GitHub": "tools/github"
    }
    for tool in tools:
        if tool in tool_tag_map:
            tags.append(tool_tag_map[tool])

    tags_yaml = "\n  - ".join(tags)
    tools_str = ", ".join(tools) if tools else "범용"
    sources_count = len(sources)

    # 관련 기법 링크 (같은 카테고리)
    related_link = f"[[{category.lower().replace(' ', '-').replace('&', 'and')}|{category}]]"

    note_content = f"""---
tags:
  - {tags_yaml}
created: {datetime.now().strftime('%Y-%m-%d')}
importance: {min(5, max(1, sources_count // 2))}
sources_count: {sources_count}
---

# {name}

> **핵심 기법 #{rank}** | 카테고리: {related_link} | 출처: {sources_count}개 문서

## 📋 개요

{description}

## 🛠️ 관련 도구

{tools_str}

## ✅ 적용 조건

{conditions if conditions else "일반적인 AI 개발 작업에 적용 가능"}

"""

    # 예시가 있는 경우 추가
    if examples:
        note_content += "## 💡 실제 예시\n\n"
        for ex in examples:
            note_content += f"- {ex}\n"
        note_content += "\n"

    # 주의사항이 있는 경우 추가
    if cautions:
        note_content += f"""## ⚠️ 주의사항

{cautions}

"""

    # 인사이트가 있는 경우 추가
    if insights:
        note_content += "## 🔍 추가 인사이트\n\n"
        for insight in insights:
            note_content += f"- {insight}\n"
        note_content += "\n"

    # 관련 문서 링크
    note_content += f"""## 🔗 관련 문서

- [[_AI-Practice-MOC|AI 활용 기법 MOC]]
- [[{category.lower().replace(' ', '-').replace('&', 'and')}|{category} 카테고리]]

---

*출처 배치: {', '.join(sources[:5])}{"..." if len(sources) > 5 else ""}*
"""

    return note_content

def main():
    """메인 실행"""
    print("=" * 60)
    print("TOP 30 핵심 기법 Obsidian 노트 생성")
    print("=" * 60)

    # 출력 디렉토리 생성
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 기법 로드 및 TOP 30 선정
    techniques = load_techniques()
    top_30 = select_top_30(techniques)

    print(f"\n총 {len(techniques)}개 기법 중 TOP 30 선정 완료\n")

    # 각 기법에 대해 노트 생성
    created_files = []
    for rank, tech in enumerate(top_30, 1):
        filename = sanitize_filename(tech['name']) + ".md"
        filepath = OUTPUT_DIR / filename

        note_content = generate_note(tech, rank)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(note_content)

        sources_count = len(tech.get('sources', []))
        print(f"[{rank:2d}] {tech['name'][:40]:<40} (출처: {sources_count}개)")
        created_files.append(filepath)

    print(f"\n✅ {len(created_files)}개 노트 생성 완료")
    print(f"📁 위치: {OUTPUT_DIR}")

    # TOP 30 목록 출력
    print("\n" + "=" * 60)
    print("TOP 30 핵심 기법 목록")
    print("=" * 60)
    for rank, tech in enumerate(top_30, 1):
        category = tech.get('category', 'N/A')[:20]
        print(f"{rank:2d}. [{category}] {tech['name']}")

if __name__ == "__main__":
    main()
