# 🔧 문제 해결 가이드

## 📖 문서 내비게이션
- [🏠 프로젝트 홈](../README.md) | [🚀 빠른 시작](QUICK_START.md) | [📚 사용자 가이드](USER_GUIDE.md) | [💡 실전 예제](EXAMPLES.md) | **🔧 문제 해결** | [⚙️ 개발자 가이드](../CLAUDE.md)

---

Vault Intelligence System V2 사용 중 발생할 수 있는 문제들과 해결 방법을 정리합니다.

## 지식 그래프 시각화 문제

### 한글 폰트 깨짐 현상

**증상**: 지식 그래프 시각화에서 한글 제목이 깨져서 표시됨 (□□□ 형태)

**원인**: matplotlib이 한글을 지원하지 않는 기본 폰트(DejaVu Sans)를 사용

**해결 방법**:
1. **자동 해결**: `visualize_knowledge_graph.py` 실행 시 자동으로 시스템 폰트 감지
2. **수동 설정**: 운영체제별 폰트 설정

#### macOS 환경
```python
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# AppleGothic 폰트 적용
font_path = '/System/Library/Fonts/Supplemental/AppleGothic.ttf'
font_prop = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = font_prop.get_name()
plt.rcParams['axes.unicode_minus'] = False
```

#### Windows 환경
```python
import matplotlib.pyplot as plt

# Malgun Gothic 폰트 적용
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
```

#### Linux 환경
```python
import matplotlib.pyplot as plt

# 나눔고딕 설치 후 사용
plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False
```

### 그래프가 생성되지 않는 문제

**증상**: 노드 0개, 엣지 0개로 빈 그래프 생성

**원인**: 
1. 임베딩이 제대로 로드되지 않음
2. 유사도 임계값이 너무 높음
3. 최소 단어 수 조건을 만족하는 문서가 없음

**해결 방법**:
```python
# 1. 임베딩 상태 확인
python -c "
import sqlite3
conn = sqlite3.connect('cache/embeddings.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM embeddings WHERE embedding IS NOT NULL')
print(f'유효한 임베딩: {cursor.fetchone()[0]}개')
conn.close()
"

# 2. 유사도 임계값 낮추기
knowledge_graph = graph_builder.build_graph(
    similarity_threshold=0.3,  # 기본값 0.4에서 낮춤
    include_tag_nodes=False    # 태그 노드 제외로 단순화
)

# 3. 최소 단어 수 조건 완화
config['knowledge_graph']['min_word_count'] = 20  # 기본값 50에서 낮춤
```

## 임베딩 캐시 문제

### 캐시 손상

**증상**: 임베딩 로드 시 오류 발생

**해결 방법**:
```bash
# 캐시 삭제 후 재구축
rm -rf cache/
vis init --vault-path /path/to/vault
```

### 메모리 부족

**증상**: 대용량 vault 처리 중 메모리 부족 오류

**해결 방법**:
```bash
# 샘플링 사용
vis search "test" --sample-size 100

# 배치 크기 줄이기 (config/settings.yaml)
model:
  batch_size: 4  # 기본값 8에서 감소
```

## 검색 성능 문제

### 검색 속도 느림

**해결 방법**:
1. **MPS 가속 활성화** (M1 Mac):
```yaml
# config/settings.yaml
model:
  device: 'mps'
  use_fp16: true
```

2. **배치 크기 최적화**:
```yaml
model:
  batch_size: 8  # GPU 메모리에 따라 조정
```

3. **샘플링 사용**:
```bash
vis search "test" --sample-size 500
```

## 설치 문제

### 의존성 설치 실패

**해결 방법**:
```bash
# Python 3.8+ 확인
python --version

# 의존성 개별 설치
pip install numpy scikit-learn pyyaml
pip install matplotlib networkx  # 시각화용
pip install FlagEmbedding  # BGE-M3 모델용
```

### M1 Mac 호환성 문제

**해결 방법**:
```bash
# ARM64 호환 Python 사용
arch -arm64 python -m pip install -r requirements.txt

# Conda 환경 사용 권장
conda create -n vault-intelligence python=3.11
conda activate vault-intelligence
pip install -r requirements.txt
```

## 로그 확인

문제 진단을 위한 상세 로그:

```bash
# 디버그 모드 실행
export PYTHONPATH=/path/to/vault-intelligence
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
# 문제가 되는 코드 실행
"
```

## ColBERT 관련 문제

### ColBERT 배열 크기 불일치 경고

**증상**: ColBERT 검색 시 다음과 같은 경고 메시지 대량 발생
```
WARNING:src.core.embedding_cache:ColBERT 배열 크기 불일치: 2444288 != 524288
```

**원인**: 이전 버전에서 생성된 ColBERT 캐시의 메타데이터 불일치

**해결 방법**: ✅ **2025-08-27 완전 수정됨**
```bash
# 캐시 완전 초기화 후 재인덱싱
rm -rf cache/
vis reindex --with-colbert --force

# 수정된 코드로 새로 생성되는 모든 임베딩은 정상
```

### ColBERT + 재순위화 오류

**증상**: `--rerank` 옵션과 ColBERT 함께 사용 시 오류
```
❌ 지원하지 않는 검색 방법: colbert
❌ 검색 실패!
```

**해결 방법**: ✅ **2025-08-27 수정 완료**
```bash
# 이제 모든 검색 방법에서 재순위화 지원
vis search "TDD" --search-method colbert --rerank ✅
vis search "TDD" --search-method hybrid --rerank ✅ 
vis search "TDD" --search-method semantic --rerank ✅
```

### ColBERT 검색 결과 품질 문제

**증상**: 단일 키워드(예: "YAGNI") 검색 시 관련 없는 결과 많이 반환

**원인**: ColBERT의 토큰 레벨 매칭 특성상 단일 약어는 많은 무관한 토큰과 유사도 매칭

**해결 방법**:
```bash
# 1. 하이브리드 검색 사용 (권장)
vis search "YAGNI" --search-method hybrid

# 2. 확장된 쿼리 사용  
vis search "YAGNI You Aren't Going to Need It principle" --search-method colbert

# 3. 재순위화 적용
vis search "YAGNI" --search-method hybrid --rerank
```

**ColBERT 적합한 사용 케이스**:
- ✅ 긴 문장: "test driven development best practices"
- ✅ 복합 개념: "clean architecture dependency inversion"  
- ❌ 단일 약어: "TDD", "YAGNI", "DDD"

## 서버 모드 (Daemon) 문제

### 데몬이 시작되지 않는 경우

**증상**: `visd start` 실행 시 포트 충돌 또는 시작 실패

**해결 방법**:
```bash
# 1. 포트 사용 여부 확인
lsof -i :8741

# 2. 좀비 PID 파일 정리
rm ~/.vis-server.pid

# 3. 로그 확인
visd logs
```

### 데몬이 응답하지 않는 경우

**증상**: `visd status`에서 실행 중이지만 검색이 안 됨

**해결 방법**:
```bash
# 1. 헬스 체크 직접 확인
curl http://localhost:8741/health

# 2. 재시작
visd restart
```

### PID 파일이 남아있는 경우

**증상**: `visd status`에서 실행 중으로 표시되지만 실제 프로세스는 없음

**해결 방법**:
```bash
# PID 파일 수동 삭제 후 재시작
rm ~/.vis-server.pid
visd start
```

### 검색 시 "visd가 실행 중이 아닙니다" 오류

**증상**: `vis search` 실행 시 데몬 미실행 오류

**해결 방법**:
```bash
# 데몬 시작
visd start

# 상태 확인
visd status
```

---

## 자주 묻는 질문

### Q: 시각화가 너무 오래 걸려요
**A**: 샘플링을 사용하세요:
```python
engine.build_index(sample_size=50)  # 50개 문서만 사용
```

### Q: 어떤 검색 방법을 언제 사용해야 하나요?
**A**: 
- **일반 검색**: `--search-method hybrid` (기본값, 추천)
- **개념 검색**: `--search-method semantic` 
- **정확한 용어**: `--search-method keyword`
- **긴 문장**: `--search-method colbert`
- **고품질 검색**: `--rerank` 추가 (모든 방법과 조합 가능)

### Q: 재순위화(--rerank)는 언제 사용하나요?
**A**: 
- ✅ 전문 지식 검색 (기술 문서, 학술 자료)
- ✅ 정밀도가 중요한 경우 (소수의 정확한 결과)
- ❌ 단순 키워드나 실시간 검색 (속도 중시)

### Q: visd는 항상 실행해야 하나요?
**A**: 네, `vis search`는 visd 데몬이 필요합니다. `visd start`로 시작하면 백그라운드에서 실행되므로 한 번 시작하면 됩니다.

### Q: 서버 모드 메모리 사용량은?
**A**: 약 2-4GB 메모리를 상주 사용합니다 (vault 크기에 따라 변동). 8GB 이상 RAM 환경에서 권장합니다.

### Q: 한글 외에 다른 언어도 지원하나요?
**A**: BGE-M3는 다국어를 지원하지만, 시각화 폰트는 별도 설정이 필요합니다.

### Q: 그래프를 웹에서 볼 수 있나요?
**A**: 현재는 PNG 파일만 지원합니다. JSON 데이터를 이용해 웹 시각화도 가능합니다.

---

문제가 해결되지 않으면 [GitHub Issues](https://github.com/your-repo/vault-intelligence/issues)에 보고해주세요.