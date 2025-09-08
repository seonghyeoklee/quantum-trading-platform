# 🔢 DAG 번호 체계 가이드

## 📋 번호 체계 규칙

### **00~09: System_Auth__ (시스템 인증)**
- **00**: 가장 높은 우선순위 (토큰 관리)
- **01**: 기초 데이터 동기화

### **10~29: Stock_Data__ (주식 데이터)**  
- **10**: 마스터 데이터 (기초)
- **11**: 메인 수집기
- **12**: 일별 데이터
- **13**: 특정 데이터 수집
- **14**: 실시간/가격 데이터

### **30~49: AI_Analysis__ (AI 분석)** [미래 확장]
- **30**: 기술적 분석
- **31**: ML 신호 생성
- **32**: 시장 감성 분석
- **33**: 예측 모델

### **50~69: Portfolio__ (포트폴리오)** [미래 확장]
- **50**: 리스크 관리
- **51**: 리밸런싱
- **52**: 성과 추적
- **53**: 백테스팅

## 🎯 현재 적용된 DAG들

### 🔧 **System_Auth__ 그룹**
- `System_Auth__00_KIS_Token_Renewal` - KIS 토큰 자동 갱신 (5시간마다)
- `System_Auth__01_Holiday_Sync` - KIS 휴장일 동기화 (매일 6시)

### 📊 **Stock_Data__ 그룹**
- `Stock_Data__10_Master_Import` - 국내주식 마스터 임포트 (주중 새벽 2시)
- `Stock_Data__11_Comprehensive_Collector` - 전체 종목 차트 수집 (주중 오후 8시)
- ~~`Stock_Data__12_Daily_Charts`~~ - **삭제됨** (11번과 중복 기능)
- ~~`Stock_Data__13_Domestic_Collection`~~ - **삭제됨** (중복 기능)
- `Stock_Data__14_Price_Collector` - 실시간 가격 수집 (주중 오후 4시)
- `Stock_Data__15_New_Stock_Backfill` - 신규 종목 백필 (주 1회, 2년치 히스토리)
- `Stock_Data__16_Daily_Update` - 기존 종목 일일 업데이트 (주중 오후 9시)

## ⏰ 실행 순서 및 의존성

### **일반적인 실행 플로우**
```
00. KIS_Token_Renewal (토큰 확보)
    ↓
01. Holiday_Sync (휴장일 정보)
    ↓
10. Master_Import (기초 종목 데이터)
    ↓
11. Comprehensive_Collector (차트 데이터 수집)
    ↓
15. New_Stock_Backfill (신규 종목 2년 히스토리) [주간]
    ↓
16. Daily_Update (기존 종목 일일 데이터) [일간]
    ↓
14. Price_Collector (가격 업데이트)
```

### **스케줄 시간표**
- **새벽 1시 (일요일)**: 15번 (신규 종목 백필)
- **새벽 2시**: 10번 (마스터 임포트)
- **오전 6시**: 01번 (휴장일 동기화)  
- **오후 4시**: 14번 (가격 수집)
- **오후 8시**: 11번 (종합 차트 수집)
- **오후 9시**: 16번 (일일 업데이트)
- **5시간마다**: 00번 (토큰 갱신)

## 🔍 Airflow UI에서 확인

번호 순서대로 자동 정렬되어 표시:
```
System_Auth__00_KIS_Token_Renewal
System_Auth__01_Holiday_Sync
Stock_Data__10_Master_Import
Stock_Data__11_Comprehensive_Collector
Stock_Data__14_Price_Collector
Stock_Data__15_New_Stock_Backfill
Stock_Data__16_Daily_Update
```

## 📈 미래 확장 계획

### **AI_Analysis__ 그룹 예정**
- `AI_Analysis__30_Technical_Indicators`
- `AI_Analysis__31_ML_Signal_Generation`
- `AI_Analysis__32_Market_Sentiment`

### **Portfolio__ 그룹 예정**
- `Portfolio__50_Risk_Management`  
- `Portfolio__51_Auto_Rebalancing`
- `Portfolio__52_Performance_Tracking`

## 💡 네이밍 규칙

1. **그룹명__번호_기능명** 형식
2. **번호는 2자리** (00~99)
3. **실행 우선순위** 순으로 번호 배정
4. **의존성 관계** 고려한 순서
5. **확장성** 고려한 번호 간격