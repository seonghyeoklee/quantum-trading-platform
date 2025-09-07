# KIS Holiday Sync DAG - KIS 국내휴장일 동기화 워크플로우

## 개요

**KIS Holiday Sync DAG**는 KIS API의 국내휴장일조회(TCA0903R) 서비스를 통해 한국 주식시장의 휴장일 정보를 자동으로 수집하여 PostgreSQL 데이터베이스에 저장하는 Airflow DAG입니다.

- **DAG ID**: `kis_holiday_sync`
- **실행 주기**: 매일 오전 6시 (장 시작 전)
- **API 제한**: 1일 1회 호출 제한 준수
- **재시도**: 3회, 30분 간격

## 전체 워크플로우 구조

```
fetch_holiday_data → store_holiday_data → validate_holiday_data
```

## 상세 단계별 프로세스

### STEP 1: 휴장일 데이터 조회 (fetch_holiday_data)
**태스크 ID**: `fetch_holiday_data`
**기능**: KIS API에서 휴장일 데이터를 조회하고 검증

#### 1.1 KIS API 인증 및 호출
```python
@task(retries=3, retry_delay=timedelta(minutes=30))
def fetch_holiday_data() -> Dict[str, Any]:
    """
    KIS API에서 휴장일 데이터 조회
    1일 1회 제한 준수
    """
    logging.info("KIS 휴장일 데이터 조회 시작")
    
    # FastAPI 서버를 통한 KIS API 호출
    base_url = "http://localhost:8000"
    endpoint = "/domestic/holiday"
    
    try:
        response = requests.get(f"{base_url}{endpoint}", timeout=30)
        response.raise_for_status()
        
        holiday_data = response.json()
        logging.info(f"✅ 휴장일 데이터 수신 성공: {len(holiday_data.get('output', []))}건")
        
        return {
            'status': 'success',
            'data': holiday_data,
            'count': len(holiday_data.get('output', [])),
            'api_response_time': response.elapsed.total_seconds()
        }
        
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ KIS API 호출 실패: {e}")
        raise
    except Exception as e:
        logging.error(f"❌ 휴장일 데이터 처리 실패: {e}")
        raise
```

#### 1.2 API 응답 데이터 구조 검증
```python
def validate_api_response(holiday_data: Dict[str, Any]) -> bool:
    """API 응답 데이터의 구조와 내용 검증"""
    
    if not holiday_data:
        raise ValueError("휴장일 데이터가 비어있습니다")
    
    # 기본 응답 구조 검증
    required_fields = ['rt_cd', 'msg_cd', 'msg1', 'output']
    for field in required_fields:
        if field not in holiday_data:
            raise ValueError(f"필수 필드 누락: {field}")
    
    # 성공 응답 코드 확인
    if holiday_data.get('rt_cd') != '0':
        error_msg = holiday_data.get('msg1', '알 수 없는 오류')
        raise ValueError(f"API 오류 응답: {error_msg}")
    
    # 휴장일 데이터 배열 검증
    holidays = holiday_data.get('output', [])
    if not isinstance(holidays, list):
        raise ValueError("휴장일 데이터가 배열 형식이 아닙니다")
    
    logging.info(f"📅 휴장일 데이터 검증 완료: {len(holidays)}건")
    return True
```

#### 1.3 휴장일 데이터 파싱 및 정규화
```python
def parse_holiday_data(raw_holidays: List[Dict]) -> List[Dict[str, Any]]:
    """휴장일 데이터를 DB 저장 형식으로 변환"""
    
    parsed_holidays = []
    
    for holiday in raw_holidays:
        try:
            # 필수 필드 추출
            holiday_date = holiday.get('bzdy_dd')  # 영업일자 (YYYYMMDD)
            holiday_name = holiday.get('bzdy_nm', '').strip()  # 휴장일명
            
            if not holiday_date or len(holiday_date) != 8:
                logging.warning(f"⚠️ 잘못된 날짜 형식 스킵: {holiday_date}")
                continue
            
            # 날짜 형식 변환 및 검증
            try:
                parsed_date = datetime.strptime(holiday_date, '%Y%m%d').date()
            except ValueError:
                logging.warning(f"⚠️ 날짜 파싱 실패 스킵: {holiday_date}")
                continue
            
            # 정규화된 휴장일 데이터
            parsed_holidays.append({
                'holiday_date': parsed_date,
                'holiday_name': holiday_name or '휴장일',
                'market_type': 'DOMESTIC',  # 국내시장
                'is_active': True,
                'raw_data': holiday,  # 원본 데이터 보존
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })
            
        except Exception as e:
            logging.error(f"❌ 휴장일 데이터 파싱 오류: {holiday} - {e}")
            continue
    
    logging.info(f"🔧 휴장일 데이터 파싱 완료: {len(parsed_holidays)}건")
    return parsed_holidays
```

### STEP 2: 휴장일 데이터 저장 (store_holiday_data)
**태스크 ID**: `store_holiday_data`
**기능**: 파싱된 휴장일 데이터를 PostgreSQL에 UPSERT

#### 2.1 데이터베이스 연결 및 테이블 준비
```python
@task(retries=2, retry_delay=timedelta(minutes=5))
def store_holiday_data(holiday_fetch_result: Dict[str, Any]) -> Dict[str, Any]:
    """휴장일 데이터를 PostgreSQL에 저장"""
    
    if holiday_fetch_result['status'] != 'success':
        raise ValueError("휴장일 데이터 조회 실패로 저장 불가")
    
    # PostgreSQL 연결
    connection = psycopg2.connect(
        host="localhost",
        port=5433,
        database="quantum_trading",
        user="quantum",
        password="quantum123"
    )
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # 휴장일 데이터 파싱
        raw_holidays = holiday_fetch_result['data'].get('output', [])
        parsed_holidays = parse_holiday_data(raw_holidays)
        
        if not parsed_holidays:
            logging.warning("⚠️ 저장할 휴장일 데이터가 없습니다")
            return {'stored_count': 0, 'updated_count': 0}
```

#### 2.2 UPSERT 쿼리 실행
```python
        # UPSERT 쿼리 (중복 시 업데이트)
        upsert_query = """
        INSERT INTO kis_domestic_holidays 
        (holiday_date, holiday_name, market_type, is_active, raw_data, created_at, updated_at)
        VALUES (%(holiday_date)s, %(holiday_name)s, %(market_type)s, 
                %(is_active)s, %(raw_data)s, %(created_at)s, %(updated_at)s)
        ON CONFLICT (holiday_date) DO UPDATE SET
            holiday_name = EXCLUDED.holiday_name,
            is_active = EXCLUDED.is_active,
            raw_data = EXCLUDED.raw_data,
            updated_at = EXCLUDED.updated_at
        """
        
        stored_count = 0
        updated_count = 0
        
        for holiday in parsed_holidays:
            try:
                # 기존 데이터 확인
                cursor.execute(
                    "SELECT id FROM kis_domestic_holidays WHERE holiday_date = %s",
                    (holiday['holiday_date'],)
                )
                existing = cursor.fetchone()
                
                # UPSERT 실행
                cursor.execute(upsert_query, {
                    'holiday_date': holiday['holiday_date'],
                    'holiday_name': holiday['holiday_name'],
                    'market_type': holiday['market_type'],
                    'is_active': holiday['is_active'],
                    'raw_data': json.dumps(holiday['raw_data']),
                    'created_at': holiday['created_at'],
                    'updated_at': holiday['updated_at']
                })
                
                if existing:
                    updated_count += 1
                else:
                    stored_count += 1
                    
            except Exception as e:
                logging.error(f"❌ 휴장일 저장 실패: {holiday['holiday_date']} - {e}")
                continue
        
        # 트랜잭션 커밋
        connection.commit()
        
        logging.info(f"💾 휴장일 데이터 저장 완료:")
        logging.info(f"   - 신규 저장: {stored_count}건")
        logging.info(f"   - 업데이트: {updated_count}건")
        
        return {
            'stored_count': stored_count,
            'updated_count': updated_count,
            'total_processed': len(parsed_holidays)
        }
        
    finally:
        cursor.close()
        connection.close()
```

### STEP 3: 휴장일 데이터 검증 (validate_holiday_data)
**태스크 ID**: `validate_holiday_data`
**기능**: 저장된 휴장일 데이터의 무결성 및 완전성 검증

#### 3.1 데이터 무결성 검증
```python
@task
def validate_holiday_data(store_result: Dict[str, Any]) -> Dict[str, str]:
    """저장된 휴장일 데이터 검증"""
    
    connection = psycopg2.connect(
        host="localhost",
        port=5433,
        database="quantum_trading",
        user="quantum",
        password="quantum123"
    )
    
    try:
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # 1. 기본 통계 조회
        cursor.execute("""
            SELECT 
                COUNT(*) as total_count,
                COUNT(CASE WHEN is_active = TRUE THEN 1 END) as active_count,
                MIN(holiday_date) as earliest_date,
                MAX(holiday_date) as latest_date
            FROM kis_domestic_holidays
        """)
        
        stats = cursor.fetchone()
        
        logging.info(f"📊 휴장일 데이터 통계:")
        logging.info(f"   - 전체 건수: {stats['total_count']}")
        logging.info(f"   - 활성 건수: {stats['active_count']}")
        logging.info(f"   - 날짜 범위: {stats['earliest_date']} ~ {stats['latest_date']}")
```

#### 3.2 데이터 품질 검증
```python
        # 2. 중복 데이터 검증
        cursor.execute("""
            SELECT holiday_date, COUNT(*) as cnt 
            FROM kis_domestic_holidays 
            GROUP BY holiday_date 
            HAVING COUNT(*) > 1
        """)
        
        duplicates = cursor.fetchall()
        if duplicates:
            logging.warning(f"⚠️ 중복된 휴장일 발견: {len(duplicates)}건")
            for dup in duplicates:
                logging.warning(f"   - {dup['holiday_date']}: {dup['cnt']}건")
        
        # 3. 최근 업데이트 데이터 확인
        cursor.execute("""
            SELECT COUNT(*) as recent_count
            FROM kis_domestic_holidays 
            WHERE updated_at >= NOW() - INTERVAL '1 DAY'
        """)
        
        recent_updates = cursor.fetchone()['recent_count']
        
        # 4. 향후 1년 휴장일 확인
        cursor.execute("""
            SELECT COUNT(*) as future_holidays
            FROM kis_domestic_holidays 
            WHERE holiday_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '1 YEAR'
            AND is_active = TRUE
        """)
        
        future_count = cursor.fetchone()['future_holidays']
        
        logging.info(f"✅ 휴장일 데이터 검증 완료:")
        logging.info(f"   - 최근 업데이트: {recent_updates}건")
        logging.info(f"   - 향후 1년 휴장일: {future_count}건")
        logging.info(f"   - 중복 데이터: {len(duplicates)}건")
        
        # 검증 결과 반환
        validation_status = "SUCCESS" if len(duplicates) == 0 else "WARNING"
        
        return {
            'status': validation_status,
            'total_count': stats['total_count'],
            'active_count': stats['active_count'],
            'recent_updates': recent_updates,
            'future_holidays': future_count,
            'duplicates': len(duplicates),
            'earliest_date': str(stats['earliest_date']),
            'latest_date': str(stats['latest_date'])
        }
        
    finally:
        cursor.close()
        connection.close()
```

## 데이터 플로우 다이어그램

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   KIS API       │    │  Data Pipeline  │    │  PostgreSQL DB  │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│TCA0903R         │───►│1. API 호출       │───►│kis_domestic_    │
│(국내휴장일조회)  │    │2. 데이터 검증    │    │holidays 테이블   │
│1일 1회 제한     │    │3. 파싱/정규화    │    │                 │
└─────────────────┘    │4. UPSERT 저장   │    └─────────────────┘
                       │5. 무결성 검증    │            ▲
                       └─────────────────┘            │
                              ▲                        │
                              │                ┌─────────────┐
                       ┌─────────────┐         │ 6. 품질검증  │
                       │ 스케줄러     │         │ 7. 통계수집  │
                       │ 매일 06:00  │         │ 8. 알람체크  │
                       └─────────────┘         └─────────────┘
```

## 데이터베이스 스키마

### kis_domestic_holidays 테이블 구조
```sql
CREATE TABLE kis_domestic_holidays (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    holiday_date DATE NOT NULL UNIQUE,         -- 휴장일 (YYYY-MM-DD)
    holiday_name VARCHAR(100) NOT NULL,        -- 휴장일명
    market_type VARCHAR(10) DEFAULT 'DOMESTIC', -- 시장구분
    is_active BOOLEAN DEFAULT TRUE,            -- 활성상태
    raw_data JSONB,                           -- 원본 API 응답 데이터
    created_at TIMESTAMP DEFAULT NOW(),        -- 생성일시
    updated_at TIMESTAMP DEFAULT NOW()         -- 수정일시
);

-- 인덱스
CREATE INDEX idx_kis_holidays_date ON kis_domestic_holidays(holiday_date);
CREATE INDEX idx_kis_holidays_active ON kis_domestic_holidays(is_active);
CREATE INDEX idx_kis_holidays_created ON kis_domestic_holidays(created_at);
```

### 저장되는 데이터 예시
```json
{
  "holiday_date": "2025-01-01",
  "holiday_name": "신정",
  "market_type": "DOMESTIC",
  "is_active": true,
  "raw_data": {
    "bzdy_dd": "20250101",
    "bzdy_nm": "신정",
    "wday_dvsn_cd": "7"
  }
}
```

## KIS API 응답 구조

### TCA0903R API 응답 예시
```json
{
  "rt_cd": "0",
  "msg_cd": "MCA00000",
  "msg1": "정상처리",
  "output": [
    {
      "bzdy_dd": "20250101",        // 영업일자 (휴장일)
      "bzdy_nm": "신정",            // 휴장일명
      "wday_dvsn_cd": "7",         // 요일구분코드
      "stck_clsg_yn": "Y"          // 주식시장 휴장여부
    },
    {
      "bzdy_dd": "20250128",
      "bzdy_nm": "설날 연휴",
      "wday_dvsn_cd": "2",
      "stck_clsg_yn": "Y"
    }
  ]
}
```

## 성능 및 제약사항

### KIS API 제약사항
- **호출 제한**: 1일 1회만 호출 가능
- **데이터 범위**: 향후 1년간의 휴장일 정보
- **응답 시간**: 평균 1-3초
- **토큰 만료**: 6시간마다 갱신 필요

### 처리 성능
- **데이터 양**: 연간 약 60-100개 휴장일
- **처리 시간**: 평균 30초 내외
- **메모리 사용**: 1MB 이하
- **저장 용량**: 휴장일당 약 500bytes

### 오류 처리 및 재시도
```python
# 재시도 설정
default_args = {
    'retries': 3,
    'retry_delay': timedelta(minutes=30)
}

# API 호출 실패 시
try:
    response = requests.get(api_url, timeout=30)
except requests.exceptions.Timeout:
    logging.error("⏰ KIS API 응답 시간 초과")
    raise
except requests.exceptions.ConnectionError:
    logging.error("🌐 KIS API 연결 실패")
    raise
```

## 모니터링 및 알람

### 주요 로그 메시지
```python
# 정상 처리
"✅ 휴장일 데이터 수신 성공: {count}건"
"💾 휴장일 데이터 저장 완료: 신규 {new}건, 업데이트 {update}건"
"✅ 휴장일 데이터 검증 완료: {total}건"

# 경고 상황
"⚠️ 잘못된 날짜 형식 스킵: {date}"
"⚠️ 중복된 휴장일 발견: {count}건"
"⚠️ 저장할 휴장일 데이터가 없습니다"

# 오류 상황
"❌ KIS API 호출 실패: {error}"
"❌ 휴장일 데이터 처리 실패: {error}"
"❌ 휴장일 저장 실패: {date} - {error}"
```

### 알람 조건
- **API 호출 실패**: 3회 재시도 후 실패 시 알람
- **데이터 없음**: 응답에 휴장일 데이터가 없을 때
- **중복 데이터**: 동일 날짜의 중복 휴장일 발견
- **DB 연결 실패**: PostgreSQL 연결 불가

## 실행 및 확인 방법

### 수동 실행
```bash
# Airflow CLI를 통한 실행
airflow dags trigger kis_holiday_sync

# 특정 날짜로 backfill
airflow dags backfill kis_holiday_sync -s 2025-09-01 -e 2025-09-01
```

### 결과 확인 쿼리
```sql
-- 최근 저장된 휴장일 확인
SELECT 
    holiday_date,
    holiday_name,
    created_at,
    updated_at
FROM kis_domestic_holidays 
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY holiday_date;

-- 향후 휴장일 목록
SELECT 
    holiday_date,
    holiday_name,
    EXTRACT(DOW FROM holiday_date) as day_of_week
FROM kis_domestic_holidays 
WHERE holiday_date >= CURRENT_DATE 
AND is_active = TRUE
ORDER BY holiday_date
LIMIT 10;

-- 월별 휴장일 통계
SELECT 
    EXTRACT(YEAR FROM holiday_date) as year,
    EXTRACT(MONTH FROM holiday_date) as month,
    COUNT(*) as holiday_count
FROM kis_domestic_holidays 
WHERE is_active = TRUE
GROUP BY EXTRACT(YEAR FROM holiday_date), EXTRACT(MONTH FROM holiday_date)
ORDER BY year, month;
```

## 비즈니스 활용

### 1. 거래 시스템 연동
```sql
-- 거래 가능일 체크 함수
CREATE OR REPLACE FUNCTION is_trading_day(check_date DATE)
RETURNS BOOLEAN AS $$
BEGIN
    -- 주말 체크
    IF EXTRACT(DOW FROM check_date) IN (0, 6) THEN
        RETURN FALSE;
    END IF;
    
    -- 휴장일 체크
    IF EXISTS (
        SELECT 1 FROM kis_domestic_holidays 
        WHERE holiday_date = check_date 
        AND is_active = TRUE
    ) THEN
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;
```

### 2. 다음 거래일 계산
```sql
-- 다음 거래일 조회
WITH RECURSIVE next_trading_days AS (
    SELECT CURRENT_DATE + 1 as check_date
    
    UNION ALL
    
    SELECT check_date + 1
    FROM next_trading_days
    WHERE NOT is_trading_day(check_date)
    AND check_date < CURRENT_DATE + 30  -- 최대 30일 후까지
)
SELECT MIN(check_date) as next_trading_day
FROM next_trading_days
WHERE is_trading_day(check_date);
```

### 3. 배치 작업 스케줄링
```python
# 휴장일을 고려한 배치 작업 스케줄링
def should_run_trading_batch(execution_date):
    """거래일에만 배치 작업 실행"""
    cursor.execute(
        "SELECT is_trading_day(%s)", 
        (execution_date.date(),)
    )
    return cursor.fetchone()[0]

# DAG에서 사용
if not should_run_trading_batch(context['execution_date']):
    return "SKIP"
```

## 확장 계획

### 단기 계획
- **해외 휴장일**: NYSE, NASDAQ 휴장일 추가
- **공휴일 알림**: 다가오는 휴장일 Slack 알림
- **API 캐싱**: 중복 호출 방지 캐싱 시스템

### 장기 계획
- **실시간 업데이트**: 임시 휴장일 긴급 업데이트
- **다국가 지원**: 아시아 주요국 휴장일 통합 관리
- **달력 연동**: Google Calendar, Outlook 연동

---

**문서 작성일**: 2025-09-06  
**작성자**: Quantum Trading Platform Team  
**버전**: 1.0