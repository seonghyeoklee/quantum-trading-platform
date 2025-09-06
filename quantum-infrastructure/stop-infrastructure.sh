#!/bin/bash

# ================================================================
# Quantum Trading Platform Infrastructure Stop Script
# ================================================================

set -e

echo "🛑 Quantum Trading Platform Infrastructure 중지 중..."

# Infrastructure 서비스 중지
docker-compose down

echo ""
echo "✅ Infrastructure 중지 완료!"
echo ""
echo "💡 팁:"
echo "  • 데이터 볼륨은 보존됩니다 (postgres, grafana, loki, prometheus)"
echo "  • 완전히 삭제하려면: docker-compose down -v"
echo "  • 네트워크 삭제하려면: docker network rm quantum-network"