#!/bin/bash

# DINO 점수 일관성 테스트 스크립트
# 삼성전자(005930) 통합 분석을 5번 실행하여 점수 일관성 확인

echo "=== DINO 점수 일관성 테스트 시작 ==="
echo "종목: 삼성전자 (005930)"
echo "테스트 횟수: 5회"
echo ""

BASE_URL="http://localhost:8080"
STOCK_CODE="005930"

# 결과를 저장할 임시 파일들
TEMP_DIR="/tmp/dino_test_$$"
mkdir -p "$TEMP_DIR"

echo "테스트 실행 중..."

for i in {1..5}; do
    echo -n "테스트 $i 실행 중... "

    # 통합 분석 POST 요청 실행
    RESULT=$(curl -s -X POST "$BASE_URL/dino/integrated/analyze" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "stockCode=$STOCK_CODE" \
        -L)

    # 총점 추출 (20점 만점)
    TOTAL_SCORE=$(echo "$RESULT" | grep -oE '총점.*?[0-9]+' | grep -oE '[0-9]+' | head -1)

    if [ -n "$TOTAL_SCORE" ]; then
        echo "완료 - 총점: $TOTAL_SCORE/20"
        echo "$TOTAL_SCORE" >> "$TEMP_DIR/scores.txt"
    else
        echo "실패 - 점수 추출 불가"
        echo "ERROR" >> "$TEMP_DIR/scores.txt"
    fi

    # 각 실행 간 짧은 대기
    sleep 1
done

echo ""
echo "=== 테스트 결과 분석 ==="

if [ -f "$TEMP_DIR/scores.txt" ]; then
    echo "획득한 점수들:"
    cat "$TEMP_DIR/scores.txt" | nl

    echo ""

    # 점수의 고유값 개수 확인
    UNIQUE_SCORES=$(cat "$TEMP_DIR/scores.txt" | grep -v "ERROR" | sort | uniq | wc -l)
    TOTAL_TESTS=$(cat "$TEMP_DIR/scores.txt" | grep -v "ERROR" | wc -l)

    if [ "$TOTAL_TESTS" -gt 0 ]; then
        echo "성공한 테스트: $TOTAL_TESTS/5"
        echo "고유 점수 개수: $UNIQUE_SCORES"

        if [ "$UNIQUE_SCORES" -eq 1 ]; then
            echo "✅ 점수 일관성 테스트 PASS - 모든 실행에서 동일한 점수"
        else
            echo "❌ 점수 일관성 테스트 FAIL - 실행마다 다른 점수"
            echo "점수 분포:"
            cat "$TEMP_DIR/scores.txt" | grep -v "ERROR" | sort | uniq -c
        fi
    else
        echo "❌ 모든 테스트 실패"
    fi
else
    echo "❌ 테스트 결과 파일을 찾을 수 없음"
fi

# 임시 파일 정리
rm -rf "$TEMP_DIR"

echo ""
echo "=== DINO 점수 일관성 테스트 완료 ==="