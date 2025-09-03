#!/bin/bash

# 테스트 로그를 Loki에 직접 전송하는 스크립트

LOKI_URL="http://localhost:3100/loki/api/v1/push"

echo "🧪 테스트 로그를 Loki에 전송합니다..."

# 현재 시간을 나노초로 변환
TIMESTAMP=$(date +%s)000000000

# 다양한 로그 레벨과 서비스의 테스트 로그 생성
send_log() {
    local service="$1"
    local level="$2"
    local message="$3"
    
    cat << EOF | curl -s -X POST "$LOKI_URL" \
        -H "Content-Type: application/json" \
        --data-binary @-
{
    "streams": [
        {
            "stream": {
                "job": "$service",
                "service": "$service",
                "level": "$level",
                "environment": "development"
            },
            "values": [
                ["$TIMESTAMP", "{\"timestamp\":\"$(date -u --iso-8601=seconds)\",\"level\":\"$level\",\"message\":\"$message\",\"service\":\"$service\",\"logger\":\"test\"}"]
            ]
        }
    ]
}
EOF
    
    if [ $? -eq 0 ]; then
        echo "   ✅ $service ($level): $message"
    else
        echo "   ❌ $service ($level): 전송 실패"
    fi
}

# Spring Boot API 테스트 로그들
echo "📦 quantum-web-api 로그 전송..."
send_log "quantum-web-api" "INFO" "Spring Boot API 서버가 시작되었습니다"
send_log "quantum-web-api" "INFO" "JWT 토큰 인증이 성공했습니다"
send_log "quantum-web-api" "WARN" "데이터베이스 연결 지연 발생 (1.2초)"
send_log "quantum-web-api" "ERROR" "KIS API 호출 실패: 토큰 만료"
send_log "quantum-web-api" "INFO" "사용자 로그인 성공: user@example.com"

# FastAPI KIS Adapter 테스트 로그들  
echo "📦 quantum-adapter-kis 로그 전송..."
send_log "quantum-adapter-kis" "INFO" "FastAPI KIS Adapter 서버가 시작되었습니다"
send_log "quantum-adapter-kis" "INFO" "KIS API 인증 토큰이 갱신되었습니다"
send_log "quantum-adapter-kis" "INFO" "삼성전자(005930) 현재가 조회 성공: 75,000원"
send_log "quantum-adapter-kis" "WARN" "API 응답 속도 지연: 2.1초"
send_log "quantum-adapter-kis" "ERROR" "해외주식 조회 실패: AAPL 심볼 오류"

# Next.js Frontend 테스트 로그들
echo "📦 quantum-web-client 로그 전송..."
send_log "quantum-web-client" "INFO" "Next.js 클라이언트가 시작되었습니다"
send_log "quantum-web-client" "INFO" "차트 컴포넌트가 로드되었습니다"
send_log "quantum-web-client" "WARN" "WebSocket 연결 재시도 중..."
send_log "quantum-web-client" "ERROR" "API 호출 실패: 500 Internal Server Error"

# API 성능 관련 구조화된 로그
echo "📊 API 성능 로그 전송..."
for i in {1..5}; do
    response_time=$((200 + RANDOM % 800))
    status_code=$((200 + (RANDOM % 10 > 7 ? 400 : 0)))
    
    cat << EOF | curl -s -X POST "$LOKI_URL" \
        -H "Content-Type: application/json" \
        --data-binary @-
{
    "streams": [
        {
            "stream": {
                "job": "quantum-web-api",
                "service": "quantum-web-api", 
                "level": "INFO",
                "event_type": "api_request",
                "environment": "development"
            },
            "values": [
                ["$TIMESTAMP", "{\"timestamp\":\"$(date -u --iso-8601=seconds)\",\"level\":\"INFO\",\"message\":\"API 요청 처리 완료\",\"service\":\"quantum-web-api\",\"event_type\":\"api_request\",\"http_method\":\"GET\",\"endpoint\":\"/api/v1/chart/005930\",\"response_time_ms\":$response_time,\"status_code\":$status_code}"]
            ]
        }
    ]
}
EOF
    
    echo "   📈 API 요청 로그 전송: 응답시간 ${response_time}ms, 상태코드 $status_code"
    
    # 시간을 조금씩 증가시켜 시계열 데이터 생성
    TIMESTAMP=$((TIMESTAMP + 1000000000))
done

echo ""
echo "🎉 테스트 로그 전송이 완료되었습니다!"
echo ""
echo "📊 Grafana에서 확인하기:"
echo "   1. http://localhost:3001 접속"
echo "   2. 'Quantum Trading Platform - 통합 로그 모니터링' 대시보드 열기"
echo "   3. 시간 범위를 'Last 5 minutes'로 설정"
echo ""
echo "🔍 Loki 직접 쿼리 테스트:"
echo "   curl -G http://localhost:3100/loki/api/v1/query_range \\"
echo "     --data-urlencode 'query={job=~\"quantum.*\"}' \\"
echo "     --data-urlencode 'start=$(date -d '5 minutes ago' --iso-8601)' \\"
echo "     --data-urlencode 'end=$(date --iso-8601)'"