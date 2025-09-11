# Stock_Data__17_Custom_Backfill DAG 사용 가이드

## 개요

`Stock_Data__17_Custom_Backfill` DAG는 사용자가 지정한 특정 종목들의 2년치 히스토리 데이터를 수집하는 맞춤형 백필 도구입니다.

## 주요 기능

- ✅ **사용자 지정 종목 리스트** - 원하는 종목만 선택적 수집
- ✅ **2년치 히스토리 데이터** - 일봉 OHLCV 데이터 백필
- ✅ **UPSERT 자동 관리** - 중복 데이터 자동 덮어쓰기
- ✅ **배치 처리** - 안정적인 20개씩 배치 처리
- ✅ **실시간 모니터링** - 상세한 진행상황 로깅
- ✅ **수동 실행** - 필요할 때만 실행하는 온디맨드 방식

## 사용 방법

### 1. Airflow UI에서 실행

1. Airflow UI (`http://localhost:8081`) 접속
2. `Stock_Data__17_Custom_Backfill` DAG 찾기
3. **"Trigger DAG w/ Config"** 클릭
4. Configuration에 JSON 설정 입력:

```json
{
  "stock_codes": ["005930", "000660", "035720", "207940"],
  "period_days": 730,
  "batch_size": 20
}
```

### 2. REST API로 실행

```bash
# 실행 예시
TIMESTAMP=$(date +%s)
LOGICAL_DATE=$(date -u +%Y-%m-%dT%H:%M:%S)Z

curl -X POST "http://localhost:8081/api/v1/dags/Stock_Data__17_Custom_Backfill/dagRuns" \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n 'admin:quantum123' | base64)" \
  -d "{
    \"dag_run_id\": \"custom_backfill_${TIMESTAMP}\",
    \"logical_date\": \"${LOGICAL_DATE}\",
    \"conf\": {
      \"stock_codes\": [\"005930\", \"000660\", \"035720\"],
      \"period_days\": 730,
      \"batch_size\": 15
    }
  }"
```

## 설정 파라미터

| 파라미터 | 타입 | 필수여부 | 기본값 | 설명 |
|----------|------|----------|--------|------|
| `stock_codes` | Array | 필수 | `["005930", "000660", "035720"]` | 수집할 종목코드 리스트 |
| `period_days` | Number | 선택 | `730` | 수집 기간 (일수) |
| `batch_size` | Number | 선택 | `20` | 배치 처리 크기 |

### 종목코드 예시

```json
{
  "stock_codes": [
    "005930",  // 삼성전자
    "000660",  // SK하이닉스
    "035420",  // NAVER
    "035720",  // 카카오
    "005380",  // 현대차
    "000270",  // 기아
    "068270",  // 셀트리온
    "207940",  // 삼성바이오로직스
    "006400",  // 삼성SDI
    "051910"   // LG화학
  ]
}
```

## 실행 플로우

```
1. validate_custom_stocks
   ├── 종목코드 유효성 검증
   ├── domestic_stocks 테이블에서 존재 여부 확인
   └── 비활성 종목 필터링

2. fetch_custom_stock_data
   ├── KIS API로 2년치 일봉 데이터 조회
   ├── 배치별 처리 (기본 20개씩)
   └── API 레이트 리미팅 준수 (50ms 간격)

3. save_custom_backfill_to_db
   ├── UPSERT로 domestic_stocks_detail에 저장
   ├── 중복 데이터 자동 덮어쓰기
   └── 데이터 품질 'EXCELLENT'로 설정

4. validate_custom_results
   ├── 수집 결과 통계 생성
   ├── 개별 종목별 데이터 확인
   └── 성공률 계산
```

## 데이터 저장 구조

### UPSERT 키 조합
```sql
ON CONFLICT (stock_code, trade_date, data_type)
```
- 동일한 **종목코드 + 거래일 + 데이터타입**이면 기존 데이터 덮어쓰기
- 신규 데이터면 INSERT

### 저장되는 정보
- **기본 OHLCV**: 시가, 고가, 저가, 종가, 거래량
- **메타데이터**: API 엔드포인트, 요청 파라미터, 응답 코드
- **완전한 원시 응답**: KIS API JSON 응답 전체 (raw_response)
- **데이터 품질**: EXCELLENT로 고정
- **백필 소스 표시**: `custom_backfill_source`로 출처 명시

## 모니터링 및 로그

### 실행 중 로그 확인
```bash
# Airflow 로그 실시간 확인
docker logs -f airflow-scheduler | grep "custom_stock_backfill"

# 특정 DAG 실행 로그 확인
# UI: Airflow > DAGs > Stock_Data__17_Custom_Backfill > Graph View > Task 클릭 > Logs
```

### 주요 로그 예시
```
📊 요청된 설정:
  - 종목 코드: ['005930', '000660', '035720']
  - 수집 기간: 730일
  - 배치 크기: 20

📈 종목 검증 결과:
  - 유효한 종목: 3개
  - 무효한 종목: 0개
  - 비활성 종목: 0개

📦 배치 1/1: 3개 종목 처리 중...
✅ 005930: 500일 데이터 저장 완료
✅ 000660: 485일 데이터 저장 완료
✅ 035720: 492일 데이터 저장 완료

🎉 커스텀 데이터 수집 완료: 3개 종목, 1,477건 저장
```

## 데이터 확인 쿼리

### 수집된 데이터 확인
```sql
-- 오늘 수집된 커스텀 백필 데이터
SELECT 
    stock_code,
    COUNT(*) as record_count,
    MIN(trade_date) as earliest_date,
    MAX(trade_date) as latest_date
FROM domestic_stocks_detail 
WHERE DATE(created_at) = CURRENT_DATE
  AND data_type = 'CHART'
  AND raw_response::text LIKE '%custom_backfill_source%'
GROUP BY stock_code
ORDER BY record_count DESC;
```

### 특정 종목 데이터 상세 확인
```sql
-- 삼성전자(005930) 최근 10일 데이터
SELECT 
    trade_date,
    current_price,
    volume,
    raw_response->>'ohlcv' as ohlcv_data
FROM domestic_stocks_detail 
WHERE stock_code = '005930'
  AND data_type = 'CHART'
ORDER BY trade_date DESC 
LIMIT 10;
```

## 에러 처리

### 일반적인 오류와 해결방법

1. **종목코드 오류**
   ```
   ❌ 무효한 종목 코드: ['Q53005']
   ```
   - 해결: domestic_stocks 테이블에 존재하는 종목코드 사용

2. **KIS API 오류**
   ```
   ❌ 005930: KIS API 오류 - 조회가능한 종목이 없습니다
   ```
   - 해결: 재실행 시 자동 재시도 (최대 3회)

3. **비활성 종목**
   ```
   ⚠️ 비활성 종목: ['123456']
   ```
   - 해결: 활성 종목만 자동 필터링됨

### 재실행 방법
- 동일한 Configuration으로 DAG 재실행하면 UPSERT로 안전하게 중복 처리
- 실패한 종목만 별도로 재수집 가능

## 성능 최적화

### 배치 크기 조정
- **소량 종목 (1-10개)**: `batch_size: 10`
- **중간 종목 (10-50개)**: `batch_size: 20` (기본값)
- **대량 종목 (50개+)**: `batch_size: 30`

### API 호출 최적화
- 50ms 간격으로 API 호출 (초당 20회 제한 준수)
- 배치 간 15초 휴식으로 안정성 보장
- 재시도 로직 (2초, 4초, 6초 간격)

## 주의사항

1. **KIS API 제한**: LIVE 계정 초당 20회, SANDBOX 계정 초당 2회
2. **대용량 수집**: 100개 이상 종목 시 수 시간 소요 가능
3. **데이터 덮어쓰기**: UPSERT 방식으로 기존 데이터가 자동으로 업데이트됨
4. **수동 실행만**: 스케줄 실행 없음, 필요시에만 수동 실행

## 문제 해결

### FAQ

**Q: 중복 데이터가 걱정됩니다.**
A: UPSERT 방식으로 자동 관리됩니다. 동일한 종목+날짜는 최신 데이터로 덮어씁니다.

**Q: 실행 중 중단되면 어떻게 되나요?**
A: 이미 저장된 데이터는 유지되고, 재실행하면 중단된 부분부터 계속 진행됩니다.

**Q: 특정 종목만 재수집하고 싶습니다.**
A: stock_codes에 해당 종목만 넣고 재실행하면 됩니다.

**Q: 2년 이외의 기간도 가능한가요?**
A: period_days 파라미터로 조정 가능하지만, KIS API 제한에 따라 최대 2년입니다.

---

## 예시 실행 케이스

### 케이스 1: 메이저 종목 소량 수집
```json
{
  "stock_codes": ["005930", "000660", "035420"],
  "period_days": 365,
  "batch_size": 5
}
```

### 케이스 2: 섹터별 대표 종목 수집
```json
{
  "stock_codes": ["005930", "035720", "068270", "207940", "005380", "000270"],
  "period_days": 730,
  "batch_size": 15
}
```

### 케이스 3: 대량 종목 효율적 수집
```json
{
  "stock_codes": ["005930", "000660", "035420", "035720", "005380", "000270", "068270", "207940", "006400", "051910", "096770", "028260", "066570", "323410", "000810"],
  "period_days": 730,
  "batch_size": 25
}
```