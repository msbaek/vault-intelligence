# 🔒 보안 가이드 - Vault Intelligence System

이 문서는 Vault Intelligence System의 보안 정책, 가이드라인 및 사고 대응 절차를 다룹니다.

## 📋 목차

1. [보안 정책](#보안-정책)
2. [민감정보 관리](#민감정보-관리)
3. [개발 보안 가이드라인](#개발-보안-가이드라인)
4. [자동화된 보안 검사](#자동화된-보안-검사)
5. [사고 대응 절차](#사고-대응-절차)
6. [보안 도구 사용법](#보안-도구-사용법)
7. [FAQ](#faq)

## 🛡️ 보안 정책

### 기본 원칙
- **최소 권한 원칙**: 필요한 최소한의 권한만 부여
- **심층 방어**: 여러 계층의 보안 조치 적용
- **투명성**: 보안 문제는 즉시 공개 및 대응
- **지속적 개선**: 정기적인 보안 검토 및 업데이트

### 지원되는 버전
현재 보안 업데이트를 받는 버전:

| 버전 | 지원 여부 |
| --- | --- |
| 2.x.x | ✅ |
| 1.9.x | ✅ |
| < 1.9 | ❌ |

## 🔐 민감정보 관리

### ❌ 절대 커밋하면 안 되는 정보
- **API 키**: OpenAI, Google, Anthropic, Naver 등
- **비밀번호**: 데이터베이스, 서비스 계정 등
- **토큰**: JWT, OAuth, Personal Access Token 등
- **인증서**: SSL/TLS 인증서, SSH 키 등
- **개인정보**: 주민등록번호, 신용카드 번호 등
- **금융정보**: 계좌번호, 카드번호 등

### ✅ 환경변수 관리 방법

#### 1. 템플릿 파일 사용
```bash
# .env.example (커밋 가능)
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
NAVER_CLIENT_ID=your_naver_client_id_here
NAVER_CLIENT_SECRET=your_naver_client_secret_here

# .env (커밋 금지, .gitignore에 포함)
OPENAI_API_KEY=sk-실제키값
GOOGLE_API_KEY=AIza실제키값
NAVER_CLIENT_ID=실제값
NAVER_CLIENT_SECRET=실제값
```

#### 2. 환경변수 파일 생성
```bash
# 템플릿에서 실제 환경변수 파일 생성
cp .env.example .env
# .env 파일을 편집하여 실제 값 입력
```

#### 3. .gitignore 설정
```gitignore
# 환경변수 파일들
.env
.env.*
!.env.*.example
!.env.*.template
!.env.*.sample

# SSH 및 인증서 파일들
*.pem
*.key
*.p12
*.pfx
*.jks
*.keystore
```

### 🔧 추천 도구들

#### 1. direnv (자동 환경변수 로드)
```bash
# 설치
brew install direnv

# .envrc 파일 생성
echo "source .env" > .envrc
direnv allow
```

#### 2. 1Password CLI (보안 저장소)
```bash
# 설치
brew install 1password-cli

# 사용 예
op item get "OpenAI API Key" --fields password
```

## 🔍 개발 보안 가이드라인

### 코드 작성 시
1. **하드코딩 금지**: API 키, 비밀번호 등을 코드에 직접 입력 금지
2. **환경변수 사용**: 모든 민감정보는 환경변수로 관리
3. **입력 검증**: 모든 외부 입력에 대한 검증 및 살균
4. **에러 메시지**: 민감정보가 포함된 에러 메시지 출력 금지
5. **로그 관리**: 민감정보를 로그에 기록하지 않음

### 좋은 예시
```python
import os
from typing import Optional

class APIClient:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다")
    
    def make_request(self, data: dict) -> dict:
        # 민감정보 마스킹된 로그
        masked_key = f"{self.api_key[:8]}...{self.api_key[-4:]}"
        logger.info(f"API 요청 - 키: {masked_key}")
```

### 나쁜 예시
```python
# ❌ 절대 하지 말 것
class APIClient:
    def __init__(self):
        self.api_key = "sk-실제API키값"  # 하드코딩 금지!
    
    def make_request(self, data: dict) -> dict:
        logger.info(f"API Key: {self.api_key}")  # 로그에 민감정보 노출 금지!
```

## 🤖 자동화된 보안 검사

### 1. Pre-commit Hook
커밋 전 자동으로 보안 검사 실행:

```bash
# 수동으로 pre-commit hook 테스트
.git/hooks/pre-commit
```

### 2. 보안 스크립트
전체 프로젝트 보안 검사:

```bash
# 기본 실행
./scripts/security-check.sh

# 자세한 출력
./scripts/security-check.sh --verbose

# 검사 패턴 확인
./scripts/security-check.sh --patterns
```

### 3. Gitleaks 사용
```bash
# Gitleaks 설치
brew install gitleaks

# 전체 저장소 스캔
gitleaks detect --config .gitleaks.toml

# 특정 커밋 스캔
gitleaks protect --config .gitleaks.toml
```

### 4. GitHub Actions (향후 추가 예정)
```yaml
# .github/workflows/security.yml
name: Security Scan
on: [push, pull_request]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## 🚨 사고 대응 절차

### 1. API 키/비밀번호 노출 시 즉시 조치

#### 단계 1: 즉시 무효화
```bash
# 1. 해당 API 키 즉시 무효화/재발급
# - OpenAI: https://platform.openai.com/api-keys
# - Google: https://console.cloud.google.com/apis/credentials
# - Anthropic: https://console.anthropic.com/
# - Naver: https://developers.naver.com/apps/

# 2. 새로운 키로 로컬 환경변수 업데이트
echo "NEW_API_KEY=새로운키값" > .env
```

#### 단계 2: Git 히스토리 정리
```bash
# BFG Repo-Cleaner 설치
brew install bfg

# 민감한 파일 히스토리에서 완전 제거
git clone --mirror https://github.com/사용자/저장소.git
bfg --replace-text passwords.txt 저장소.git
cd 저장소.git
git reflog expire --expire=now --all && git gc --prune=now --aggressive
git push --force
```

#### 단계 3: 영향 범위 분석
```bash
# 언제 노출되었는지 확인
git log --oneline --grep="키워드" --all

# 어떤 브랜치에 영향을 줬는지 확인
git branch --contains 커밋해시
```

### 2. 보안 취약점 발견 시

#### 내부 발견
1. 즉시 수정 작업 시작
2. 영향 범위 분석
3. 패치 개발 및 테스트
4. 업데이트 배포

#### 외부 신고
1. security@vault-intelligence.com으로 연락
2. 90일 책임 공개 원칙 적용
3. 신고자와 협력하여 수정
4. 수정 후 공개 감사

## 🛠️ 보안 도구 사용법

### 1. 보안 스크립트 활용

#### 기본 사용법
```bash
# 전체 보안 검사
./scripts/security-check.sh

# 결과:
# ✅ 보안 문제가 발견되지 않았습니다!
# 또는
# ❌ 3개의 보안 문제가 발견되었습니다.
```

#### 고급 옵션
```bash
# 자세한 출력 (디버그 모드)
./scripts/security-check.sh --verbose

# 검사 패턴 목록 확인
./scripts/security-check.sh --patterns

# 전체 보안 검사를 pre-commit에서 실행
export RUN_FULL_SECURITY_CHECK=true
git commit -m "테스트 커밋"
```

### 2. Pre-commit Hook 제어

#### 임시 비활성화
```bash
# 한 번만 비활성화 (권장하지 않음)
git commit --no-verify -m "긴급 수정"
```

#### 영구 비활성화
```bash
# pre-commit hook 비활성화 (권장하지 않음)
chmod -x .git/hooks/pre-commit
```

#### 다시 활성화
```bash
# pre-commit hook 다시 활성화
chmod +x .git/hooks/pre-commit
```

### 3. Gitleaks 설정

#### 커스텀 패턴 추가
`.gitleaks.toml` 파일에 새 규칙 추가:

```toml
[[rules]]
id = "custom-api-key"
description = "Custom Service API Key"
regex = '''custom-[a-zA-Z0-9]{32}'''
tags = ["api-key", "custom-service"]
```

#### 허용 목록 관리
```toml
[allowlist]
paths = [
    "docs/**",
    "*.example",
    "*.template"
]

regexes = [
    '''your_api_key_here''',
    '''example_.*_key''',
]
```

## ❓ FAQ

### Q: .env 파일이 실수로 커밋되었어요!
**A:** 즉시 다음 절차를 따르세요:
1. API 키들을 모두 재발급
2. `git rm --cached .env`로 추적 해제
3. `.gitignore`에 `.env` 추가
4. BFG Repo-Cleaner로 히스토리 정리

### Q: Pre-commit hook이 너무 느려요
**A:** 다음 방법을 시도해보세요:
1. `RUN_FULL_SECURITY_CHECK=false`로 설정 (기본값)
2. 대용량 파일들을 `.gitignore`에 추가
3. 필요시 `git commit --no-verify` 사용 (주의 필요)

### Q: False positive가 너무 많아요
**A:** `.gitleaks.toml` 파일의 `allowlist` 섹션을 조정하세요:
```toml
regexes = [
    '''your_pattern_here''',
]
```

### Q: 팀 전체에 어떻게 적용하나요?
**A:**
1. 모든 팀원이 저장소를 새로 clone
2. pre-commit hooks가 자동으로 적용됨
3. 보안 교육 및 가이드라인 공유
4. 정기적인 보안 리뷰 실시

### Q: CI/CD에서 보안 검사를 어떻게 하나요?
**A:** GitHub Actions를 설정하여 자동화:
```yaml
- name: Security Scan
  run: |
    ./scripts/security-check.sh
    gitleaks detect --config .gitleaks.toml
```

## 📞 연락처

- **보안 문제 신고**: security@vault-intelligence.com
- **일반 문의**: support@vault-intelligence.com
- **긴급 사안**: 이슈 트래커에 '[SECURITY]' 태그 사용

## 📚 참고 자료

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
- [Gitleaks Documentation](https://github.com/gitleaks/gitleaks)
- [Python Security Guidelines](https://python-security.readthedocs.io/)

---

**마지막 업데이트**: 2025-01-08  
**다음 리뷰**: 2025-04-08  

이 문서는 정기적으로 업데이트됩니다. 보안은 모든 개발자의 책임입니다! 🛡️