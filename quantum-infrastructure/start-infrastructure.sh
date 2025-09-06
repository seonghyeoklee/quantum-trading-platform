#!/bin/bash

# ================================================================
# Quantum Trading Platform Infrastructure Startup Script
# ================================================================

set -e

echo "🚀 Quantum Trading Platform Infrastructure 시작 중..."

# quantum-network 네트워크가 없으면 생성
if ! docker network ls --format "{{.Name}}" | grep -q "^quantum-network$"; then
    echo "📡 quantum-network 네트워크 생성 중..."
    docker network create quantum-network
fi

# Infrastructure 서비스 시작
echo "🏗️  Infrastructure 서비스 시작 중..."
docker-compose up -d

# 서비스 상태 확인
echo "⏳ 서비스 시작 대기 중..."
sleep 10

# 상태 출력
echo ""
echo "✅ Quantum Trading Platform Infrastructure 시작 완료!"
echo ""
echo "📊 서비스 상태:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(airflow|quantum|Container)"

echo ""
echo "🌐 서비스 URL:"
echo "  📈 Grafana (모니터링 대시보드): http://localhost:3001 (admin/quantum2024)"
echo "  🔧 Airflow (데이터 파이프라인): http://localhost:8081 (admin/quantum123)"  
echo "  🔍 Prometheus (메트릭):        http://localhost:9090"
echo "  📝 Loki (로그 집계):           http://localhost:3100"
echo ""
echo "💾 데이터베이스:"
echo "  🗄️  PostgreSQL (통합):         localhost:5432 (quantum/quantum123)"
echo ""
echo "🎯 모든 서비스가 같은 quantum-network에서 실행 중입니다."