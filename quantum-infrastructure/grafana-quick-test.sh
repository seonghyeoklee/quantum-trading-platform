#!/bin/bash

echo "🔍 Grafana & Loki 연동 상태 빠른 확인"
echo "================================================"

# 1. 서비스 상태 확인
echo "📊 서비스 상태:"
echo -n "   Grafana (3001): "
if curl -s http://localhost:3001/api/health > /dev/null; then
    echo "✅ 정상"
else
    echo "❌ 연결 실패"
fi

echo -n "   Loki (3100): "
if curl -s http://localhost:3100/ready | grep -q "ready"; then
    echo "✅ 준비됨"
else
    echo "⚠️  대기 중"
fi

# 2. Loki 데이터 확인
echo ""
echo "📦 Loki 데이터 현황:"
LABELS=$(curl -s http://localhost:3100/loki/api/v1/labels | jq -r '.data | length')
echo "   사용 가능한 라벨 수: $LABELS"

JOBS=$(curl -s 'http://localhost:3100/loki/api/v1/label/job/values' | jq -r '.data | length')
echo "   등록된 서비스 수: $JOBS"

# 3. Grafana 대시보드 접근 가이드
echo ""
echo "🎯 Grafana 대시보드 접근 방법:"
echo "================================================"
echo "1. 브라우저에서 http://localhost:3001 접속"
echo "2. 로그인: admin / quantum2024"
echo "3. 좌측 메뉴 > Dashboards 클릭"
echo "4. 'Quantum Trading Platform - 통합 로그 모니터링' 선택"
echo "5. 우측 상단 시간 범위를 'Last 15 minutes'로 변경"
echo ""
echo "🔧 데이터가 보이지 않을 경우:"
echo "------------------------------------------------"
echo "• Explore 메뉴에서 Loki 선택"
echo "• 쿼리 입력: {job=\"quantum-web-api\"}"
echo "• 시간 범위: Last 15 minutes"
echo "• Run query 버튼 클릭"
echo ""
echo "📝 수동으로 로그 생성 (실제 서비스):"
echo "------------------------------------------------"
echo "cd quantum-web-api && ./gradlew bootRun --args='--spring.profiles.active=docker'"
echo "cd quantum-adapter-kis && uv run python main.py"
echo ""
echo "🆘 문제 해결:"
echo "------------------------------------------------"
echo "docker-compose -f docker-compose.monitoring.yml logs grafana"
echo "docker-compose -f docker-compose.monitoring.yml logs loki"