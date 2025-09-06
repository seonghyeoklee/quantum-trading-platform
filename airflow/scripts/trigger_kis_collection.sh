#!/bin/bash
# KIS 데이터 수집 DAG 수동 트리거 스크립트
# 
# 사용법:
# ./trigger_kis_collection.sh "005930,000660" "price,chart"
# 
# Author: Quantum Trading Platform

set -e

# Airflow 설정
AIRFLOW_URL="http://localhost:8081"
AIRFLOW_USERNAME="admin"
AIRFLOW_PASSWORD="quantum123"
DAG_ID="kis_data_collection"

# 파라미터 설정
SYMBOLS=${1:-"005930,000660,035720"}  # 기본값: 삼성전자, SK하이닉스, 카카오
DATA_TYPES=${2:-"price,chart"}         # 기본값: 현재가, 차트
CHART_PERIOD=${3:-"D"}                 # 기본값: 일봉
CHART_COUNT=${4:-100}                  # 기본값: 100개

echo "🚀 KIS 데이터 수집 DAG 실행"
echo "📈 종목 코드: $SYMBOLS"
echo "📊 데이터 타입: $DATA_TYPES"
echo "⏰ 차트 기간: $CHART_PERIOD"
echo "🔢 차트 개수: $CHART_COUNT"
echo ""

# 타임스탬프 생성
TIMESTAMP=$(date +%s)
LOGICAL_DATE=$(date -u +%Y-%m-%dT%H:%M:%S)Z
DAG_RUN_ID="manual_kis_collection_${TIMESTAMP}"

# DAG 실행을 위한 JSON 페이로드 생성
JSON_PAYLOAD=$(cat <<EOF
{
    "dag_run_id": "$DAG_RUN_ID",
    "logical_date": "$LOGICAL_DATE",
    "conf": {
        "symbols": "$SYMBOLS",
        "data_types": "$DATA_TYPES",
        "chart_period": "$CHART_PERIOD",
        "chart_count": $CHART_COUNT
    }
}
EOF
)

echo "📤 DAG 실행 요청 중..."
echo "🆔 실행 ID: $DAG_RUN_ID"

# Airflow REST API 호출
RESPONSE=$(curl -s -X POST \
    "$AIRFLOW_URL/api/v1/dags/$DAG_ID/dagRuns" \
    -H "Content-Type: application/json" \
    -H "Authorization: Basic $(echo -n "${AIRFLOW_USERNAME}:${AIRFLOW_PASSWORD}" | base64)" \
    -d "$JSON_PAYLOAD" \
    -w "\nHTTP_CODE:%{http_code}")

# 응답 파싱
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE:/d')

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ DAG 실행 성공!"
    echo "📊 응답: $RESPONSE_BODY"
    echo ""
    echo "🌐 Airflow UI에서 진행상황을 확인하세요:"
    echo "   $AIRFLOW_URL/dags/$DAG_ID/grid"
    echo ""
    echo "📋 실행 로그 확인:"
    echo "   $AIRFLOW_URL/dags/$DAG_ID/grid?dag_run_id=$DAG_RUN_ID"
else
    echo "❌ DAG 실행 실패! (HTTP $HTTP_CODE)"
    echo "🔍 오류 응답: $RESPONSE_BODY"
    exit 1
fi

echo ""
echo "⏱️ 대기 시간: 약 2-5분 소요 예상"
echo "📈 수집 예정 데이터:"

# 종목별 예상 데이터 계산
IFS=',' read -ra SYMBOL_ARRAY <<< "$SYMBOLS"
IFS=',' read -ra TYPE_ARRAY <<< "$DATA_TYPES"

TOTAL_REQUESTS=$((${#SYMBOL_ARRAY[@]} * ${#TYPE_ARRAY[@]}))
echo "   - 종목 수: ${#SYMBOL_ARRAY[@]}"
echo "   - 데이터 타입 수: ${#TYPE_ARRAY[@]}"
echo "   - 총 요청 수: $TOTAL_REQUESTS"

if [[ "$DATA_TYPES" == *"chart"* ]]; then
    CHART_RECORDS=$((${#SYMBOL_ARRAY[@]} * $CHART_COUNT))
    echo "   - 예상 차트 레코드 수: $CHART_RECORDS"
fi