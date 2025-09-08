#!/bin/bash

# 민감정보 감지 스크립트
# vault-intelligence 프로젝트용 보안 체크

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수들
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# 스크립트 디렉토리 찾기
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

log_info "프로젝트 루트: $PROJECT_ROOT"
cd "$PROJECT_ROOT"

# 검사할 파일 패턴들
SENSITIVE_PATTERNS=(
    # API 키 패턴
    "sk-[a-zA-Z0-9]{32,}"                    # OpenAI API 키
    "AIza[a-zA-Z0-9_-]{35}"                  # Google API 키
    "sk-ant-[a-zA-Z0-9_-]{95,}"              # Anthropic API 키
    "xoxb-[a-zA-Z0-9]+"                      # Slack Bot 토큰
    "xoxp-[a-zA-Z0-9]+"                      # Slack User 토큰
    "ghp_[a-zA-Z0-9]{36}"                    # GitHub Personal Access Token
    "gho_[a-zA-Z0-9]{36}"                    # GitHub OAuth Token
    "ghu_[a-zA-Z0-9]{36}"                    # GitHub User Token
    "ghs_[a-zA-Z0-9]{36}"                    # GitHub Server Token
    "ghr_[a-zA-Z0-9]{36}"                    # GitHub Refresh Token
    
    # AWS 패턴 (실제 값만)
    "AKIA[0-9A-Z]{16}"                       # AWS Access Key ID
    "AWS_SECRET_ACCESS_KEY\s*[:=]\s*['\"][^'\"]{20,}['\"]"  # 실제 AWS Secret Key 할당
    
    # 네이버 API (실제 환경변수 할당만)
    "NAVER_CLIENT_ID\s*[:=]\s*['\"]?[a-zA-Z0-9]{15,}['\"]?"
    "NAVER_CLIENT_SECRET\s*[:=]\s*['\"]?[a-zA-Z0-9_-]{10,}['\"]?"
    
    # 일반적인 시크릿 패턴 (실제 값이 있는 경우만)
    "password\s*[:=]\s*['\"][^'\"]{8,}['\"]"
    "secret\s*[:=]\s*['\"][^'\"]{8,}['\"]"  
    "token\s*[:=]\s*['\"][^'\"]{16,}['\"]"
    "api_key\s*[:=]\s*['\"][^'\"]{16,}['\"]"
    
    # 암호화폐 지갑
    "0x[a-fA-F0-9]{40}"                      # Ethereum address
    "[13][a-km-zA-HJ-NP-Z1-9]{25,34}"       # Bitcoin address
    
    # JWT 토큰
    "eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*"
)

# 위험한 파일 확장자
DANGEROUS_EXTENSIONS=(
    "*.pem"
    "*.key"
    "*.p12"
    "*.pfx"
    "*.jks"
    "*.keystore"
)

# 환경변수 파일 패턴 (템플릿 제외)
ENV_FILE_PATTERNS=(
    "\.env$"
    "\.env\.[^.]*$"
)

# 제외할 디렉토리
EXCLUDE_DIRS=(
    ".git"
    "node_modules"
    ".venv"
    "__pycache__"
    ".pytest_cache"
    "cache"
    "models"
    ".claude"
    "samples"
)

# 제외할 파일
EXCLUDE_FILES=(
    "*.example"
    "*.template"
    "*.sample" 
    "*.lock"
    "package-lock.json"
    "yarn.lock"
    "security-check.sh"  # 보안 스크립트 자체 제외
    "*.md"               # 문서 파일 제외
    ".gitleaks.toml"     # 설정 파일 제외
)

# 감지된 문제 카운터
ISSUES_FOUND=0

# 파일이 제외 대상인지 확인
is_excluded() {
    local file="$1"
    local filename=$(basename "$file")
    
    # 제외 디렉토리 확인
    for exclude_dir in "${EXCLUDE_DIRS[@]}"; do
        if [[ "$file" == *"$exclude_dir"* ]]; then
            return 0
        fi
    done
    
    # 제외 파일 패턴 확인
    for exclude_pattern in "${EXCLUDE_FILES[@]}"; do
        case "$exclude_pattern" in
            *.*)
                # 확장자 패턴 (*.md, *.example 등)
                if [[ "$filename" == $exclude_pattern ]]; then
                    return 0
                fi
                ;;
            *)
                # 정확한 파일명
                if [[ "$filename" == "$exclude_pattern" ]]; then
                    return 0
                fi
                ;;
        esac
    done
    
    return 1
}

# 민감 패턴 검사
check_sensitive_patterns() {
    log_info "민감한 패턴 검사 중..."
    
    while IFS= read -r -d '' file; do
        if is_excluded "$file"; then
            continue
        fi
        
        # 바이너리 파일 건너뛰기
        if ! file "$file" | grep -q "text"; then
            continue
        fi
        
        for pattern in "${SENSITIVE_PATTERNS[@]}"; do
            if grep -l -E "$pattern" "$file" 2>/dev/null; then
                log_error "민감한 패턴 발견: $file"
                echo "  패턴: $pattern"
                ISSUES_FOUND=$((ISSUES_FOUND + 1))
                break
            fi
        done
    done < <(find . -type f -print0)
}

# 환경변수 파일 검사
check_env_files() {
    log_info "환경변수 파일 검사 중..."
    
    for pattern in "${ENV_FILE_PATTERNS[@]}"; do
        while IFS= read -r file; do
            # 템플릿/예제 파일 제외
            if [[ "$file" == *.example ]] || [[ "$file" == *.template ]] || [[ "$file" == *.sample ]]; then
                continue
            fi
            
            if [[ -f "$file" ]]; then
                log_error "환경변수 파일 발견: $file"
                log_warn "이 파일이 git에 추적되고 있는지 확인하세요."
                ISSUES_FOUND=$((ISSUES_FOUND + 1))
            fi
        done < <(find . -type f -regex ".*/$pattern" 2>/dev/null)
    done
}

# 위험한 파일 확장자 검사
check_dangerous_files() {
    log_info "위험한 파일 확장자 검사 중..."
    
    for extension in "${DANGEROUS_EXTENSIONS[@]}"; do
        while IFS= read -r file; do
            if is_excluded "$file"; then
                continue
            fi
            
            log_error "위험한 파일 발견: $file"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
        done < <(find . -name "$extension" -type f 2>/dev/null)
    done
}

# Git 추적 상태 검사
check_git_tracking() {
    log_info "Git 추적 상태 검사 중..."
    
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_warn "Git 저장소가 아닙니다."
        return
    fi
    
    # 위험한 파일이 추적되는지 확인
    for pattern in "${ENV_FILE_PATTERNS[@]}"; do
        while IFS= read -r file; do
            # 템플릿/예제 파일 제외
            if [[ "$file" == *.example ]] || [[ "$file" == *.template ]] || [[ "$file" == *.sample ]]; then
                continue
            fi
            
            if git ls-files --error-unmatch "$file" >/dev/null 2>&1; then
                log_error "환경변수 파일이 Git에 추적되고 있습니다: $file"
                log_warn "즉시 다음 명령을 실행하세요: git rm --cached '$file'"
                ISSUES_FOUND=$((ISSUES_FOUND + 1))
            fi
        done < <(find . -type f -regex ".*/$pattern" 2>/dev/null)
    done
}

# 대용량 파일 검사
check_large_files() {
    log_info "대용량 파일 검사 중 (10MB 이상)..."
    
    while IFS= read -r -d '' file; do
        if is_excluded "$file"; then
            continue
        fi
        
        size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
        if [[ $size -gt 10485760 ]]; then  # 10MB
            size_mb=$((size / 1024 / 1024))
            log_warn "대용량 파일 발견: $file (${size_mb}MB)"
            log_warn "이 파일이 정말 필요한지 확인하세요."
        fi
    done < <(find . -type f -print0)
}

# Git 히스토리 검사 (간단한 체크)
check_git_history() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        return
    fi
    
    log_info "Git 히스토리 간단 검사 중..."
    
    # 최근 10개 커밋에서 민감한 키워드 검사
    if git log --oneline -10 | grep -i -E "(password|secret|key|token|api)" >/dev/null 2>&1; then
        log_warn "최근 커밋 메시지에 민감한 키워드가 포함되어 있습니다."
        log_info "자세한 검사: git log --grep='password\\|secret\\|key\\|token\\|api' -i"
    fi
}

# 메인 실행 함수
main() {
    echo "========================================"
    echo "🔒 보안 체크 시작"
    echo "========================================"
    
    check_sensitive_patterns
    check_env_files
    check_dangerous_files
    check_git_tracking
    check_large_files
    check_git_history
    
    echo "========================================"
    if [[ $ISSUES_FOUND -eq 0 ]]; then
        log_success "✅ 보안 문제가 발견되지 않았습니다!"
    else
        log_error "❌ $ISSUES_FOUND개의 보안 문제가 발견되었습니다."
        echo ""
        echo "해결 방법:"
        echo "1. 민감한 정보가 포함된 파일을 .gitignore에 추가"
        echo "2. 이미 커밋된 파일은 'git rm --cached <파일>' 실행"
        echo "3. API 키가 노출된 경우 즉시 재발급"
        echo "4. git filter-branch나 BFG Repo-Cleaner로 히스토리 정리 고려"
        exit 1
    fi
    echo "========================================"
}

# 도움말 표시
show_help() {
    echo "사용법: $0 [옵션]"
    echo ""
    echo "옵션:"
    echo "  -h, --help     도움말 표시"
    echo "  -v, --verbose  자세한 출력"
    echo "  --patterns     검사하는 패턴 목록 표시"
    echo ""
    echo "예제:"
    echo "  $0              # 기본 보안 체크 실행"
    echo "  $0 --verbose    # 자세한 출력과 함께 실행"
    echo "  $0 --patterns   # 검사 패턴 목록 표시"
}

# 패턴 목록 표시
show_patterns() {
    echo "검사하는 민감 정보 패턴:"
    echo "========================"
    for pattern in "${SENSITIVE_PATTERNS[@]}"; do
        echo "- $pattern"
    done
    echo ""
    echo "위험한 파일 확장자:"
    echo "=================="
    for ext in "${DANGEROUS_EXTENSIONS[@]}"; do
        echo "- $ext"
    done
}

# 명령행 인수 처리
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    --patterns)
        show_patterns
        exit 0
        ;;
    -v|--verbose)
        set -x
        main
        ;;
    "")
        main
        ;;
    *)
        echo "알 수 없는 옵션: $1"
        show_help
        exit 1
        ;;
esac