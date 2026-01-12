#!/usr/bin/env python3
"""
AI Practice Techniques Deduplication Script
===========================================
29개 배치 파일에서 기법을 추출하고 중복을 제거합니다.

기준:
- 기법명 유사도 (Levenshtein distance < 3)
- 설명 의미적 유사도 (키워드 기반, Jaccard > 0.5)

병합 규칙:
- 가장 상세한 설명 선택
- 출처 문서 누적
- 관련 도구 합집합
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional
from collections import defaultdict
import difflib

@dataclass
class Technique:
    """AI 활용 기법 데이터 클래스"""
    name: str
    description: str
    category: str = ""
    tools: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    conditions: str = ""
    cautions: str = ""
    insights: List[str] = field(default_factory=list)
    batch_id: int = 0

def normalize_name(name: str) -> str:
    """기법명 정규화"""
    # 숫자, 특수문자 제거, 소문자 변환
    name = re.sub(r'^(기법\s*\d+[:\.]\s*|###?\s*기법\s*\d+[:\.]\s*)', '', name)
    name = re.sub(r'^\d+\.\s*', '', name)
    name = re.sub(r'\*\*', '', name)
    name = name.strip()
    return name.lower()

def is_valid_technique_name(name: str) -> bool:
    """유효한 기법명인지 확인 (메타데이터 레이블 제외)"""
    # 메타데이터 레이블 필터
    invalid_names = {
        '적용 조건', '관련 도구', '주의사항', '카테고리', '상세 설명', '적용 예시',
        '적용 시나리오', '적용 상황', '적용 방법', '예시', '도구', '설명',
        '핵심 인사이트', '참고 인사이트', '핵심 기법', '주요 기법',
        '요약', '배경', '개요', '결론', '결과', '문서명', '출처',
        '파일', '해당 없음', '통계', '비고', '완료 문서', '병렬 처리', '비용 모니터링',
        'applicable conditions', 'related tools', 'cautions', 'category', 'description',
        'example', 'scenario', 'insights',
    }

    name_lower = name.lower().strip()

    # 정확히 일치하는 메타데이터 레이블
    if name_lower in invalid_names:
        return False

    # 패턴 필터
    invalid_patterns = [
        r'^주요 기법\s*\(\d+개\)',  # 주요 기법 (N개)
        r'^추출된 기법\s*\(\d+개\)',  # 추출된 기법 (N개)
        r'^기법\s*\d+',  # 기법 1, 기법 2 등
        r'^문서\s*\d+',  # 문서 1, 문서 2 등
        r'^\d+개\s*기법',  # N개 기법
        r'^batch\s*\d+',  # Batch N
        r'^파일\s*\d+',  # 파일 N
    ]

    for pattern in invalid_patterns:
        if re.match(pattern, name_lower):
            return False

    # 너무 짧거나 일반적인 이름
    if len(name_lower) < 3:
        return False

    return True

def extract_keywords(text: str) -> Set[str]:
    """텍스트에서 키워드 추출"""
    # 한글, 영어, 숫자만 유지
    words = re.findall(r'[가-힣a-zA-Z0-9]+', text.lower())
    # 불용어 제거
    stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'to', 'of', 'and', 'or',
                 '및', '등', '을', '를', '이', '가', '에', '의', '로', '으로', '에서', '한다',
                 '하는', '하기', '위해', '통해', '대한', '위한'}
    return {w for w in words if len(w) > 1 and w not in stopwords}

def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """Jaccard 유사도 계산"""
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0

def levenshtein_distance(s1: str, s2: str) -> int:
    """Levenshtein 거리 계산"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def parse_batch_file(filepath: Path) -> List[Technique]:
    """배치 파일에서 기법 추출 (다양한 형식 지원)"""
    techniques = []
    content = filepath.read_text(encoding='utf-8')

    # 배치 ID 추출
    batch_match = re.search(r'batch-(\d+)', filepath.name)
    batch_id = int(batch_match.group(1)) if batch_match else 0

    # 형식 1: ### 기법 1: 이름 (Batch 01 스타일)
    pattern1 = r'###\s*기법\s*\d+[:\.]\s*\*?\*?([^*\n]+)\*?\*?\n([\s\S]*?)(?=###\s*기법|\n##\s|\n---|\Z)'
    for match in re.findall(pattern1, content, re.MULTILINE):
        technique = parse_technique_block(match[0], match[1], filepath.stem, batch_id)
        if technique:
            techniques.append(technique)

    # 형식 2: 1. **이름**: 설명 (카테고리: **카테고리명**) - 한 줄 형식 (Batch 03 스타일)
    pattern2 = r'^\d+\.\s*\*\*([^*]+)\*\*[:：]\s*([^\n]+(?:\([카카테테고고리리][：:][^\)]+\))?)'
    for match in re.findall(pattern2, content, re.MULTILINE):
        name = normalize_name(match[0])
        if not is_valid_technique_name(name):
            continue
        desc_full = match[1].strip()
        # 카테고리 추출
        cat_match = re.search(r'\(카테고리[:：]\s*\*?\*?([^*)]+)\*?\*?\)', desc_full)
        category = cat_match.group(1).strip() if cat_match else ""
        description = re.sub(r'\s*\(카테고리[:：][^\)]+\)', '', desc_full).strip()

        if name and len(name) >= 3 and description:
            technique = Technique(
                name=name,
                description=description,
                category=category,
                sources=[filepath.stem],
                batch_id=batch_id
            )
            techniques.append(technique)

    # 형식 3: #### 1. 이름 + 줄바꿈 + - **카테고리**: (Batch 11, 21 스타일)
    pattern3 = r'####\s*\d+\.\s*([^\n]+)\n([\s\S]*?)(?=####\s*\d+\.|\n###\s|\n##\s|\n---|\Z)'
    for match in re.findall(pattern3, content, re.MULTILINE):
        technique = parse_technique_block(match[0], match[1], filepath.stem, batch_id)
        if technique:
            techniques.append(technique)

    # 형식 4: **기법명**: 줄바꿈 + 설명
    pattern4 = r'^\*\*([^*\n]+)\*\*[:：]\s*\n([\s\S]*?)(?=^\*\*[^*]+\*\*[:：]|\n##\s|\n---|\Z)'
    for match in re.findall(pattern4, content, re.MULTILINE):
        technique = parse_technique_block(match[0], match[1], filepath.stem, batch_id)
        if technique:
            techniques.append(technique)

    # 형식 5: - **이름**: 설명 (목록 형식)
    pattern5 = r'^-\s*\*\*([^*:]+)\*\*[:：]\s*([^\n]+)'
    for match in re.findall(pattern5, content, re.MULTILINE):
        name = normalize_name(match[0])
        if not is_valid_technique_name(name):
            continue
        description = match[1].strip()
        if name and len(name) >= 3 and len(description) >= 10:
            technique = Technique(
                name=name,
                description=description,
                sources=[filepath.stem],
                batch_id=batch_id
            )
            techniques.append(technique)

    return techniques

def parse_technique_block(name_raw: str, body: str, source: str, batch_id: int) -> Optional[Technique]:
    """기법 블록 파싱"""
    name = normalize_name(name_raw)
    if not name or len(name) < 3:
        return None
    if not is_valid_technique_name(name):
        return None

    # 설명 추출
    desc_match = re.search(r'-?\s*\*?\*?설명\*?\*?[:：]\s*([^\n]+(?:\n[^-\n#][^\n]*)*)', body)
    description = desc_match.group(1).strip() if desc_match else ""
    if not description:
        # 첫 줄을 설명으로 사용
        lines = body.strip().split('\n')
        for line in lines:
            cleaned = re.sub(r'^[-*]\s*', '', line).strip()
            if cleaned and not cleaned.startswith('카테고리') and not cleaned.startswith('적용'):
                description = cleaned
                break

    if not description or len(description) < 5:
        return None

    # 카테고리 추출
    cat_match = re.search(r'-?\s*\*?\*?카테고리\*?\*?[:：]\s*([^\n]+)', body)
    category = cat_match.group(1).strip() if cat_match else ""

    # 도구 추출
    tools_match = re.search(r'-?\s*\*?\*?관련\s*도구\*?\*?[:：]\s*([^\n]+)', body)
    tools = []
    if tools_match:
        tools = [t.strip() for t in re.split(r'[,，、]', tools_match.group(1))]

    # 예시 추출
    example_match = re.search(r'-?\s*\*?\*?예시\*?\*?[:：]\s*([^\n]+)', body)
    examples = [example_match.group(1).strip()] if example_match else []

    # 적용 조건/상황 추출
    condition_match = re.search(r'-?\s*\*?\*?적용\s*(?:조건|시나리오|상황)\*?\*?[:：]\s*([^\n]+)', body)
    conditions = condition_match.group(1).strip() if condition_match else ""

    # 주의사항 추출
    caution_match = re.search(r'-?\s*\*?\*?주의사항\*?\*?[:：]\s*([^\n]+)', body)
    cautions = caution_match.group(1).strip() if caution_match else ""

    return Technique(
        name=name,
        description=description,
        category=category,
        tools=tools,
        examples=examples,
        conditions=conditions,
        cautions=cautions,
        sources=[source],
        batch_id=batch_id
    )

def find_duplicates(techniques: List[Technique], name_threshold: int = 5, desc_threshold: float = 0.4) -> List[List[int]]:
    """중복 기법 그룹 찾기"""
    n = len(techniques)
    visited = [False] * n
    groups = []

    # 기법명과 키워드 사전 생성
    name_map = {}
    keyword_map = {}
    for i, t in enumerate(techniques):
        norm_name = normalize_name(t.name)
        name_map[i] = norm_name
        keyword_map[i] = extract_keywords(t.name + " " + t.description)

    for i in range(n):
        if visited[i]:
            continue

        group = [i]
        visited[i] = True

        for j in range(i + 1, n):
            if visited[j]:
                continue

            # 기법명 유사도 체크
            name_dist = levenshtein_distance(name_map[i], name_map[j])
            name_similar = name_dist <= name_threshold or difflib.SequenceMatcher(None, name_map[i], name_map[j]).ratio() > 0.7

            # 설명 키워드 유사도 체크
            keyword_sim = jaccard_similarity(keyword_map[i], keyword_map[j])

            if name_similar or keyword_sim > desc_threshold:
                group.append(j)
                visited[j] = True

        if len(group) > 1:
            groups.append(group)

    return groups

def merge_techniques(techniques: List[Technique], indices: List[int]) -> Technique:
    """기법들을 하나로 병합"""
    selected = [techniques[i] for i in indices]

    # 가장 긴 설명을 가진 기법 선택
    best = max(selected, key=lambda t: len(t.description))

    # 모든 출처 합치기
    all_sources = []
    for t in selected:
        all_sources.extend(t.sources)

    # 모든 도구 합치기
    all_tools = []
    for t in selected:
        all_tools.extend(t.tools)
    all_tools = list(set(t.strip() for t in all_tools if t.strip()))

    # 모든 예시 합치기
    all_examples = []
    for t in selected:
        all_examples.extend(t.examples)
    all_examples = list(set(e.strip() for e in all_examples if e.strip()))

    # 조건과 주의사항 중 가장 긴 것 선택
    best_condition = max([t.conditions for t in selected], key=len, default="")
    best_caution = max([t.cautions for t in selected], key=len, default="")

    return Technique(
        name=best.name,
        description=best.description,
        category=best.category,
        tools=all_tools,
        sources=list(set(all_sources)),
        examples=all_examples[:5],  # 최대 5개
        conditions=best_condition,
        cautions=best_caution,
        batch_id=best.batch_id
    )

def categorize_technique(technique: Technique) -> str:
    """기법을 6개 카테고리로 분류"""
    name_lower = technique.name.lower()
    desc_lower = technique.description.lower()
    combined = name_lower + " " + desc_lower

    # 카테고리별 키워드
    categories = {
        "Prompt Engineering": ['프롬프트', 'prompt', 'sticc', 'cta', '컨텍스트', 'context', '질문', 'question',
                               '메타 프롬프트', 'template', '템플릿', 'few-shot', '되묻기', '불확실성'],
        "AI-Assisted Development": ['tdd', 'bdd', 'test', '테스트', 'red-green', 'spec', 'specification',
                                     '개발 방법론', 'vibe coding', '바이브', 'refactor', '리팩토링', 'clean code',
                                     'ddd', 'solid', 'clean architecture'],
        "Agent & Workflow": ['에이전트', 'agent', 'workflow', '워크플로우', '자동화', 'automation', 'pipeline',
                             '병렬', 'parallel', 'orchestr', 'subagent', 'hook'],
        "Quality & Security": ['품질', 'quality', '보안', 'security', '검증', 'validation', '리뷰', 'review',
                               'hallucination', '환각', '취약점', 'vulnerability', '오류', 'error', 'bug'],
        "Tools & Integration": ['mcp', 'cursor', 'claude code', 'copilot', 'tool', '도구', 'ide', 'plugin',
                                'serena', 'repomix', 'figma', 'github', 'git', '통합', 'integration'],
        "Learning & Mindset": ['학습', 'learn', '역량', 'skill', '마인드셋', 'mindset', '협업', 'collaboration',
                               '문화', 'culture', '교육', 'training', '멘토', 'mentor', '팀']
    }

    # 점수 계산
    scores = defaultdict(int)
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in combined:
                scores[category] += 1

    if scores:
        return max(scores, key=scores.get)
    return "AI-Assisted Development"  # 기본 카테고리

def main():
    base_path = Path(__file__).parent.parent / "ai-practice-results"
    output_path = Path(__file__).parent

    print("=" * 60)
    print("AI Practice Techniques Deduplication")
    print("=" * 60)

    # 1. 모든 배치 파일에서 기법 추출
    all_techniques = []
    batch_stats = {}

    for i in range(1, 30):
        batch_file = base_path / f"batch-{i:02d}-results.md"
        if batch_file.exists():
            techniques = parse_batch_file(batch_file)
            batch_stats[i] = len(techniques)
            all_techniques.extend(techniques)
            print(f"  Batch {i:02d}: {len(techniques)} 기법 추출")
        else:
            print(f"  Batch {i:02d}: 파일 없음")

    print(f"\n총 추출 기법: {len(all_techniques)}개")

    # 2. 중복 찾기
    print("\n중복 탐지 중...")
    duplicate_groups = find_duplicates(all_techniques)
    print(f"중복 그룹: {len(duplicate_groups)}개")

    # 3. 중복 병합 및 최종 목록 생성
    merged_indices = set()
    merged_techniques = []

    for group in duplicate_groups:
        merged = merge_techniques(all_techniques, group)
        merged.category = categorize_technique(merged)
        merged_techniques.append(merged)
        merged_indices.update(group)

    # 중복이 아닌 기법들 추가
    for i, technique in enumerate(all_techniques):
        if i not in merged_indices:
            technique.category = categorize_technique(technique)
            merged_techniques.append(technique)

    print(f"\n중복 제거 후 기법: {len(merged_techniques)}개")

    # 4. 카테고리별 통계
    category_stats = defaultdict(list)
    for t in merged_techniques:
        category_stats[t.category].append(t.name)

    print("\n카테고리별 분포:")
    for category in sorted(category_stats.keys()):
        print(f"  {category}: {len(category_stats[category])}개")

    # 5. JSON 저장
    json_output = output_path / "ai-techniques-deduplicated.json"
    with open(json_output, 'w', encoding='utf-8') as f:
        data = {
            "total_extracted": len(all_techniques),
            "total_deduplicated": len(merged_techniques),
            "duplicate_groups": len(duplicate_groups),
            "categories": {k: len(v) for k, v in category_stats.items()},
            "techniques": [asdict(t) for t in merged_techniques]
        }
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nJSON 저장: {json_output}")

    # 6. 리포트 생성
    report_path = output_path / "deduplication-report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# AI 활용 기법 중복 제거 리포트\n\n")
        f.write(f"**생성일**: 2026-01-04\n\n")

        f.write("## 요약\n\n")
        f.write(f"| 항목 | 값 |\n")
        f.write(f"|------|----|\n")
        f.write(f"| 원본 기법 수 | {len(all_techniques)} |\n")
        f.write(f"| 중복 제거 후 | {len(merged_techniques)} |\n")
        f.write(f"| 중복 그룹 수 | {len(duplicate_groups)} |\n")
        f.write(f"| 중복률 | {(len(all_techniques) - len(merged_techniques)) / len(all_techniques) * 100:.1f}% |\n\n")

        f.write("## 카테고리별 분포\n\n")
        f.write("| 카테고리 | 기법 수 | 비율 |\n")
        f.write("|----------|--------|------|\n")
        for category in sorted(category_stats.keys()):
            count = len(category_stats[category])
            ratio = count / len(merged_techniques) * 100
            f.write(f"| {category} | {count} | {ratio:.1f}% |\n")

        f.write("\n## 주요 중복 그룹 (상위 10개)\n\n")
        sorted_groups = sorted(duplicate_groups, key=lambda g: len(g), reverse=True)[:10]
        for i, group in enumerate(sorted_groups, 1):
            names = [all_techniques[idx].name for idx in group]
            f.write(f"### 그룹 {i} ({len(group)}개 병합)\n")
            for name in names:
                f.write(f"- {name}\n")
            f.write("\n")

        f.write("## 배치별 추출 통계\n\n")
        f.write("| Batch | 추출 기법 수 |\n")
        f.write("|-------|------------|\n")
        for batch_id in sorted(batch_stats.keys()):
            f.write(f"| Batch {batch_id:02d} | {batch_stats[batch_id]} |\n")

    print(f"리포트 저장: {report_path}")
    print("\n완료!")

if __name__ == "__main__":
    main()
