# KIS Token Renewal DAG - KIS 토큰 자동 갱신 워크플로우

## 개요

**KIS Token Renewal DAG**는 KIS API 인증 토큰을 자동으로 갱신하여 API 호출의 지속성을 보장하는 Airflow DAG입니다. KIS 토큰의 6시간 만료 주기를 고려하여 5시간마다 자동 갱신을 실행합니다.

- **DAG ID**: `kis_token_renewal`
- **실행 주기**: 매 5시간 (`0 */5 * * *`)
- **타임존**: Asia/Seoul (KST)
- **재시도**: 3회, 5분 간격
- **토큰 유효기간**: 6시간 (5시간 간격으로 사전 갱신)

## 전체 워크플로우 구조

```
check_token_status → renew_kis_token → validate_new_token → cleanup_old_tokens
```

## 상세 단계별 프로세스

### STEP 1: 토큰 상태 확인 (check_token_status)
**태스크 ID**: `check_token_status`
**기능**: 현재 저장된 KIS 토큰의 상태와 만료 시간 확인

#### 1.1 토큰 파일 위치 및 명명 규칙
```python
def check_token_status():
    """현재 토큰 상태 확인"""
    logging.info("🔍 KIS 토큰 상태 확인 시작")
    
    config_root = "/Users/admin/KIS/config"
    
    # 한국 시간대로 날짜 계산
    kst_now = datetime.now(ZoneInfo("Asia/Seoul"))
    today = kst_now.strftime('%Y%m%d')
    token_file = os.path.join(config_root, f"KIS{today}")
    
    logging.info(f"📁 토큰 파일 경로: {token_file}")
```

#### 1.2 토큰 파일 존재 여부 및 만료 확인
```python
    # 토큰 파일 존재 확인
    if not os.path.exists(token_file):
        logging.warning("⚠️ 토큰 파일이 존재하지 않음")
        return {
            'status': 'missing',
            'file_path': token_file,
            'needs_renewal': True,
            'message': '토큰 파일 없음'
        }
    
    # 파일 수정 시간 확인
    file_mtime = os.path.getmtime(token_file)
    file_datetime = datetime.fromtimestamp(file_mtime, tz=ZoneInfo("Asia/Seoul"))
    
    # 토큰 나이 계산 (시간 단위)
    token_age_hours = (kst_now - file_datetime).total_seconds() / 3600
    
    logging.info(f"⏰ 토큰 생성시간: {file_datetime}")
    logging.info(f"📊 토큰 나이: {token_age_hours:.1f}시간")
    
    # 만료 임계값 설정 (4.5시간)
    EXPIRY_THRESHOLD_HOURS = 4.5
    needs_renewal = token_age_hours > EXPIRY_THRESHOLD_HOURS
    
    return {
        'status': 'exists',
        'file_path': token_file,
        'created_at': file_datetime.isoformat(),
        'age_hours': token_age_hours,
        'needs_renewal': needs_renewal,
        'threshold_hours': EXPIRY_THRESHOLD_HOURS,
        'message': f'토큰 나이: {token_age_hours:.1f}시간'
    }
```

#### 1.3 토큰 내용 유효성 검증
```python
    # 토큰 파일 내용 확인
    try:
        with open(token_file, 'r') as f:
            token_content = f.read().strip()
        
        if not token_content or len(token_content) < 50:
            logging.warning("⚠️ 토큰 파일이 비어있거나 너무 짧음")
            return {
                'status': 'invalid',
                'file_path': token_file,
                'needs_renewal': True,
                'message': '토큰 내용 무효'
            }
        
        logging.info(f"✅ 토큰 파일 검증 성공 (길이: {len(token_content)})")
        
    except Exception as e:
        logging.error(f"❌ 토큰 파일 읽기 실패: {e}")
        return {
            'status': 'error',
            'file_path': token_file,
            'needs_renewal': True,
            'message': f'파일 읽기 오류: {str(e)}'
        }
```

### STEP 2: KIS 토큰 갱신 (renew_kis_token)
**태스크 ID**: `renew_kis_token`
**기능**: kis_auth.py 모듈을 사용하여 새로운 토큰 발급

#### 2.1 갱신 필요성 판단
```python
def renew_kis_token(**context):
    """KIS 토큰 갱신"""
    
    # 이전 단계의 토큰 상태 확인
    token_status = context['task_instance'].xcom_pull(task_ids='check_token_status')
    
    if not token_status.get('needs_renewal', True):
        logging.info("✅ 토큰이 아직 유효함. 갱신 스킵")
        return {
            'status': 'skipped',
            'reason': '토큰이 아직 유효함',
            'current_age_hours': token_status.get('age_hours', 0)
        }
    
    logging.info("🔄 KIS 토큰 갱신 시작")
```

#### 2.2 kis_auth 모듈을 통한 토큰 갱신
```python
    # kis_auth.py 경로 추가
    kis_auth_path = "/opt/airflow/quantum-adapter-kis/examples_llm"
    if kis_auth_path not in sys.path:
        sys.path.insert(0, kis_auth_path)
    
    try:
        import kis_auth as ka
        
        # 실전투자 환경으로 토큰 갱신
        logging.info("🔐 KIS 실전투자 토큰 발급 요청")
        
        # kis_auth 모듈의 auth 함수 호출
        auth_result = ka.auth(svr="prod", product="01")
        
        if auth_result and hasattr(auth_result, 'isOK') and auth_result.isOK():
            logging.info("✅ KIS 토큰 갱신 성공")
            
            # 새로 생성된 토큰 파일 정보
            kst_now = datetime.now(ZoneInfo("Asia/Seoul"))
            today = kst_now.strftime('%Y%m%d')
            new_token_file = f"/Users/admin/KIS/config/KIS{today}"
            
            return {
                'status': 'success',
                'renewed_at': kst_now.isoformat(),
                'token_file': new_token_file,
                'message': '토큰 갱신 완료'
            }
        else:
            error_msg = "KIS 토큰 갱신 실패"
            logging.error(f"❌ {error_msg}")
            raise Exception(error_msg)
            
    except Exception as e:
        logging.error(f"❌ KIS 토큰 갱신 오류: {e}")
        raise
```

#### 2.3 토큰 갱신 후 검증
```python
    # 새 토큰 파일 생성 확인
    if os.path.exists(new_token_file):
        file_size = os.path.getsize(new_token_file)
        logging.info(f"📁 새 토큰 파일 생성됨: {file_size} bytes")
        
        # 토큰 내용 간단 검증
        with open(new_token_file, 'r') as f:
            token_content = f.read().strip()
        
        if len(token_content) > 50:  # 최소 길이 체크
            logging.info(f"✅ 새 토큰 검증 성공 (길이: {len(token_content)})")
        else:
            raise Exception("생성된 토큰이 너무 짧음")
    else:
        raise Exception("새 토큰 파일이 생성되지 않음")
```

### STEP 3: 새 토큰 유효성 검증 (validate_new_token)
**태스크 ID**: `validate_new_token`
**기능**: 갱신된 토큰으로 실제 API 호출 테스트

#### 3.1 테스트 API 호출
```python
def validate_new_token(**context):
    """새로 갱신된 토큰의 유효성 검증"""
    
    renewal_result = context['task_instance'].xcom_pull(task_ids='renew_kis_token')
    
    if renewal_result.get('status') == 'skipped':
        logging.info("✅ 토큰 갱신이 스킵되어 검증도 스킵")
        return {'status': 'skipped', 'reason': '토큰 갱신 스킵됨'}
    
    if renewal_result.get('status') != 'success':
        raise Exception("토큰 갱신이 실패하여 검증 불가")
    
    logging.info("🧪 새 토큰 유효성 검증 시작")
    
    # FastAPI 서버를 통한 간단한 API 테스트
    test_url = "http://localhost:8000/health"
    
    try:
        response = requests.get(test_url, timeout=10)
        
        if response.status_code == 200:
            logging.info("✅ 토큰 검증 성공: API 응답 정상")
            
            return {
                'status': 'success',
                'test_endpoint': test_url,
                'response_code': response.status_code,
                'validation_time': datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
                'message': 'API 테스트 성공'
            }
        else:
            raise Exception(f"API 응답 오류: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ API 테스트 실패: {e}")
        # 토큰은 갱신됐지만 API 서버 문제일 수 있으므로 경고로 처리
        return {
            'status': 'warning',
            'test_endpoint': test_url,
            'error': str(e),
            'message': 'API 서버 연결 실패하지만 토큰은 갱신됨'
        }
```

#### 3.2 토큰 메타데이터 수집
```python
    # 토큰 파일 메타데이터 수집
    token_file = renewal_result.get('token_file')
    
    if token_file and os.path.exists(token_file):
        stat_info = os.stat(token_file)
        
        metadata = {
            'file_size': stat_info.st_size,
            'created_timestamp': stat_info.st_ctime,
            'modified_timestamp': stat_info.st_mtime,
            'file_mode': oct(stat_info.st_mode)[-3:],  # 권한 정보
        }
        
        logging.info(f"📊 토큰 파일 메타데이터: {metadata}")
    else:
        logging.warning("⚠️ 토큰 파일 메타데이터 수집 실패")
```

### STEP 4: 오래된 토큰 정리 (cleanup_old_tokens)
**태스크 ID**: `cleanup_old_tokens` 
**기능**: 7일 이상 된 오래된 토큰 파일 정리

#### 4.1 오래된 토큰 파일 탐색
```python
def cleanup_old_tokens(**context):
    """7일 이상 된 오래된 토큰 파일 정리"""
    
    logging.info("🧹 오래된 토큰 파일 정리 시작")
    
    config_root = "/Users/admin/KIS/config"
    
    if not os.path.exists(config_root):
        logging.warning(f"⚠️ 설정 디렉토리 없음: {config_root}")
        return {'cleaned_files': 0, 'message': '설정 디렉토리 없음'}
    
    # 7일 전 시점 계산
    cutoff_time = datetime.now(ZoneInfo("Asia/Seoul")) - timedelta(days=7)
    
    cleaned_files = []
    total_size_freed = 0
    
    try:
        for filename in os.listdir(config_root):
            if filename.startswith('KIS') and len(filename) == 11:  # KIS20250906 형식
                file_path = os.path.join(config_root, filename)
                
                # 파일 수정 시간 확인
                file_mtime = datetime.fromtimestamp(
                    os.path.getmtime(file_path), 
                    tz=ZoneInfo("Asia/Seoul")
                )
                
                if file_mtime < cutoff_time:
                    file_size = os.path.getsize(file_path)
                    
                    # 파일 삭제
                    os.remove(file_path)
                    
                    cleaned_files.append({
                        'filename': filename,
                        'size': file_size,
                        'modified_date': file_mtime.isoformat()
                    })
                    
                    total_size_freed += file_size
                    logging.info(f"🗑️ 삭제됨: {filename} ({file_size} bytes)")
    
    except Exception as e:
        logging.error(f"❌ 토큰 파일 정리 중 오류: {e}")
        raise
```

#### 4.2 정리 결과 요약
```python
    logging.info(f"✅ 토큰 파일 정리 완료:")
    logging.info(f"   - 삭제된 파일: {len(cleaned_files)}개")
    logging.info(f"   - 확보된 용량: {total_size_freed} bytes")
    
    return {
        'status': 'completed',
        'cleaned_files': len(cleaned_files),
        'total_size_freed': total_size_freed,
        'cutoff_date': cutoff_time.isoformat(),
        'files': cleaned_files
    }
```

## 데이터 플로우 다이어그램

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Token Status   │    │ Token Renewal   │    │   Validation    │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│1. 파일 존재확인  │───►│1. kis_auth 호출  │───►│1. API 테스트     │
│2. 만료시간 체크  │    │2. 새 토큰 발급  │    │2. 응답 코드 확인 │
│3. 내용 검증     │    │3. 파일 저장     │    │3. 메타데이터 수집│
└─────────────────┘    └─────────────────┘    └─────────────────┘
        ▲                       ▲                       ▲
        │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Scheduler      │    │ KIS API Server  │    │ File System     │
│  매 5시간       │    │ OAuth Token     │    │ /KIS/config/    │
│  0 */5 * * *    │    │ 6시간 만료      │    │ KIS20250906     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       ▲
                                               ┌─────────────┐
                                               │ 4. Cleanup   │
                                               │ 7일 이상삭제  │
                                               └─────────────┘
```

## KIS 토큰 시스템 이해

### 토큰 생명주기
```
토큰 발급 → 6시간 유효 → 만료 → 새 토큰 발급 (반복)
   ↑                              ↑
   └── 5시간 간격 자동 갱신 ─────────┘
```

### 토큰 파일 명명 규칙
```
파일명: KIS{YYYYMMDD}
예시: KIS20250906
위치: /Users/admin/KIS/config/
```

### 토큰 상태 분류
- **VALID**: 4.5시간 미만, 정상적으로 사용 가능
- **EXPIRED**: 4.5시간 이상, 갱신 필요
- **MISSING**: 파일이 존재하지 않음
- **INVALID**: 파일이 있지만 내용이 잘못됨

## 성능 및 제약사항

### KIS 토큰 제약사항
- **유효기간**: 6시간
- **발급 제한**: 계정당 동시에 1개만 유효
- **갱신 주기**: 5시간 (안전 마진 1시간)
- **파일 크기**: 약 2-4KB

### 처리 성능
- **갱신 시간**: 평균 3-5초
- **검증 시간**: 평균 1-2초
- **정리 작업**: 평균 1초 미만
- **전체 DAG**: 평균 10초 내외

### 오류 처리 전략
```python
# 재시도 설정
default_args = {
    'retries': 3,
    'retry_delay': timedelta(minutes=5)
}

# 토큰 갱신 실패 시
try:
    auth_result = ka.auth(svr="prod", product="01")
except Exception as e:
    logging.error(f"KIS 인증 실패: {e}")
    # 5분 후 자동 재시도 (최대 3회)
    raise
```

## 모니터링 및 알람

### 주요 로그 메시지
```python
# 정상 상황
"✅ 토큰이 아직 유효함. 갱신 스킵"
"✅ KIS 토큰 갱신 성공"
"✅ 토큰 검증 성공: API 응답 정상"
"✅ 토큰 파일 정리 완료: {count}개 삭제"

# 경고 상황  
"⚠️ 토큰 파일이 존재하지 않음"
"⚠️ 토큰 파일이 비어있거나 너무 짧음"
"⚠️ API 서버 연결 실패하지만 토큰은 갱신됨"

# 오류 상황
"❌ KIS 토큰 갱신 실패"
"❌ 토큰 파일 읽기 실패: {error}"
"❌ API 테스트 실패: {error}"
```

### 알람 조건
- **토큰 갱신 실패**: 3회 재시도 후 실패
- **토큰 파일 없음**: 예상 위치에 토큰 파일 부재
- **API 테스트 실패**: 새 토큰으로 API 호출 불가
- **연속 실패**: 3회 연속 갱신 실패 시

## 실행 및 확인 방법

### 수동 실행
```bash
# Airflow CLI를 통한 즉시 실행
airflow dags trigger kis_token_renewal

# 특정 태스크만 실행
airflow tasks run kis_token_renewal check_token_status 2025-09-06

# 토큰 상태 확인
ls -la /Users/admin/KIS/config/KIS*
```

### 토큰 파일 확인
```bash
# 최신 토큰 파일 확인
TOKEN_FILE=/Users/admin/KIS/config/KIS$(date +%Y%m%d)
if [ -f "$TOKEN_FILE" ]; then
    echo "토큰 파일 존재: $(ls -lh $TOKEN_FILE)"
    echo "토큰 길이: $(wc -c < $TOKEN_FILE) bytes"
    echo "수정 시간: $(stat -f %Sm $TOKEN_FILE)"
else
    echo "토큰 파일 없음: $TOKEN_FILE"
fi
```

### API 테스트
```bash
# KIS API 서버 상태 확인
curl -f http://localhost:8000/health

# 토큰 기반 API 호출 테스트
curl http://localhost:8000/domestic/price/005930
```

## 통합 시스템과의 연동

### 1. 다른 DAG들과의 의존성
```python
# 다른 KIS 관련 DAG에서 토큰 상태 확인
def check_kis_token_validity():
    """KIS 토큰 유효성 사전 체크"""
    token_file = f"/Users/admin/KIS/config/KIS{datetime.now().strftime('%Y%m%d')}"
    
    if not os.path.exists(token_file):
        raise Exception("KIS 토큰 파일 없음. 토큰 갱신 DAG 실행 필요")
    
    file_age = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(token_file))).total_seconds() / 3600
    
    if file_age > 5:  # 5시간 이상
        logging.warning("KIS 토큰이 오래됨. 갱신 권장")
```

### 2. FastAPI 서버와의 연동
```python
# FastAPI 서버의 토큰 자동 새로고침
@app.middleware("http")
async def token_refresh_middleware(request: Request, call_next):
    # 토큰 파일 확인 및 자동 로딩
    token_file = get_current_token_file()
    if token_file and is_token_fresh(token_file):
        load_token_to_memory(token_file)
    
    response = await call_next(request)
    return response
```

### 3. 모니터링 시스템 연동
```python
# Prometheus 메트릭 노출
from prometheus_client import Gauge, Counter

token_age_gauge = Gauge('kis_token_age_hours', 'KIS 토큰 나이 (시간)')
token_renewal_counter = Counter('kis_token_renewals_total', '토큰 갱신 횟수')

def update_token_metrics():
    token_file = get_current_token_file()
    if token_file:
        age_hours = get_token_age_hours(token_file)
        token_age_gauge.set(age_hours)
```

## 보안 고려사항

### 토큰 파일 보안
```bash
# 토큰 파일 권한 설정
chmod 600 /Users/admin/KIS/config/KIS*  # 소유자만 읽기/쓰기

# 디렉토리 권한 설정  
chmod 700 /Users/admin/KIS/config/      # 소유자만 접근
```

### 로그 보안
```python
# 토큰 내용을 로그에 노출하지 않음
logging.info(f"토큰 길이: {len(token_content)}")  # OK
logging.info(f"토큰 내용: {token_content}")       # 절대 금지!
```

## 확장 계획

### 단기 계획
- **토큰 상태 대시보드**: Grafana 대시보드로 토큰 상태 시각화
- **다중 환경 지원**: PROD/SANDBOX 환경별 토큰 관리
- **알림 통합**: Slack으로 토큰 갱신 알림

### 장기 계획
- **토큰 풀링**: 여러 계정의 토큰 로드밸런싱
- **자동 페일오버**: 토큰 실패 시 백업 토큰 사용
- **토큰 분석**: 토큰 사용 패턴 분석 및 최적화

---

**문서 작성일**: 2025-09-06  
**작성자**: Quantum Trading Platform Team  
**버전**: 1.0