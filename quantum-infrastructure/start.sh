#!/bin/bash

# Quantum Trading Platform - Docker Compose 시작 스크립트

echo "================================================"
echo "   Quantum Trading Platform - Infrastructure   "
echo "================================================"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 현재 디렉토리 확인
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 환경변수 파일 체크
if [ ! -f ".env.docker" ]; then
    echo -e "${RED}Error: .env.docker 파일이 없습니다.${NC}"
    exit 1
fi

# 명령어 파싱
COMMAND=${1:-up}
SERVICES=${2:-all}

# 함수 정의
check_network_conflicts() {
    echo -e "${YELLOW}네트워크 충돌 확인...${NC}"
    
    # 172.25.0.0/16 대역 사용 중인 네트워크 확인
    CONFLICTING_NETWORKS=$(docker network ls --format "table {{.Name}}" | xargs -I {} docker network inspect {} 2>/dev/null | grep -B5 -A5 "172.25.0.0/16" | grep "Name" | cut -d'"' -f4 | grep -v "^$" || true)
    
    if [ ! -z "$CONFLICTING_NETWORKS" ]; then
        echo -e "${RED}네트워크 충돌 감지: $CONFLICTING_NETWORKS${NC}"
        echo -e "${YELLOW}충돌하는 네트워크를 정리 중...${NC}"
        
        for network in $CONFLICTING_NETWORKS; do
            if [ "$network" != "quantum-infrastructure_quantum-network" ]; then
                docker network rm "$network" 2>/dev/null || echo "네트워크 $network 삭제 실패"
            fi
        done
    fi
}

start_infrastructure() {
    check_network_conflicts
    echo -e "${GREEN}인프라 서비스 시작...${NC}"
    docker-compose --env-file .env.docker up -d \
        axon-server \
        postgres \
        redis \
        zookeeper \
        kafka \
        prometheus \
        grafana
    
    echo -e "${YELLOW}서비스 초기화 대기 (30초)...${NC}"
    sleep 30
}

start_brokers() {
    echo -e "${GREEN}브로커 서비스 시작...${NC}"
    docker-compose --env-file .env.docker up -d \
        kiwoom-api \
        kis-mock-api
}

start_applications() {
    echo -e "${GREEN}애플리케이션 서비스 시작...${NC}"
    docker-compose --env-file .env.docker up -d \
        quantum-api-gateway \
        quantum-batch
}

start_monitoring() {
    echo -e "${GREEN}모니터링 도구 시작...${NC}"
    docker-compose --env-file .env.docker up -d \
        kafka-ui \
        redis-commander
}

stop_all() {
    echo -e "${YELLOW}모든 서비스 종료...${NC}"
    docker-compose --env-file .env.docker down
}

clean_all() {
    echo -e "${RED}모든 서비스 및 볼륨 삭제...${NC}"
    docker-compose --env-file .env.docker down -v --remove-orphans
    
    # 네트워크 정리
    echo -e "${YELLOW}네트워크 정리...${NC}"
    docker network prune -f
}

show_status() {
    echo -e "${GREEN}서비스 상태:${NC}"
    docker-compose --env-file .env.docker ps
}

show_logs() {
    SERVICE=$1
    if [ -z "$SERVICE" ]; then
        docker-compose --env-file .env.docker logs -f --tail=100
    else
        docker-compose --env-file .env.docker logs -f --tail=100 $SERVICE
    fi
}

# 메인 로직
case "$COMMAND" in
    up|start)
        if [ "$SERVICES" == "all" ]; then
            start_infrastructure
            start_brokers
            start_applications
            start_monitoring
        elif [ "$SERVICES" == "infra" ]; then
            start_infrastructure
        elif [ "$SERVICES" == "brokers" ]; then
            start_brokers
        elif [ "$SERVICES" == "apps" ]; then
            start_applications
        elif [ "$SERVICES" == "monitoring" ]; then
            start_monitoring
        else
            echo -e "${YELLOW}특정 서비스 시작: $SERVICES${NC}"
            docker-compose --env-file .env.docker up -d $SERVICES
        fi
        
        echo ""
        echo -e "${GREEN}서비스 접속 정보:${NC}"
        echo "================================================"
        echo "Axon Server Dashboard:  http://localhost:8024"
        echo "PostgreSQL:            localhost:5433"
        echo "Redis:                 localhost:6379"
        echo "Kafka:                 localhost:9092"
        echo "Prometheus:            http://localhost:9090"
        echo "Grafana:               http://localhost:3000"
        echo "Kiwoom API:            http://localhost:8100"
        echo "KIS Mock API:          http://localhost:8200"
        echo "API Gateway:           http://localhost:8080"
        echo "Kafka UI:              http://localhost:8090"
        echo "Redis Commander:       http://localhost:8091"
        echo "================================================"
        ;;
        
    stop|down)
        stop_all
        ;;
        
    clean)
        read -p "정말로 모든 데이터를 삭제하시겠습니까? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            clean_all
        fi
        ;;
        
    restart)
        stop_all
        sleep 5
        $0 up $SERVICES
        ;;
        
    status|ps)
        show_status
        ;;
        
    logs)
        show_logs $SERVICES
        ;;
        
    build)
        echo -e "${GREEN}Docker 이미지 빌드...${NC}"
        docker-compose --env-file .env.docker build
        ;;
        
    *)
        echo "사용법: $0 {up|stop|clean|restart|status|logs|build} [서비스명|all|infra|brokers|apps|monitoring]"
        echo ""
        echo "명령어:"
        echo "  up/start   - 서비스 시작"
        echo "  stop/down  - 서비스 종료"
        echo "  clean      - 서비스 및 데이터 삭제"
        echo "  restart    - 서비스 재시작"
        echo "  status/ps  - 서비스 상태 확인"
        echo "  logs       - 로그 확인"
        echo "  build      - Docker 이미지 빌드"
        echo ""
        echo "서비스 그룹:"
        echo "  all        - 모든 서비스"
        echo "  infra      - 인프라 서비스 (DB, Kafka, Redis 등)"
        echo "  brokers    - 브로커 서비스 (Kiwoom, KIS)"
        echo "  apps       - 애플리케이션 서비스"
        echo "  monitoring - 모니터링 도구"
        exit 1
        ;;
esac