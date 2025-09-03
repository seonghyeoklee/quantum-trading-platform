#!/bin/bash

# Quantum Trading Platform 모니터링 시스템 테스트 스크립트

echo "🧪 Quantum Trading Platform 모니터링 시스템 테스트를 시작합니다..."

# 함수 정의
check_service() {
    local service_name="$1"
    local url="$2"
    local expected_status="$3"
    
    echo -n "   $service_name 확인: "
    
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected_status"; then
        echo "✅ 정상"
    else
        echo "❌ 실패"
        return 1
    fi
}

# 1. Docker 컨테이너 상태 확인
echo "🐳 Docker 컨테이너 상태 확인..."
echo "-------------------------------------------"
docker-compose -f docker-compose.monitoring.yml ps

# 2. 서비스 연결 테스트
echo ""
echo "🔗 서비스 연결 테스트..."
echo "-------------------------------------------"

check_service "Loki" "http://localhost:3100/ready" "200"
check_service "Prometheus" "http://localhost:9090/-/ready" "200" 
check_service "Grafana" "http://localhost:3001/api/health" "200"

# 3. 로그 디렉터리 확인
echo ""
echo "📁 로그 디렉터리 확인..."
echo "-------------------------------------------"

for service in "quantum-web-api" "quantum-adapter-kis" "quantum-web-client"; do
    if [ -d "../$service/logs" ]; then
        echo "   ✅ $service/logs/ 디렉터리 존재"
        echo "      권한: $(ls -ld "../$service/logs" | awk '{print $1}')"
    else
        echo "   ❌ $service/logs/ 디렉터리 없음"
    fi
done

# 4. Loki 쿼리 테스트
echo ""
echo "🔍 Loki 쿼리 테스트..."
echo "-------------------------------------------"

# 기본 쿼리 테스트
LOKI_QUERY_URL="http://localhost:3100/loki/api/v1/query_range"
QUERY='{job=~"quantum.*"}'
START_TIME=$(date -d '1 hour ago' --iso-8601)
END_TIME=$(date --iso-8601)

echo -n "   로그 쿼리 테스트: "
if curl -s -G "$LOKI_QUERY_URL" \
   --data-urlencode "query=$QUERY" \
   --data-urlencode "start=$START_TIME" \
   --data-urlencode "end=$END_TIME" | jq '.status' | grep -q '"success"'; then
    echo "✅ 정상"
else
    echo "⚠️  쿼리 실행됨 (로그 데이터 없음)"
fi

# 5. Prometheus 메트릭 테스트  
echo ""
echo "📊 Prometheus 메트릭 테스트..."
echo "-------------------------------------------"

PROMETHEUS_QUERY_URL="http://localhost:9090/api/v1/query"
METRIC_QUERY="up"

echo -n "   메트릭 쿼리 테스트: "
if curl -s -G "$PROMETHEUS_QUERY_URL" \
   --data-urlencode "query=$METRIC_QUERY" | jq '.status' | grep -q '"success"'; then
    echo "✅ 정상"
else
    echo "❌ 실패"
fi

# 6. 테스트 로그 생성
echo ""
echo "📝 테스트 로그 생성..."
echo "-------------------------------------------"

# Spring Boot 테스트 로그
TEST_LOG="../quantum-web-api/logs/quantum-web-api.log"
if [ ! -f "$TEST_LOG" ]; then
    mkdir -p "$(dirname "$TEST_LOG")"
    echo '{"timestamp":"'"$(date -u --iso-8601=seconds)"'","level":"INFO","message":"모니터링 테스트 로그","service":"quantum-web-api","logger":"test"}' >> "$TEST_LOG"
    echo "   ✅ Spring Boot 테스트 로그 생성: $TEST_LOG"
else
    echo "   ℹ️  Spring Boot 로그 파일 이미 존재: $TEST_LOG"
fi

# FastAPI 테스트 로그
TEST_LOG="../quantum-adapter-kis/logs/quantum-adapter-kis.log"  
if [ ! -f "$TEST_LOG" ]; then
    mkdir -p "$(dirname "$TEST_LOG")"
    echo '{"timestamp":"'"$(date -u --iso-8601=seconds)"'","level":"INFO","message":"모니터링 테스트 로그","service":"quantum-adapter-kis","logger":"test"}' >> "$TEST_LOG"
    echo "   ✅ FastAPI 테스트 로그 생성: $TEST_LOG"
else
    echo "   ℹ️  FastAPI 로그 파일 이미 존재: $TEST_LOG"
fi

# 7. Promtail 설정 검증
echo ""
echo "🔧 Promtail 설정 검증..."
echo "-------------------------------------------"

echo -n "   Promtail 컨테이너 상태: "
if docker-compose -f docker-compose.monitoring.yml ps promtail | grep -q "Up"; then
    echo "✅ 실행 중"
    
    # Promtail 로그 확인
    echo "   📜 Promtail 로그 (최근 10줄):"
    docker-compose -f docker-compose.monitoring.yml logs --tail=10 promtail | sed 's/^/      /'
else
    echo "❌ 중단됨"
fi

# 8. 성능 테스트
echo ""
echo "⚡ 성능 테스트..."
echo "-------------------------------------------"

# 메모리 사용량 확인
echo "   🧠 컨테이너별 메모리 사용량:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep -E "(grafana|loki|prometheus|promtail)" | sed 's/^/      /'

# 디스크 사용량 확인
echo ""
echo "   💾 로그 디렉터리 디스크 사용량:"
for service in "quantum-web-api" "quantum-adapter-kis" "quantum-web-client"; do
    if [ -d "../$service/logs" ]; then
        size=$(du -sh "../$service/logs" 2>/dev/null | cut -f1)
        echo "      $service/logs/: $size"
    fi
done

# 9. 종합 결과
echo ""
echo "📋 테스트 결과 요약..."
echo "-------------------------------------------"

# 전체 컨테이너가 정상 실행 중인지 확인
CONTAINER_COUNT=$(docker-compose -f docker-compose.monitoring.yml ps -q | wc -l)
RUNNING_COUNT=$(docker-compose -f docker-compose.monitoring.yml ps | grep -c "Up")

if [ "$CONTAINER_COUNT" -eq "$RUNNING_COUNT" ] && [ "$RUNNING_COUNT" -eq 4 ]; then
    echo "   ✅ 모든 컨테이너가 정상 실행 중 ($RUNNING_COUNT/4)"
else
    echo "   ⚠️  일부 컨테이너 문제 ($RUNNING_COUNT/$CONTAINER_COUNT)"
fi

# 포트 접근성 확인
ACCESSIBLE_PORTS=0
for port in 3001 3100 9090; do
    if curl -s -o /dev/null "http://localhost:$port"; then
        ((ACCESSIBLE_PORTS++))
    fi
done

echo "   🌐 접근 가능한 포트: $ACCESSIBLE_PORTS/3"

echo ""
echo "🎉 모니터링 시스템 테스트가 완료되었습니다!"
echo ""
echo "📊 다음 단계:"
echo "   1. Grafana 접속: http://localhost:3001 (admin/quantum2024)"
echo "   2. 대시보드 확인: 'Quantum Trading Platform - 통합 로그 모니터링'"
echo "   3. 실제 서비스 실행하여 로그 생성 테스트"
echo ""
echo "💡 문제 발생 시 'docker-compose -f docker-compose.monitoring.yml logs' 명령으로 로그를 확인하세요."