# DAG Documentation Template - Airflow DAG 표준 문서화 템플릿

## 개요

이 템플릿은 Quantum Trading Platform의 모든 Airflow DAG 문서화를 위한 표준화된 형식을 제공합니다. 각 DAG마다 이 템플릿을 따라 상세한 문서를 작성하여 유지보수성과 이해도를 높입니다.

## 문서 구조 표준

### 1. 헤더 및 개요
```markdown
# [DAG Name] - [Brief Description] 워크플로우

## 개요

**[DAG Display Name]**은 [핵심 기능 설명] Airflow DAG입니다.

- **DAG ID**: `dag_id_here`
- **실행 주기**: [스케줄 정보]
- **타임존**: Asia/Seoul (KST)
- **재시도**: [횟수], [간격]
- **주요 기능**: [핵심 기능 요약]
```

### 2. 워크플로우 구조
```markdown
## 전체 워크플로우 구조

```
task_1 → task_2 → task_3 → task_4
```

## 상세 단계별 프로세스

### STEP 1: [First Task Name] (task_id)
**태스크 ID**: `first_task_id`
**기능**: [태스크 기능 설명]

#### 1.1 [Sub Process Name]
[상세 구현 로직]

#### 1.2 [Next Sub Process]  
[다음 세부 프로세스]
```

### 3. 필수 섹션들

#### A. 데이터 플로우 다이어그램
```markdown
## 데이터 플로우 다이어그램

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Source   │    │  Processing     │    │   Data Store    │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ Input Type      │───►│ Process Step    │───►│ Output Table    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```
```

#### B. 성능 및 제약사항
```markdown
## 성능 및 제약사항

### [External System] 제약사항
- **제한사항**: [API 호출 제한 등]
- **성능**: [처리 시간, 용량 등]

### 처리 성능
- **처리량**: [처리 가능한 데이터량]
- **실행시간**: [예상 실행 시간]
- **메모리 사용**: [메모리 요구사항]

### 오류 처리
[오류 처리 로직 및 재시도 전략]
```

#### C. 모니터링 및 로그
```markdown
## 모니터링 및 로그

### 주요 로그 메시지
```python
# 정상 처리
"✅ [성공 메시지 패턴]"

# 경고 상황
"⚠️ [경고 메시지 패턴]"

# 오류 상황
"❌ [오류 메시지 패턴]"
```

### 알람 조건
- **[Condition 1]**: [알람 조건과 대응]
- **[Condition 2]**: [알람 조건과 대응]
```

#### D. 실행 및 확인 방법
```markdown
## 실행 및 확인 방법

### 수동 실행
```bash
# Airflow CLI를 통한 실행
airflow dags trigger [dag_id]

# 특정 태스크 실행
airflow tasks run [dag_id] [task_id] [execution_date]
```

### 결과 확인 쿼리
```sql
-- [확인용 쿼리 제목]
SELECT ... FROM ...;
```
```

#### E. 확장 계획
```markdown
## 확장 계획

### 단기 계획
- **[Feature 1]**: [설명]
- **[Feature 2]**: [설명]

### 장기 계획  
- **[Long-term Goal 1]**: [설명]
- **[Long-term Goal 2]**: [설명]
```

## 기존 DAG 문서 예시

현재 프로젝트에 완성된 DAG 문서들:

### 1. ✅ Stock Master Sync DAG
**파일**: `stock_master_sync_README.md`
- **기능**: 국내/해외 종목 마스터 데이터 동기화
- **특징**: 6단계 워크플로우, UPSERT 로직, 중복 제거

### 2. ✅ Domestic Stock Data Collection DAG  
**파일**: `domestic_stock_data_collection_dag_README.md`
- **기능**: DDD 기반 국내주식 상세 데이터 수집
- **특징**: 자동 종목 조회, 스케줄 실행, 새로운 테이블 구조

### 3. ✅ KIS Holiday Sync DAG
**파일**: `kis_holiday_sync_dag_README.md`  
- **기능**: 한국 주식시장 휴장일 동기화
- **특징**: 1일 1회 제한, 비즈니스 로직 연동

### 4. ✅ KIS Token Renewal DAG
**파일**: `kis_token_renewal_README.md`
- **기능**: KIS API 토큰 자동 갱신
- **특징**: 5시간 주기, 토큰 생명주기 관리

## 문서화 가이드라인

### 코드 블록 표준
```python
# Python 코드는 이렇게
def example_function():
    """함수 설명"""
    return "결과"
```

```sql
-- SQL 쿼리는 이렇게
SELECT column1, column2 
FROM table_name 
WHERE condition = 'value';
```

```bash
# Bash 명령어는 이렇게
airflow dags trigger dag_name
```

### 이모지 사용 표준
- ✅ 성공, 완료
- ❌ 실패, 오류
- ⚠️ 경고, 주의
- 📊 데이터, 통계
- 🔄 진행중, 처리중
- 🚀 시작, 실행
- 💾 저장, 데이터베이스
- 🔍 확인, 검증
- 📈 결과, 성과
- 🧹 정리, 클린업

### 섹션 번호 체계
```
## 주요 섹션 (##)
### STEP N: 단계별 프로세스 (###)  
#### N.N 세부 프로세스 (####)
```

## 문서 메타데이터 표준

모든 DAG 문서는 다음으로 끝나야 합니다:

```markdown
---

**문서 작성일**: YYYY-MM-DD  
**작성자**: Quantum Trading Platform Team  
**버전**: 1.0
**최종 수정**: YYYY-MM-DD
**검토자**: [검토자명]
```

## 품질 체크리스트

새 DAG 문서 작성 시 다음 항목들을 확인하세요:

### 📋 필수 섹션 포함 여부
- [ ] 개요 및 DAG 기본 정보
- [ ] 전체 워크플로우 구조  
- [ ] 단계별 상세 프로세스 (STEP N 형식)
- [ ] 데이터 플로우 다이어그램
- [ ] 성능 및 제약사항
- [ ] 모니터링 및 로그
- [ ] 실행 및 확인 방법
- [ ] 확장 계획
- [ ] 문서 메타데이터

### 📋 내용 품질 체크
- [ ] 모든 태스크의 기능 설명 포함
- [ ] 실제 코드 스니펫 제공
- [ ] 오류 처리 방법 명시
- [ ] API/DB 스키마 정보 포함
- [ ] 실행 가능한 예시 명령어
- [ ] 성능 메트릭 및 임계값
- [ ] 로그 메시지 패턴 정의

### 📋 문서 형식 체크  
- [ ] 마크다운 문법 준수
- [ ] 일관된 이모지 사용
- [ ] 적절한 코드 블록 언어 지정
- [ ] 섹션 번호 체계 준수
- [ ] 다이어그램 ASCII 아트 포함

## 문서 업데이트 정책

### 업데이트 시점
1. **DAG 코드 변경 시**: 기능 추가/수정/삭제
2. **성능 개선 시**: 처리 시간, 메모리 사용량 변경  
3. **오류 패턴 발견 시**: 새로운 오류 상황 추가
4. **운영 경험 축적**: 모니터링, 알람 조건 개선

### 버전 관리
- **Major**: 1.0 → 2.0 (DAG 구조 대폭 변경)
- **Minor**: 1.0 → 1.1 (새로운 섹션 추가)  
- **Patch**: 1.1 → 1.1.1 (오타 수정, 내용 보완)

## 관련 도구 및 자동화

### 문서 검증 도구
```bash
# 마크다운 문법 검사
markdownlint *.md

# 링크 검증
markdown-link-check *.md

# 맞춤법 검사  
aspell check *.md
```

### 자동 생성 스크립트
```python
# DAG 메타데이터 추출 스크립트 예시
def extract_dag_info(dag_file_path):
    """DAG 파일에서 기본 정보 추출"""
    return {
        'dag_id': extract_dag_id(dag_file_path),
        'schedule': extract_schedule(dag_file_path),
        'tasks': extract_task_list(dag_file_path)
    }
```

이 템플릿을 활용하여 모든 새로운 DAG에 대해 일관되고 상세한 문서를 작성하시기 바랍니다. 

---

**문서 작성일**: 2025-09-06  
**작성자**: Quantum Trading Platform Team  
**버전**: 1.0