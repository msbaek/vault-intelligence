# 실전에서 이렇게 쓴다

- 강연
  - 하고 싶은 말을 A4 반장 정도 분량으로 작성
  - vault-intelligence 에게 그 메모를 보고 발표할 내용을 작성해 달라고 요청
  - obsidian advanced slide 공식 url을 알려주고 발표 시간에 맞는 분량의 슬라이드
    작성을 요청
- MindMap
  - 유사한 방식으로 OPML로 출력 요청

## 오프닝

실제로 일하면서 vault-intelligence를 어떻게 활용하는지, 세 가지 시나리오로
보여줌

## 시나리오 1: 코딩 중 지식 검색 (4분)

#### [코드 - 화면에 보이는 것]

```java
@Test
void shouldValidateUserInput() {
    // 이 패턴... 예전에 정리한 적 있는데...
    // TDD 관련 노트에 있었던 것 같은데
}
```

#### [해설]

> "TDD로 코드를 짜다가 막혔습니다. '이 패턴 예전에 정리한 적 있는데...' 하는 느낌이 들죠."
>
> "예전 같으면 Obsidian 열어서 검색하고, 파일 찾아보고... 컨텍스트 스위칭이 일어납니다. 하지만 지금은 다릅니다."

### 1.2 Claude Code에서 즉시 검색 (1분 30초)

**[시간: 1:30-3:00]**

#### [화면]

- Claude Code 터미널로 전환
- 프롬프트 입력

#### [입력 - 화면에 보이는 것]

```
User: TDD 패턴 중에 입력 검증하는 방법 정리한 노트 찾아줘
```

#### [Claude Code 실행 - 화면에 보이는 것]

```bash
# Claude Code가 자동으로 vault-intelligence 호출
python -m src search --query "TDD 패턴 과거 정리한 내용" --rerank --top-k 5
```

#### [출력 결과 - 화면에 보이는 것]

```
📄 검색 결과 (5개):
--------------------------------------------------------------------------------
1. TDD와 Refactoring 관련 리소스 모음
   경로: 003-RESOURCES/TDD-RELATED-RESOURCES.md
   유사도: 0.3162
   키워드: tdd, 패턴, 내용

2. TDD-Theme & Variations
   경로: 003-RESOURCES/TDD/TDD-Theme & Variations.md
   유사도: -0.7490
   키워드: tdd, 패턴, 과거, 정리한, 내용
```

#### [해설]

> "Claude Code에게 그냥 물어봤더니, 알아서 vault-intelligence를 호출해서 제 3천 개 노트를 검색합니다."
>
> "여기서 핵심은 `--rerank` 옵션인데요. 재순위화 덕분에 제가 찾던 정확한 문서가 상위에 나타납니다."

### 1.3 검색된 지식을 현재 코딩에 적용 (1분 30초)

**[시간: 3:00-4:30]**

#### [화면]

- Claude Code가 검색 결과를 분석
- Obsidian에서 해당 노트 미리보기
- 다시 IntelliJ로 돌아와 코드 작성

#### [Claude Code 응답 - 화면에 보이는 것]

```
Claude: "TDD-Theme & Variations.md"에서 관련 내용을 찾았습니다.

입력 검증 패턴:
1. Degenerate Case부터 시작 (null, empty)
2. 정상 케이스로 확장
3. 경계값 테스트

이 순서로 테스트를 작성하면 자연스럽게 구현이 진화합니다.
```

#### [코드 작성 - 화면에 보이는 것]

```java
@Test
void shouldRejectNullInput() {  // Degenerate Case
    assertThrows(IllegalArgumentException.class,
        () -> validator.validate(null));
}

@Test
void shouldRejectEmptyInput() {  // Degenerate Case
    assertThrows(IllegalArgumentException.class,
        () -> validator.validate(""));
}

@Test
void shouldAcceptValidInput() {  // 정상 케이스
    assertTrue(validator.validate("user@example.com"));
}
```

#### [해설]

> "과거의 제가 정리해둔 TDD 패턴을 현재의 제가 활용합니다. 컨텍스트 스위칭 없이, Claude Code 안에서 모든 게 이뤄집니다."
>
> "이게 바로 'AI가 내 두 번째 뇌를 읽는다'의 진짜 의미입니다."

---

## 시나리오 2: 학습 리뷰 (3분)

**[시간: 4:30-7:30]**

### 2.1 학습 내용 정리 필요성 (30초)

**[시간: 4:30-5:00]**

#### [화면]

- Claude Code 터미널

#### [해설]

> "주말이 되면 이번 주에 뭘 배웠는지 정리하고 싶을 때가 있죠. 하지만 vault에 3천 개가 넘는 노트가 있으니 어디서부터 봐야 할지..."

### 2.2 MOC 자동 생성 (1분 30초)

**[시간: 5:00-6:30]**

#### [입력 - 화면에 보이는 것]

```bash
python -m src generate-moc --topic "TDD" --top-k 30
```

#### [출력 결과 - 화면에 보이는 것]

```
📚 'TDD' MOC 생성 시작...

📊 MOC 생성 결과:
--------------------------------------------------
주제: TDD
총 문서: 30개
핵심 문서: 5개
카테고리: 7개
학습 경로: 7단계

📋 카테고리별 문서 분포:
  입문/기초: 9개 문서
  개념/이론: 9개 문서
  실습/예제: 10개 문서
  도구/기술: 10개 문서
  심화/고급: 5개 문서

🛤️ 학습 경로:
  1단계: 입문/기초 (입문) - 5개 문서
  2단계: 개념/이론 (기초) - 5개 문서
  3단계: 실습/예제 (중급) - 5개 문서
```

#### [화면 전환]

- 생성된 MOC 파일을 Obsidian에서 열기

#### [해설]

> "generate-moc 명령으로 TDD 관련 문서 30개를 자동으로 정리했습니다."
>
> "제가 직접 분류한 게 아니라, AI가 문서들의 의미를 분석해서 입문부터 고급까지 학습 경로를 만들어줬습니다."

### 2.3 주제별 문서 수집 (1분)

**[시간: 6:30-7:30]**

#### [입력 - 화면에 보이는 것]

```bash
python -m src collect --topic "리팩토링" --output refactoring-collection.md
```

#### [출력 결과 - 화면에 보이는 것]

```
📚 주제 '리팩토링' 문서 수집 시작...

📊 수집 결과:
--------------------------------------------------
주제: 리팩토링
수집 문서: 10개
총 단어수: 39,118개
총 크기: 390.9KB

🏷️ 태그 분포:
  source/book: 6개
  type/book-notes: 6개
  topic/clean-coders/codecasts: 4개

💾 결과가 refactoring-collection.md에 저장되었습니다.
```

#### [화면 전환]

- 생성된 collection 파일을 Obsidian에서 열어서 스크롤

#### [해설]

> "collect 명령은 주제별로 문서를 모아서 하나의 파일로 만들어줍니다. 리팩토링 관련 노트 10개, 총 390KB를 한 번에 볼 수 있죠."
>
> "이렇게 주말마다 주제별로 정리하면, 제 지식이 어떻게 쌓여가는지 한눈에 볼 수 있습니다."

---

## 시나리오 3: 새 노트 자동 연결 (3분)

**[시간: 7:30-10:30]**

### 3.1 새 노트 작성 후 고민 (30초)

**[시간: 7:30-8:00]**

#### [화면]

- Obsidian에서 새로 작성한 노트 (2025-ISMS-P.md)
- 태그가 하나도 없는 상태

#### [해설]

> "오늘 회의에서 배운 내용을 노트로 정리했습니다. 그런데 이제 고민이 시작되죠."
>
> "'어떤 태그를 달아야 하지?' '이거랑 관련된 노트가 뭐가 있었지?' vault와 어떻게 연결해야 할지 막막합니다."

### 3.2 자동 태깅 (1분)

**[시간: 8:00-9:00]**

#### [입력 - 화면에 보이는 것]

```bash
python -m src tag --target 2025-ISMS-P.md
```

#### [출력 결과 - 화면에 보이는 것]

```
🏷️ 자동 태깅 시작: 2025-ISMS-P.md

📊 태깅 결과:
--------------------------------------------------
처리 파일: 1개
성공: 1개
성공률: 100.0%

📋 상세 결과:

1. 2025-ISMS-P.md
   ✅ 성공 (처리시간: 2.85초)
   기존 태그: 0개
   생성 태그: 8개
   새 태그:
     - career-development/senior-engineer
     - document-type/work-log
     - architecture/clean-architecture
     - architecture/hexagonal
     - data-platform/design
     - databricks/architecture
     - ddd/value-objects/implementation
     - java/records/validation
```

#### [화면 전환]

- Obsidian에서 노트 다시 열기
- frontmatter에 태그가 추가된 모습

#### [해설]

> "tag 명령 하나로 vault 전체의 태그 패턴을 학습해서, 이 문서에 어울리는 태그 8개를 자동으로 붙여줬습니다."
>
> "제가 3년 동안 수동으로 달아왔던 태그 스타일을 AI가 학습해서 그대로 따라합니다."

### 3.3 관련 문서 찾기 (1분 30초)

**[시간: 9:00-10:30]**

#### [입력 - 화면에 보이는 것]

```bash
python -m src related --file 2025-ISMS-P.md --top-k 5
```

#### [출력 결과 - 화면에 보이는 것]

```
🔗 '2025-ISMS-P.md' 관련 문서 찾기...

📄 관련 문서 (5개):
--------------------------------------------------------------------------------
1. Web Application Architecture Types
   경로: 003-RESOURCES/ARCHITECTURE/Web Application...
   관련도: 0.5750
   태그: architecture/design, technology/java

2. FOMS
   경로: notes/dailies/2026-02-03-FOMS.md
   관련도: 0.5654

3. 의존성 역전
   경로: 997-BOOKS/Get_Your_Hands_Dirty.../Ch05...
   관련도: 0.5649
   태그: architecture/clean-architecture, architecture/hexagonal

4. 운영팁
   경로: work-log/2022/운영팁.md
   관련도: 0.5583
   태그: operations/tips, web/authentication

5. 2025-11-20
   경로: notes/dailies/2025-11-20.md
   관련도: 0.5561
```

#### [화면 전환]

- Obsidian에서 노트에 "관련 노트" 섹션 추가
- 링크 5개 복사해서 붙여넣기

#### [노트에 추가된 내용 - 화면에 보이는 것]

```markdown
## 관련 노트

- [[Web Application Architecture Types]] - 아키텍처 설계 패턴
- [[FOMS]] - 동일 프로젝트 이전 작업
- [[의존성 역전]] - Clean Architecture 참고서적
- [[운영팁]] - 인증/암호화 관련 팁
- [[2025-11-20]] - 이전 회의록
```

#### [해설]

> "related 명령으로 이 노트와 의미적으로 가장 유사한 문서 5개를 찾았습니다."
>
> "태그만으로는 찾을 수 없었던 연결고리를 AI가 발견해줬죠. '아, 이전에 FOMS 프로젝트에서 비슷한 고민을 했었구나' 이런 걸 알게 됩니다."
>
> "이제 이 노트는 vault 전체와 연결되었습니다. 고립된 섬이 아니라, 지식 그래프의 일부가 된 거죠."

---

## 마무리 (2분)

**[시간: 10:30-12:00]**

### 4.1 시리즈 전체 요약 (1분)

**[시간: 10:30-11:30]**

#### [화면]

- 슬라이드 형태로 4편 요약
  - 1편: WOW 순간 - "이걸 어떻게 찾았지?"
  - 2편: 핵심 기능 - 검색 방법 4가지
  - 3편: 고급 활용 - 지식 그래프, MOC
  - 4편: 실전 워크플로우 - Claude Code 통합

#### [해설]

> "지난 3편을 되돌아보면, vault-intelligence는 단순한 검색 도구가 아니었습니다."
>
> "1편에서는 AI의 힘으로 어떻게 정확한 문서를 찾는지 봤고, 2편에서는 검색 방법 4가지를 익혔죠. 3편에서는 지식 그래프로 vault 전체를 조망했습니다."
>
> "그리고 오늘 4편, 실제로 어떻게 쓰는지 봤습니다. Claude Code와 함께 코딩하면서, 학습하면서, 노트를 정리하면서."

### 4.2 vault-intelligence의 가치 (30초)

**[시간: 11:30-12:00]**

#### [화면]

- vault-intelligence 로고
- GitHub 저장소 주소

#### [해설]

> "결국 vault-intelligence의 진짜 가치는 이겁니다. '과거의 내가 미래의 나를 돕는다.'"
>
> "제가 3년 동안 쌓아온 3,400개 노트가, 이제 제 두 번째 뇌가 됐습니다. 그리고 AI가 그 뇌를 읽고, 제게 필요한 순간에 필요한 지식을 꺼내줍니다."

#### [화면에 표시되는 텍스트]

```
vault-intelligence
GitHub: https://github.com/msbaek/vault-intelligence

설치:
pip install -r requirements.txt
python -m src init --vault-path ~/your-vault

시작하기:
python -m src search --query "검색어" --rerank
```

#### [마지막 멘트]

> "시청해주셔서 감사합니다. 여러분도 자신만의 두 번째 뇌를 만들어보세요."
>
> "GitHub에서 vault-intelligence를 다운받아 사용해보시고, 이슈나 PR로 함께 발전시켜 나갔으면 좋겠습니다."

---

## 제작 노트

### 촬영 팁

1. **시나리오 1 (코딩 중 검색)**

   - IntelliJ와 Claude Code 터미널을 분할 화면으로
   - 실제 코딩하는 손의 움직임 보여주기
   - Claude Code가 자동으로 CLI를 호출하는 과정 강조

2. **시나리오 2 (학습 리뷰)**

   - MOC 생성 전후 비교 (수동 vs 자동)
   - 터미널 출력을 천천히 스크롤하면서 해설
   - Obsidian에서 생성된 파일 확인

3. **시나리오 3 (새 노트 연결)**
   - 태그 없는 노트 → 태그 추가 과정 화면 녹화
   - related 명령 실행 → 링크 복사 → 노트에 붙여넣기까지 원샷으로
   - 최종적으로 그래프 뷰에서 연결된 모습 보여주기

### 편집 포인트

- 터미널 출력이 길 때는 빠르게 재생 (1.5x ~ 2x)
- 중요한 결과는 화면에 하이라이트 박스 추가
- Claude Code 응답 부분은 말풍선 효과로 강조
- 배경음악: 차분하고 집중력 있는 lo-fi

### 자막

- 명령어는 고정폭 폰트로 표시
- 핵심 키워드는 색상 강조 (예: `--rerank`, `MOC`, `related`)
- 한글 자막 + 영어 명령어는 병기

---

## 실제 명령어 순서 (촬영 시 참조)

### 시나리오 1

```bash
# 터미널에서 실행
python -m src search --query "TDD 패턴 과거 정리한 내용" --rerank --top-k 5
```

### 시나리오 2

```bash
# MOC 생성
python -m src generate-moc --topic "TDD" --top-k 30

# 주제별 수집
python -m src collect --topic "리팩토링" --output refactoring-collection.md
```

### 시나리오 3

```bash
# 자동 태깅
python -m src tag --target 2025-ISMS-P.md

# 관련 문서 찾기
python -m src related --file 2025-ISMS-P.md --top-k 5
```

---

## 예상 시청자 반응 & 대응

### Q1: "Claude Code가 자동으로 vault-intelligence를 호출하나요?"

**A**: 네, Claude Code에게 "vault에서 검색해줘"라고 하면 알아서 적절한 CLI 명령어를 실행합니다. CLAUDE.md 파일에 vault-intelligence 사용법을 정의해두면 됩니다.

### Q2: "제 vault는 노트가 100개밖에 안 되는데 필요한가요?"

**A**: vault-intelligence는 100개부터 유용합니다. 문서 수가 적을수록 검색은 빠르고, 나중에 문서가 늘어나도 같은 방식으로 계속 사용할 수 있습니다.

### Q3: "영어 문서에도 작동하나요?"

**A**: 네, BGE-M3 모델은 다국어를 지원합니다. 한글, 영어, 중국어, 일본어 등 100개 이상 언어에서 작동합니다.

### Q4: "검색 속도는 어느 정도인가요?"

**A**: 초기 인덱싱은 1,000개 문서 기준 40-60분 정도 걸리지만, 한 번 인덱싱하면 검색은 1-2초 안에 완료됩니다. 캐시를 활용하기 때문입니다.

---

## 시리즈 완성 체크리스트

- [x] 1편: WOW 순간 4개 (ep1-wow-script.md)
- [x] 2편: 핵심 기능 완전 정복 (ep2-basics-script.md)
- [x] 3편: 고급 활용 (ep3-advanced-script.md)
- [x] 4편: 실전 워크플로우 (이 문서)
- [ ] 썸네일 디자인 (4편용)
- [ ] 영상 편집
- [ ] YouTube 업로드
- [ ] 시리즈 재생목록 생성

---

**제작 완료일**: 2026-02-07
**제작자**: vault-intelligence YouTube 시리즈 팀
**버전**: 1.0
