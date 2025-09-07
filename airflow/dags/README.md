# Airflow DAGs Documentation - 전체 DAG 문서 가이드

## 개요

Quantum Trading Platform의 Apache Airflow에서 사용하는 모든 DAG들에 대한 종합적인 문서입니다. 각 DAG는 상세한 워크플로우 설명과 운영 가이드를 포함한 개별 문서를 가지고 있습니다.

## 📚 DAG 문서 목록

### 1. 🏗️ Stock Master Sync DAG
**파일**: [`stock_master_sync_README.md`](stock_master_sync_README.md)
- **DAG ID**: `stock_master_sync_dag`
- **기능**: 국내(KOSPI/KOSDAQ)와 해외(NASDAQ) 종목 마스터 데이터 동기화
- **스케줄**: 매주 월요일 오전 9시
- **처리량**: 약 8,714개 종목 (국내 3,902개 + 해외 4,812개)
- **주요 특징**:
  - 6단계 워크플로우 (파싱 → 로드 → 검증 → 동기화 → 정리 → 완료)
  - UPSERT 로직으로 안전한 데이터 업데이트
  - 중복 제거 및 데이터 품질 검증
  - 임시 테이블을 통한 원자적 동기화

### 2. 📅 KIS Holiday Sync DAG
**파일**: [`kis_holiday_sync_dag_README.md`](kis_holiday_sync_dag_README.md)  
- **DAG ID**: `kis_holiday_sync`
- **기능**: 한국 주식시장 휴장일 정보 자동 수집 및 동기화
- **스케줄**: 매일 오전 6시 (장 시작 전)
- **API 제한**: 1일 1회 호출 제한 준수
- **주요 특징**:
  - KIS TCA0903R API 사용 (국내휴장일조회)
  - 비즈니스 로직 연동 (거래 가능일 판단 함수)
  - 향후 1년 휴장일 정보 관리
  - 중복 데이터 자동 검증 및 처리

### 3. 🔑 KIS Token Renewal DAG
**파일**: [`kis_token_renewal_README.md`](kis_token_renewal_README.md)
- **DAG ID**: `kis_token_renewal`  
- **기능**: KIS API 인증 토큰 자동 갱신
- **스케줄**: 매 5시간 (`0 */5 * * *`)
- **토큰 수명**: 6시간 (5시간 간격으로 사전 갱신)
- **주요 특징**:
  - 4단계 프로세스 (상태확인 → 갱신 → 검증 → 정리)
  - kis_auth.py 모듈 직접 활용
  - 오래된 토큰 파일 자동 정리 (7일 이상)
  - API 테스트를 통한 토큰 유효성 검증

## 🛠️ 표준 문서화 템플릿
**파일**: [`DAG_DOCUMENTATION_TEMPLATE.md`](DAG_DOCUMENTATION_TEMPLATE.md)
- **목적**: 모든 DAG 문서의 일관성 보장
- **구조**: 표준화된 섹션 및 형식 제공
- **가이드**: 문서 작성 가이드라인 및 품질 체크리스트
- **도구**: 문서 검증 및 자동화 도구 안내

## 🏗️ DAG 아키텍처 개요

### 시스템 구성도
```
┌─────────────────────────────────────────────────────────────┐
│                    Airflow Scheduler                        │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │Stock Master   │  │KIS Data       │  │KIS Holiday    │   │
│  │Sync DAG       │  │Collection DAG │  │Sync DAG       │   │
│  │(Weekly)       │  │(On-demand)    │  │(Daily)        │   │
│  └───────────────┘  └───────────────┘  └───────────────┘   │
│  ┌───────────────┐                                         │
│  │KIS Token      │          ┌─────────────────┐           │
│  │Renewal DAG    │◄─────────┤ Token Manager   │           │
│  │(5 hourly)     │          │ (Shared)        │           │
│  └───────────────┘          └─────────────────┘           │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                 Data Flow & Storage                         │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │KIS API        │  │FastAPI Server │  │PostgreSQL     │   │
│  │(External)     │◄─┤(localhost:8000│  │(Port 5433)    │   │
│  └───────────────┘  └───────────────┘  └───────────────┘   │
│                             │                              │
│  데이터 소스:                │          저장 테이블:         │
│  • 종목 마스터 파일         │          • domestic_stock_    │
│  • KIS API 실시간 데이터    │            master             │
│  • 휴장일 정보             │          • overseas_stock_    │
│                           │            master             │
│                           │          • kis_market_data    │
│                           │          • kis_domestic_      │
│                           │            holidays           │
└─────────────────────────────────────────────────────────────┘
```

### 데이터 의존성 관계
```
KIS Token Renewal ──► All KIS API Operations
                      │
                      ├──► Stock Master Sync (주간)
                      │
                      ├──► KIS Data Collection (수동)
                      │  
                      └──► KIS Holiday Sync (일간)
```

## 📋 운영 가이드

### 일반적인 실행 순서
1. **KIS Token Renewal**: 모든 KIS API 작업의 사전 요구사항
2. **Stock Master Sync**: 주간 단위로 종목 마스터 업데이트  
3. **KIS Holiday Sync**: 일간 단위로 휴장일 정보 업데이트
4. **KIS Data Collection**: 필요 시 수동으로 특정 종목 데이터 수집

### 전체 시스템 상태 확인
```bash
# 모든 DAG 상태 확인
airflow dags list

# 실행 중인 DAG 확인
airflow dags list --only_active

# 최근 실행 상태 확인
airflow dags list --output table
```

### 통합 모니터링 쿼리
```sql
-- 전체 시스템 데이터 현황
SELECT 
    'domestic_stocks' as table_name,
    COUNT(*) as total_count,
    COUNT(CASE WHEN is_active THEN 1 END) as active_count,
    MAX(updated_at) as last_updated
FROM domestic_stock_master

UNION ALL

SELECT 
    'overseas_stocks' as table_name,
    COUNT(*) as total_count,
    COUNT(CASE WHEN is_active THEN 1 END) as active_count,
    MAX(updated_at) as last_updated
FROM overseas_stock_master

UNION ALL

SELECT 
    'market_data' as table_name,
    COUNT(*) as total_count,
    COUNT(CASE WHEN created_at >= CURRENT_DATE THEN 1 END) as today_count,
    MAX(created_at) as last_updated
FROM kis_market_data

UNION ALL

SELECT 
    'holidays' as table_name,
    COUNT(*) as total_count,
    COUNT(CASE WHEN holiday_date >= CURRENT_DATE THEN 1 END) as future_count,
    MAX(updated_at) as last_updated
FROM kis_domestic_holidays;
```

## 🚨 트러블슈팅 가이드

### 공통 오류 상황

#### 1. KIS API 토큰 만료
**증상**: 모든 KIS 관련 DAG 실패
**해결**: `kis_token_renewal` DAG 수동 실행
```bash
airflow dags trigger kis_token_renewal
```

#### 2. PostgreSQL 연결 실패
**증상**: 데이터베이스 관련 태스크 실패
**확인**: 
```bash
docker ps | grep postgres
docker logs quantum-postgres
```

#### 3. FastAPI 서버 연결 실패
**증상**: KIS API 호출 관련 태스크 실패
**확인**:
```bash
curl http://localhost:8000/health
cd /Users/admin/study/quantum-trading-platform/quantum-adapter-kis
uv run python main.py
```

#### 4. 파일 권한 오류
**증상**: 종목 마스터 파일 읽기 실패
**해결**:
```bash
chmod 644 /opt/airflow/quantum-adapter-kis/docs/*.txt
chmod 644 /opt/airflow/quantum-adapter-kis/docs/*.COD
```

### 로그 위치 및 확인 방법
```bash
# Airflow 로그 디렉토리
ls -la /opt/airflow/logs/

# 특정 DAG 로그 확인
docker exec airflow-scheduler find /opt/airflow/logs -name "*.log" | grep [dag_id]

# 실시간 로그 모니터링
docker logs -f airflow-scheduler
```

## 📈 성능 최적화 가이드

### DAG 최적화 체크리스트
- [ ] **병렬 처리**: 독립적인 태스크들의 병렬 실행 설정
- [ ] **리소스 제한**: max_active_runs, max_active_tasks 적절히 설정
- [ ] **재시도 전략**: retries, retry_delay 적절히 구성
- [ ] **의존성 최적화**: 불필요한 의존성 제거
- [ ] **배치 처리**: 대량 데이터 배치 단위로 처리

### 성능 메트릭 모니터링
```sql
-- DAG 실행 통계 (Airflow 메타데이터)
SELECT 
    dag_id,
    COUNT(*) as total_runs,
    AVG(EXTRACT(EPOCH FROM (end_date - start_date))) as avg_duration_seconds,
    COUNT(CASE WHEN state = 'success' THEN 1 END) as success_count,
    COUNT(CASE WHEN state = 'failed' THEN 1 END) as failed_count
FROM dag_run 
WHERE start_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY dag_id
ORDER BY avg_duration_seconds DESC;
```

## 🔧 개발 및 테스트 가이드

### 새 DAG 개발 프로세스
1. **기획**: 요구사항 정의 및 워크플로우 설계
2. **개발**: DAG 파일 작성 및 테스트
3. **문서화**: 표준 템플릿 활용하여 문서 작성
4. **검증**: 품질 체크리스트 확인
5. **배포**: 운영 환경 배포 및 모니터링

### 로컬 테스트 방법
```bash
# DAG 파일 문법 검증
python /path/to/dag/file.py

# 특정 태스크 테스트 실행
airflow tasks test [dag_id] [task_id] [execution_date]

# DAG 전체 테스트 (dry-run)
airflow dags test [dag_id] [execution_date]
```

### CI/CD 연동 가이드
```yaml
# .github/workflows/airflow-dags.yml 예시
name: Airflow DAGs CI/CD
on:
  push:
    paths:
      - 'airflow/dags/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: DAG Syntax Check
        run: python -m py_compile airflow/dags/*.py
      
      - name: Documentation Check
        run: |
          for dag in airflow/dags/*.py; do
            readme="${dag%.*}_README.md"
            if [ ! -f "$readme" ]; then
              echo "Missing documentation: $readme"
              exit 1
            fi
          done
```

## 🔍 확장 및 유지보수

### 향후 추가 예정 DAG들
- **ML Signal Training DAG**: 머신러닝 신호 생성 모델 훈련
- **Portfolio Rebalancing DAG**: 포트폴리오 자동 리밸런싱
- **Risk Management DAG**: 리스크 모니터링 및 알림
- **Performance Monitoring DAG**: 성능 지표 수집 및 분석

### 문서 유지보수 일정
- **월간**: 성능 메트릭 업데이트
- **분기**: 확장 계획 검토 및 업데이트  
- **반기**: 전체 아키텍처 리뷰
- **연간**: 기술 스택 업그레이드 계획

## 📞 지원 및 연락처

### 기술 지원
- **이슈 보고**: GitHub Issues
- **개발 문의**: 개발팀 Slack 채널
- **긴급 상황**: 온콜 담당자 연락

### 관련 문서
- [Quantum Trading Platform CLAUDE.md](../../CLAUDE.md)
- [KIS Adapter Documentation](../../quantum-adapter-kis/CLAUDE.md)
- [Backend API Documentation](../../quantum-web-api/README.md)
- [Frontend Documentation](../../quantum-web-client/README.md)

---

**문서 최종 업데이트**: 2025-09-06  
**담당팀**: Quantum Trading Platform Team  
**문서 버전**: 1.0  
**다음 리뷰 예정**: 2025-12-06