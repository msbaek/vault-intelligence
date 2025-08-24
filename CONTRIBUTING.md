# 기여 가이드 (Contributing Guide)

Vault Intelligence System V2 프로젝트에 기여해 주셔서 감사합니다! 이 문서는 효과적이고 일관성 있는 기여를 위한 가이드라인을 제공합니다.

## 🤝 기여 방법

### 1. 이슈 보고
버그나 개선사항을 발견했다면:
1. [Issues](https://github.com/your-username/vault-intelligence/issues)에서 유사한 이슈가 있는지 확인
2. 새 이슈 생성 시 적절한 템플릿 사용
3. 재현 가능한 예시와 환경 정보 포함

### 2. 기능 제안
새로운 기능 아이디어가 있다면:
1. [Discussions](https://github.com/your-username/vault-intelligence/discussions)에서 먼저 논의
2. 커뮤니티 피드백을 받은 후 이슈로 전환
3. 기능의 목적, 사용 사례, 구현 방향 명시

### 3. 코드 기여
직접 코드를 기여하려면:
1. Fork 생성 후 feature 브랜치에서 작업
2. 변경사항에 대한 테스트 작성
3. Pull Request 생성 전 아래 체크리스트 확인

## 🔧 개발 환경 설정

### 필수 요구사항
- Python 3.11+
- Git
- 8GB+ RAM (테스트용)

### 설정 단계
```bash
# 1. 레포지토리 포크 및 클론
git clone https://github.com/your-username/vault-intelligence.git
cd vault-intelligence

# 2. 개발 환경 설정
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. 개발용 의존성 설치 (선택)
pip install pytest black flake8 mypy

# 4. 시스템 테스트
python -m src test
```

## 📝 코딩 표준

### Python 코딩 스타일
- [PEP 8](https://peps.python.org/pep-0008/) 준수
- 라인 길이: 최대 100자
- 들여쓰기: 4 스페이스
- 문자열: 큰따옴표(`"`) 사용

### 코드 품질 도구
```bash
# 코드 포맷팅
black src/

# 린팅
flake8 src/

# 타입 체크
mypy src/
```

### 문서화
- 모든 public 함수/클래스에 docstring 필수
- Google 스타일 docstring 사용
- 복잡한 로직에는 인라인 주석 추가

```python
def example_function(param1: str, param2: int) -> dict:
    """함수의 목적을 간단히 설명합니다.
    
    Args:
        param1: 첫 번째 파라미터 설명
        param2: 두 번째 파라미터 설명
        
    Returns:
        결과 딕셔너리에 대한 설명
        
    Raises:
        ValueError: 발생 가능한 예외 설명
    """
    # 구현 내용
    pass
```

## 🧪 테스트

### 테스트 작성 원칙
- 새로운 기능은 반드시 테스트 포함
- 기존 테스트가 깨지지 않도록 확인
- Edge case와 에러 상황 테스트

### 테스트 실행
```bash
# 전체 시스템 테스트
python -m src test

# 특정 모듈 테스트
python -c "from src.features.advanced_search import test_search_engine; test_search_engine()"

# pytest 사용 (설치된 경우)
pytest tests/
```

### 테스트 커버리지
핵심 기능은 최소 80% 이상의 코드 커버리지 유지

## 🔄 Pull Request 가이드

### PR 생성 전 체크리스트
- [ ] 관련 이슈 번호 연결
- [ ] 기능에 대한 테스트 작성
- [ ] 모든 기존 테스트 통과
- [ ] 코드 스타일 가이드 준수
- [ ] 문서 업데이트 (필요시)
- [ ] CHANGELOG.md 업데이트 (중요 변경사항)

### PR 템플릿
```markdown
## 변경사항 요약
간단한 변경사항 설명

## 관련 이슈
- Fixes #123
- Related to #456

## 변경 유형
- [ ] 🐛 버그 수정
- [ ] ✨ 새 기능
- [ ] 📚 문서 개선  
- [ ] 🎨 코드 스타일
- [ ] ♻️ 리팩토링
- [ ] ⚡ 성능 개선
- [ ] 🧪 테스트 추가

## 테스트
- [ ] 단위 테스트 작성
- [ ] 기존 테스트 통과
- [ ] 수동 테스트 완료

## 스크린샷/로그
(필요시 추가)
```

## 🏷️ 커밋 메시지 규칙

### Conventional Commits 사용
```
type(scope): subject

body

footer
```

### 타입 종류
- `feat`: 새로운 기능
- `fix`: 버그 수정
- `docs`: 문서 변경
- `style`: 코드 포맷팅, 세미콜론 등
- `refactor`: 코드 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드, 패키지 매니저 설정 등

### 예시
```
feat(search): add ColBERT token-level search support

- Implement ColBERT search method in AdvancedSearchEngine
- Add colbert_search CLI option
- Include performance optimizations for large documents

Closes #123
```

## 🎯 기여 영역

### 우선순위가 높은 기여 분야
1. **문서 개선**: 사용법, 예시, 트러블슈팅
2. **테스트 커버리지**: 기존 기능의 테스트 보완
3. **성능 최적화**: 메모리 사용량, 검색 속도 개선
4. **새로운 검색 알고리즘**: 새로운 임베딩 모델 지원
5. **UI/UX 개선**: CLI 인터페이스 개선

### Phase 10+ 로드맵 기여
- 웹 인터페이스 개발 (FastAPI + React)
- 플러그인 시스템 아키텍처
- 다중 언어 지원 확장
- 실시간 모니터링 대시보드

## 🐛 버그 리포트 템플릿

```markdown
## 버그 설명
명확하고 간결한 버그 설명

## 재현 단계
1. '...' 이동
2. '...' 클릭
3. '...' 스크롤
4. 오류 확인

## 예상 동작
예상했던 결과 설명

## 실제 동작
실제 발생한 결과 설명

## 환경
- OS: [예: macOS 13.0]
- Python: [예: 3.11.5]
- 시스템 버전: [예: v2.1.0]
- Vault 크기: [예: 1000개 문서]

## 추가 정보
스크린샷, 로그, 기타 관련 정보
```

## 📋 기능 요청 템플릿

```markdown
## 기능 설명
원하는 기능에 대한 명확하고 간결한 설명

## 동기/문제
현재 어떤 문제가 있으며, 왜 이 기능이 필요한가?

## 제안하는 해결책
이 문제를 어떻게 해결하고 싶은지 설명

## 대안 검토
고려해본 다른 해결책이나 기능

## 추가 컨텍스트
스크린샷, 링크 등 추가 정보
```

## 🏆 기여자 인정

모든 기여자는 다음과 같이 인정받습니다:
- README.md의 기여자 섹션에 이름 추가
- 각 릴리스 노트에 주요 기여자 언급
- Discord/커뮤니티에서 기여 소개

## 📞 커뮤니케이션

### 소통 채널
- **이슈**: 버그 리포트, 기능 요청
- **토론**: 아이디어 공유, 질문
- **PR**: 코드 리뷰, 구현 논의

### 응답 시간
- 이슈/PR: 48시간 내 최초 응답
- 코드 리뷰: 72시간 내 완료
- 긴급 버그: 24시간 내 응답

## 🙏 감사의 말

Vault Intelligence System V2는 커뮤니티의 기여로 만들어집니다. 큰 변경부터 작은 오타 수정까지, 모든 기여에 감사드립니다!

질문이 있으시면 언제든지 이슈를 생성해 주세요. 함께 더 나은 도구를 만들어 갑시다! 🚀