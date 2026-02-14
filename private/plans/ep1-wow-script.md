# "이걸 어떻게 찾았지?" - Vault Intelligence 첫인상

## 문제 제기

vis tool을 이용해서 kent beck이 전문가는 복잡한 문제를 분해서 일반적인 기술로 처리한다는 내용이 있는 유튜브 영상이나 아티클 정리를 한 문서를 찾아줘

### [화면]

메모를 좋아함. 근데 어디에 적었는지 기억을 못 할때가 많음
옵시디안은 그런 내겐 완벽한 해결책. 정말 "제2의 뇌"처럼 좋았음
제텔카스텐을 공부하며 실행히 보기도 했음.
그런데 곧 INBOX, SLIPBOX, RESOURCE에 엉망으로 문서가 쌓였음

```bash
fdm -e md | wc -l
```

난 폴더로 정리하는 것은 시작해서 끝까지 유지해 본 기억이 없음
어떤 분들은 001~999 같은 번호 매긴 폴더를 이용하는데 나는 그렇게 정리 정돈을 하지 못 함.
물건도 잘 못 찾음.
그런데 검색해서 찾는 것도 잘 못함

그래서 RAG를 생각했다. 하지만 청킹에서 어려움을 겪었음.
그러다 키워드 뿐 아니라 문서의 벡터 검색을 통해 내가 원하는 문서를 정확히
찾아주는 툴을 Claude와 대화를 하면서 만들게 되었다.

python도 잘 모르고, 검색 엔진에 대한 이해도 깊지 않았다.
그런데 수천개의 마크다운 문서를 잘 검색하고 싶었다.
원하는 기능을 만들면서 조금 조금씩 배웠다.
dense, sparse, colbert 등을 이제 좀 이해한다.

이론적으로 다 학습하고 구현하면 좋겠지만 지금도 충분히 좋다
조각 지식을 쌓았다
모르는게 많다고 강박을 가질 필요 없다
vis 는 세컨브레인을 위한 나만의 rag 이면서 옵시디안 ai 비서이다.

그리고 이 툴을 커맨드 라인에서 직접 사용하는 것 보다 claude code에게 이 툴의 사용법을
알려주고 claude를 이용해서 검색했을 때 엄청난 만족감을 느끼게 되었다.

### [화면]

- Obsidian 기본 검색창 표시
- "kent beck 주니어 전문가" 검색 → 많은 결과가 나오가 원하는 문서를 찾기 어려움

"분명히 어디선가 읽었는데..."
"Kent Beck이 전문가와 주니어의 차이에 대해 얘기했던 게 어디더라..."

오늘은 이 문제를 해결한 결과를 보여드리겠습니다.

## #1: Kent Beck - 전문가 vs 주니어

### Vault Intelligence 소개

제가 만든 도구, Vault Intelligence입니다.
BGE-M3라는 최신 AI 임베딩 모델을 사용해서 문서의 '의미'를 이해합니다.

> BGE-M3는 BAAI(Beijing Academy of Artificial Intelligence: 중국 베이징에 위치한 AI 연구기관, BGE 시리즈 등 오픈소스 임베딩 모델과 다양한 AI 연구로 유명)에서 개발한 다국어 임베딩 모델로, Dense, Sparse(Lexical), Multi-vector(ColBERT) 세 가지 검색 방식을 하나의 모델에서 동시에 지원하는 것이 특징
> Dense Retrieval: **텍스트**를 하나의 **고정 차원 벡터**로 변환하여 **코사인 유사도** 등으로 **의미적 유사성을 비교**하는 방식입니다.
> Sparse (Lexical) Retrieval: **BM25**(출현 빈도(TF)와 전체 문서에서의 희소성(IDF))처럼 각 토큰에 가중치를 부여한 희소 벡터를 생성하여 **키워드 매칭 기반**으로 검색하는 방식입니다.
> Multi-vector (ColBERT): **텍스트의 각 토큰마다 별도 벡터를 생성**한 뒤, 토큰 단위로 유사도를 계산하고 합산(MaxSim)하여 더 세밀한 매칭을 수행하는 방식입니다.

자연어로 질문해볼게요.

### 검색

vis search "kent beck 전문가 복잡한 문제" --rerank

/vis kent beck이 전문가들이 복잡한 문제를 다른 것에 대해 설명한 문서를 찾아줘.

### [해설/나레이션]

음... 나쁘지 않네요. 관련 문서들이 나왔습니다.
하지만 이제 --rerank 옵션을 켜보겠습니다.

> --rerank 옵션
> 1차 검색 결과를 Cross-encoder(BGE Reranker V2-M3)로 재평가하여 의미적 정확도를 높임
> 쿼리와 문서를 하나의 입력으로 함께 넣어 Transformer가 둘 사이의 관련성을 직접 계산하는 방식
> 정확도가 높지만 모든 후보 문서마다 개별 추론이 필요해 속도가 느려서 주로 리랭킹 단계에서 사용

```bash
$ python -m src search --query "kent beck이 전문가는 주니어와 다른 접근법을 취한다고 언급한 내용이 있는 문서를 찾아줘" --rerank --top-k 5
```

순위가 완전히 바뀌었습니다.
rerank는 BGE Reranker라는 또 다른 AI 모델을 사용해서
쿼리와 문서의 관련성을 더 정확하게 재평가합니다.

## #2: AI 코드 리뷰 vs TDD

"요즘 AI가 코드 리뷰도 해주는데, 굳이 TDD랑 Refactoring을 배워야 할까?"

Kent Beck이 이런 질문에 대답한 내용이 있었던 것 같은데... 어디였더라?

```bash
$ python -m src search --query "kent beck이 AI로 코드 리뷰를 해서 피드백을 받을 수 있는데 왜 TDD, Refactoring을 배워야 한다는 질문에 답하는 내용이 있는 문서를 찾아줘" --rerank --top-k 5
```

## #3: Victor Rentea의 숨겨진 기법

Victor Rentea라는 개발 코치가 있습니다.
그가 "split by unrelated complexity"라는 기법을 소개했는데,
그와 동일한 수준의 또 다른 기법을 언급했던 게 기억나는데...

이걸 일반 검색으로 찾는다? 불가능합니다.

```bash
$ python -m src search --query "victor rentea가 split by unrelated complexity와 동일한 수준의 기법을 하나 더 말했는데 그 기법과 관련된 문서를 찾아줘" --rerank --top-k 5
```

## #4: 80% 코드 미사용 - 언제, 누가?

"어떤 조사 결과가 있었어. 구현된 코드의 80%는 거의 사용되지 않는다는..."
"그게 언제, 어떤 기관에서 한 조사였지?"

이런 건 정말... 기억의 조각만 남은 상태죠.

```bash
$ python -m src search --query "어떤 기관의 조사에서 구현 코드의 80%는 거의 사용되지 않는다는 내용과 해당 조사가 언제 수행되었는지를 포함한 문서를 찾아줘" --rerank --top-k 5
```

## 마무리

vibe coding

내가 필요한 것을 만들었댜.
지금까지 나를 제외한 사용자는 한명으로 알고 있다.
하지만 이렇게 나에게 필요한 것을 만들면서
Dense, Sparse, Multi-vector 검색을 모두 지원하는
최신 AI 임베딩 모델 BGE-M3를 활용하는 도구를 만들었다
그리고 그런 기술들이 무엇인지를 꽤 배우게 되었다.
이렇게 AI는 나의 문제를 푸는데 도움도 되었고,
어렴풋이 알던 기술들에 대한 나의 이해도 높여주었다.

### Vault Intelligence 정보

- GitHub 링크: https://github.com/msbaek/vault-intelligence
- AI(claude code)에게 검색 도구(Vault Intelligence)를 알려주고 검색을 시켰더니
  검색툴을 직접 사용했을 때 보다 훨씬 더 정확한 결과를 얻을 수 있었습니다.

여러분들도 자신의 지식 저장소에 Vault Intelligence를 적용해보시며 어떨까요 ?

### [해설/나레이션]

오늘은 Vault Intelligence를 사용해서
제가 정리해둔 방대한 문서들 속에서
제가 궁금했던 내용들을 정확히 찾아내는 모습을 보여드렸습니다.

다음 편에서는:

- Semantic, Keyword, Hybrid, ColBERT... 4가지 검색 방법
- --expand로 쿼리 확장하기
- --with-centrality로 중심 문서 찾기
- 관련 문서 자동 탐색
- 자동 태깅 시스템
