#!/bin/bash

# Quantum Trading Platform 모니터링 시스템 시작 스크립트

echo "🚀 Quantum Trading Platform 모니터링 시스템을 시작합니다..."

# 현재 디렉터리 확인
if [ ! -f "docker-compose.monitoring.yml" ]; then
    echo "❌ docker-compose.monitoring.yml 파일을 찾을 수 없습니다."
    echo "quantum-infrastructure 디렉터리에서 실행해주세요."
    exit 1
fi

# 로그 디렉터리 생성 및 권한 설정
echo "📁 로그 디렉터리 생성 중..."
mkdir -p ../quantum-web-api/logs
mkdir -p ../quantum-adapter-kis/logs
mkdir -p ../quantum-web-client/logs

# 권한 설정
chmod 755 ../quantum-web-api/logs
chmod 755 ../quantum-adapter-kis/logs  
chmod 755 ../quantum-web-client/logs

# Docker Compose로 모니터링 스택 실행
echo "🐳 Docker 컨테이너를 시작합니다..."
docker-compose -f docker-compose.monitoring.yml up -d

# 컨테이너 상태 확인
echo "⏳ 컨테이너 시작을 기다리는 중..."
sleep 10

echo "📊 컨테이너 상태 확인:"
docker-compose -f docker-compose.monitoring.yml ps

# 서비스 가용성 체크
echo "🔍 서비스 가용성 확인 중..."

# Loki 확인
if curl -s http://localhost:3100/ready > /dev/null; then
    echo "✅ Loki가 준비되었습니다 (http://localhost:3100)"
else
    echo "⚠️  Loki 연결 실패"
fi

# Prometheus 확인
if curl -s http://localhost:9090/-/ready > /dev/null; then
    echo "✅ Prometheus가 준비되었습니다 (http://localhost:9090)"
else
    echo "⚠️  Prometheus 연결 실패"
fi

# Grafana 확인
if curl -s http://localhost:3001/api/health > /dev/null; then
    echo "✅ Grafana가 준비되었습니다 (http://localhost:3001)"
    echo "   👤 로그인: admin/quantum2024"
else
    echo "⚠️  Grafana 연결 실패"
fi

echo ""
echo "🎉 모니터링 시스템이 시작되었습니다!"
echo ""
echo "📊 대시보드 접근:"
echo "   • Grafana:    http://localhost:3001 (admin/quantum2024)"
echo "   • Prometheus: http://localhost:9090"
echo "   • Loki:       http://localhost:3100"
echo ""
echo "🚀 다음 단계:"
echo "   1. Spring Boot API 실행:  ./gradlew bootRun --args='--spring.profiles.active=docker'"
echo "   2. FastAPI KIS 실행:      uv run python main.py"
echo "   3. Next.js Frontend 실행: npm run dev"
echo ""
echo "📝 로그 파일 위치:"
echo "   • Spring Boot: quantum-web-api/logs/"
echo "   • FastAPI:     quantum-adapter-kis/logs/"
echo "   • Next.js:     quantum-web-client/logs/"
echo ""
echo "💡 사용법은 README.md 파일을 참고하세요."