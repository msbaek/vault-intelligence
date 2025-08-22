# 🔧 문제 해결 가이드

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
python -m src init --vault-path /path/to/vault
```

### 메모리 부족

**증상**: 대용량 vault 처리 중 메모리 부족 오류

**해결 방법**:
```bash
# 샘플링 사용
python -m src search --query "test" --sample-size 100

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
python -m src search --query "test" --sample-size 500
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

## 자주 묻는 질문

### Q: 시각화가 너무 오래 걸려요
**A**: 샘플링을 사용하세요:
```python
engine.build_index(sample_size=50)  # 50개 문서만 사용
```

### Q: 한글 외에 다른 언어도 지원하나요?
**A**: BGE-M3는 다국어를 지원하지만, 시각화 폰트는 별도 설정이 필요합니다.

### Q: 그래프를 웹에서 볼 수 있나요?
**A**: 현재는 PNG 파일만 지원합니다. JSON 데이터를 이용해 웹 시각화도 가능합니다.

---

문제가 해결되지 않으면 [GitHub Issues](https://github.com/your-repo/vault-intelligence/issues)에 보고해주세요.