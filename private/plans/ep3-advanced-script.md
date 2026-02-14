# "내 지식의 지도를 그리다"

## 메타데이터

## 오프닝

- Obsidian Graph View를 배경으로 (3,103개 노드가 연결된 복잡한 그래프)

> "오늘은 한 단계 더 나아가서, **검색을 넘어선 지식 분석** 기능들을 소개합니다."
>
> "제 vault에는 3,103개의 문서가 있습니다. 이 문서들 사이에 어떤 패턴이 있을까요? 어떤 부분이 부족할까요? 어떻게 연결되어 있을까요?"
>
> "오늘은 AI가 제 지식의 지도를 그려주는 과정을 보여드리겠습니다."

---

## 지식 공백 분석 (1:30-4:30)

```bash
python -m src analyze-gaps --top-k 20
```

- "3천 개가 넘는 문서를 다 기억할 수 없음
- 어떤 주제는 깊이 있게 정리했지만, 어떤 주제는 단편적인 메모만 있을 수 있음
- 이 명령어는 vault 전체를 스캔해서 **어떤 부분이 약하게 연결되어 있는지** 찾아줌

### [화면]

실행 결과 표시:

```
📊 지식 공백 분석 결과:
--------------------------------------------------
전체 문서: 3,103개
고립 문서: 0개
약한 연결 문서: 0개
고립 태그: 7,855개
고립률: 0.0%

🏷️ 고립된 태그들 (상위 10개):
  - development/practices/legacy-code
  - java/errorprone/static-analysis
  - java/lombok/code-cleanup
  - refactoring/automated/structural-search-replace
  - refactoring/openrewrite/migration
  ...

📈 주요 태그 분포:
  - daily-notes: 209개 문서
  - status/active: 186개 문서
  - topic/code-review: 183개 문서
  - technology/java: 168개 문서
  - status/archived: 152개 문서
  ...
```

### [나레이션]

> "결과를 보면 흥미로운 점들이 보입니다."
>
> "첫째, 고립된 태그가 7,855개나 됩니다. 이 태그들은 단 하나의 문서에만 사용된 태그들입니다. 즉, **아직 체계화되지 않은 지식**이라는 뜻이죠."
>
> "예를 들어 'refactoring/automated/structural-search-replace' 같은 태그는 딱 한 문서에만 달려있습니다. 이런 주제에 대해서는 더 많은 학습이나 정리가 필요할 수 있습니다."
>
> "둘째, 주요 태그 분포를 보면 제가 어떤 주제에 관심이 많은지 한눈에 보입니다."
>
> "daily-notes가 209개로 가장 많고, code-review가 183개, Java 관련이 168개... 제가 일상적으로 코드 리뷰와 Java 개발에 집중하고 있다는 걸 알 수 있죠."
>
> "이런 분석은 **내가 어디에 시간을 쓰고 있는지**, **어떤 분야를 더 공부해야 하는지** 객관적으로 보여줍니다."

---

## MOC 자동 생성 - TDD (4:30-8:00)

### [화면]

터미널에서 명령어 입력:

```bash
python -m src generate-moc --topic "TDD" --top-k 50
```

MOC(Map of Content): Obsidian에서 특정 주제와 관련된 모든 노트를 한곳에 모아놓은 허브 노트

실행 결과 표시:

```
📚 'TDD' MOC 생성 시작...

📊 MOC 생성 결과:
--------------------------------------------------
주제: TDD
총 문서: 50개
핵심 문서: 5개
카테고리: 7개
학습 경로: 7단계
관련 주제: 10개
최근 업데이트: 19개
문서 관계: 44개

📋 카테고리별 문서 분포:
  입문/기초: 10개 문서
  개념/이론: 10개 문서
  실습/예제: 10개 문서
  도구/기술: 10개 문서
  심화/고급: 9개 문서
  참고자료: 10개 문서
  기타: 10개 문서

🛤️ 학습 경로:
  1. 1단계: 입문/기초 (입문) - 5개 문서
  2. 2단계: 개념/이론 (기초) - 5개 문서
  3. 3단계: 실습/예제 (중급) - 5개 문서
  ...
```

## 주제별 문서 수집 (9:30-11:30)

```bash
python -m src collect --topic "TDD" --output /tmp/tdd-collection.md
```

MOC는 링크만 모아주는 거라면, collect는 **실제 내용까지 전부 모아줌**

- 예. TDD에 대해 발표 자료를 만들거나 블로그 글을 쓸 때 관련 자료를 모두 한곳에 모아서 보고 싶은 필요가 생김

실행 결과 표시:

```
📊 수집 결과:
--------------------------------------------------
주제: TDD
수집 문서: 10개
총 단어수: 31,848개
총 크기: 296.5KB

🏷️ 태그 분포:
  - source/book: 6개
  - type/book-notes: 6개
  - topic/clean-coders/codecasts: 2개
  ...

📁 디렉토리 분포:
  - clean-coders-my-youtube: 2개
  - clean-coders-codecasts: 2개
  ...

💾 결과가 /tmp/tdd-collection.md에 저장되었습니다.
```

## 마무리 (11:30-13:00)

### [화면]

터미널과 Obsidian을 나란히

- 터미널: 오늘 사용한 세 가지 명령어 요약
- Obsidian: Graph View에서 특정 클러스터들이 하이라이트됨

### 명령어 치트시트

```bash
# 지식 공백 분석
python -m src analyze-gaps --top-k 20

# MOC 생성
python -m src generate-moc --topic "주제명" --top-k 50

# 문서 수집
python -m src collect --topic "주제명" --output 파일명.md
```
