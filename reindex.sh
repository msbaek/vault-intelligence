#!/bin/bash

# 폴더별 재인덱싱 스크립트
# 각 폴더 완료 후 30초 대기하여 시스템 부하 분산

folders=("997-BOOKS" "000-SLIPBOX" "105-PROJECTS" "001-INBOX" "work-log" "998-PRIVATE" "notes" "003-RESOURCES")
total_folders=${#folders[@]}
current=1

echo "🚀 폴더별 재인덱싱 시작: 총 ${total_folders}개 폴더"
echo "=================================================="

for folder in "${folders[@]}"; do
    echo ""
    echo "📁 [$current/$total_folders] 폴더 처리 시작: $folder"
    echo "⏰ 시작 시간: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "--------------------------------------------------"
    
    # 재인덱싱 실행
    vis reindex --force --with-colbert --include-folders "$folder"
    
    # 결과 확인
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ [$current/$total_folders] 완료: $folder"
    else
        echo ""
        echo "❌ [$current/$total_folders] 실패: $folder"
    fi
    
    echo "⏰ 완료 시간: $(date '+%Y-%m-%d %H:%M:%S')"
    
    # 마지막 폴더가 아니면 30초 대기
    if [ $current -lt $total_folders ]; then
        echo ""
        echo "⏳ 다음 폴더 처리를 위해 30초 대기 중..."
        echo "   (시스템 부하 완화 및 안정화)"
        
        # 30초 카운트다운
        for i in {30..1}; do
            printf "\r   남은 시간: %2d초" $i
            sleep 1
        done
        printf "\r   ✨ 대기 완료!     \n"
        echo "=================================================="
    fi
    
    current=$((current + 1))
done

echo ""
echo "🎉 전체 폴더별 재인덱싱 완료!"
echo "⏰ 전체 완료 시간: $(date '+%Y-%m-%d %H:%M:%S')"
echo "📊 처리된 폴더: ${total_folders}개"
