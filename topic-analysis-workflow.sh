#!/bin/bash
# topic-analysis-workflow.sh

TOPIC=$1
OUTPUT_DIR="./analysis-results"

if [ -z "$TOPIC" ]; then
    echo "사용법: $0 <주제명>"
    exit 1
fi

echo "📋 $TOPIC 주제 분석 시작..."

# 출력 디렉토리 생성
mkdir -p "$OUTPUT_DIR"

# 1. 기본 수집
echo "1️⃣ 기본 문서 수집..."
vis collect --topic "$TOPIC" --output "$OUTPUT_DIR/${TOPIC}-topics.md"

# 2. 확장 검색
echo "2️⃣ 확장 검색 실행..."
vis search --query "$TOPIC" --top-k 15 > "$OUTPUT_DIR/${TOPIC}-search-results.txt"

# 3. 영문 검색 (필요시)
echo "3️⃣ 영문 검색 실행..."
vis search --query "$TOPIC english equivalent" --top-k 10 >> "$OUTPUT_DIR/${TOPIC}-search-results.txt"

echo "✅ $TOPIC 주제 분석 완료!"
echo "📁 결과 파일: $OUTPUT_DIR/${TOPIC}-topics.md"
echo "📄 검색 결과: $OUTPUT_DIR/${TOPIC}-search-results.txt"