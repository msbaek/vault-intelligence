# YouTube 시리즈 기획안: "AI가 내 두 번째 뇌를 읽다"

## 개요

- **주제**: Claude Code + Vault Intelligence를 활용한 개인 지식 관리
- **타겟**: 한국 개발자 커뮤니티 (TDD/OOP/아키텍처 관심자)
- **형식**: 시리즈 4편 (각 10-15분)
- **Vault 규모**: 3,465개 문서

## 에피소드 구성

### 1편: "이걸 어떻게 찾았지?" - Vault Intelligence 첫인상 (10-12분)

**목적**: 첫 영상에서 시청자를 사로잡는 WOW 순간 제공

**구성**:
- 오프닝 (2분): 문제 제기 - 3,400개 노트에서 원하는 걸 찾는 어려움
- WOW 순간 4개 (각 2분):
  1. "kent beck이 전문가는 주니어와 다른 접근법을 취한다는 내용이 있는 문서를 찾아줘"
     → 기대 결과: The-Bet-On-Juniors-Just-Got-Better-Kent-Beck.md
  2. "kent beck이 AI로 코드 리뷰를 해서 피드백을 받을 수 있는데 왜 TDD, Refactoring을 배워야 한다는 질문에 답하는 내용이 있는 문서를 찾아줘"
     → 기대 결과: TDD-Theme & Variations.md (Q&A 섹션)
  3. "victor rentea가 split by unrelated complexity와 동일한 수준의 기법을 하나 더 말했는데 그 기법과 관련된 문서를 찾아줘"
     → 기대 결과: Test Driven Design Insights - 10 Hints You Were Missing By Victor Rentea.md
  4. "어떤 기관의 조사에서 구현 코드의 80%는 거의 사용되지 않는다는 내용과 해당 조사가 언제 수행되었는지를 포함한 문서를 찾아줘"
     → 기대 결과: SW 공학의 개발 생산성.md, Refactoring Lecture.md
- 마무리 (1분): 다음 편 예고

**CLI 명령어**:
```bash
python -m src search --query "..." --rerank --top-k 5
python -m src search --query "..." --search-method semantic --top-k 5
```

**연출 포인트**:
- Obsidian 기본 검색 → vault intelligence 검색 비교
- 같은 쿼리를 semantic vs hybrid vs rerank로 비교

---

### 2편: "기본기가 탄탄해야" - 핵심 기능 완전 정복 (12-15분)

**목적**: 도구의 전체 기능을 체계적으로 소개

**구성**:
- 설치 & 셋업 (2분): pip install, init, reindex
- 4가지 검색 방법 (4분): semantic / keyword / hybrid / colbert
- 고급 검색 옵션 (3분): --rerank, --expand, --with-centrality
- 관련 문서 탐색 (2분): related --file 명령
- 자동 태깅 (2분): tag 명령으로 미분류 문서에 태그 자동 부여
- 마무리 (1분): 다음 편 예고

**CLI 명령어**:
```bash
python -m src search --query "TDD" --search-method semantic
python -m src search --query "TDD" --search-method keyword
python -m src search --query "TDD" --search-method hybrid
python -m src search --query "TDD" --search-method colbert
python -m src search --query "TDD" --rerank
python -m src search --query "TDD" --expand
python -m src search --query "TDD" --with-centrality
python -m src related --file "문서명.md" --top-k 10
python -m src tag "문서명.md"
```

---

### 3편: "내 지식의 지도를 그리다" - 고급 활용 (12-15분)

**목적**: 검색을 넘어서는 지식 분석 기능 시연

**구성**:
- 지식 공백 분석 (3분): analyze-gaps
- MOC 자동 생성 (4분): generate-moc --topic "TDD"
- 주제별 문서 수집 (3분): collect --topic "리팩토링"
- 문서 클러스터링 (3분): vault 전체를 주제별로 자동 분류
- 마무리 (1분): 다음 편 예고

**CLI 명령어**:
```bash
python -m src analyze-gaps --top-k 20
python -m src generate-moc --topic "TDD" --top-k 50
python -m src collect --topic "리팩토링" --output collection.md
```

---

### 4편: "실전에서 이렇게 쓴다" - Claude Code 통합 워크플로우 (10-12분)

**목적**: 실제 개발 중 vault 활용 시나리오 시연

**구성**:
- 코딩 중 지식 검색 (4분): Claude Code에서 코딩하다가 vault 검색
- 학습 리뷰 (3분): 주간/월간 학습 내역 자동 리뷰
- 새 노트 자동 연결 (3분): 새로 작성한 노트를 기존 vault와 자동 연결
- 마무리 (2분): 시리즈 정리 + 향후 계획

**시나리오 예시**:
- TDD로 코딩하다가 "이 패턴 예전에 정리한 적 있는데..." → vault 검색 → 과거 지식 활용
- 새로 배운 내용을 노트로 저장 → 자동 태깅 → 관련 문서 연결

---

## 제작 가이드

### 공통 연출
- 터미널에서 CLI 직접 실행 (라이브 코딩 느낌)
- 검색 결과가 나오면 Obsidian에서 해당 문서를 열어 내용 확인
- 자연어 질문 → AI 검색 결과 → "이걸 이렇게 찾네!" 리액션

### 파일 구조
```
docs/plans/
├── youtube-series-plan.md          # 이 문서 (전체 기획안)
├── ep1-wow-script.md               # 1편 대본
├── ep2-basics-script.md            # 2편 대본
├── ep3-advanced-script.md          # 3편 대본
└── ep4-workflow-script.md          # 4편 대본
```
