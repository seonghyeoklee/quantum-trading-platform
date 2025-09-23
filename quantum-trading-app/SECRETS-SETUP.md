# 🔒 시크릿 설정 가이드

DINO 테스트 애플리케이션을 실행하기 위한 KIS API 시크릿 설정 방법입니다.

## 🚨 보안 주의사항

**절대로 실제 API 키나 계좌번호를 git에 커밋하지 마세요!**

- ✅ 환경변수 사용
- ✅ 로컬 설정 파일 사용 (git ignore됨)
- ❌ application.yml에 직접 입력 금지

## 📋 필요한 정보

KIS API를 사용하기 위해 다음 정보가 필요합니다:

### 1. KIS 개발자센터에서 발급받는 정보
- **실전투자 앱키** (KIS_MY_APP)
- **실전투자 앱시크릿** (KIS_MY_SEC)
- **모의투자 앱키** (KIS_PAPER_APP)
- **모의투자 앱시크릿** (KIS_PAPER_SEC)

### 2. 한국투자증권 계좌 정보
- **HTS ID** (KIS_MY_HTS_ID)
- **증권계좌번호** (KIS_MY_ACCT_STOCK)
- **선물계좌번호** (KIS_MY_ACCT_FUTURE)
- **모의투자 계좌번호들** (KIS_MY_PAPER_STOCK, KIS_MY_PAPER_FUTURE)

## ⚙️ 설정 방법

### 방법 1: 환경변수 사용 (권장)

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집하여 실제 값 입력
vi .env
```

### 방법 2: 로컬 설정 파일 사용

```bash
# application-local.yml 파일에 실제 값 입력
vi src/main/resources/application-local.yml
```

## 🏃‍♂️ 애플리케이션 실행

### 환경변수 방법으로 실행
```bash
# .env 파일이 있으면 자동으로 로드됨
./gradlew bootRun

# 또는 환경변수 직접 설정
export KIS_MY_APP=your-app-key
export KIS_MY_SEC=your-secret-key
./gradlew bootRun
```

### 로컬 프로파일로 실행
```bash
# application-local.yml 사용
./gradlew bootRun --args='--spring.profiles.active=local'
```

## 🧪 테스트 모드 실행

API 키 없이 테스트하려면:

```bash
# 테스트 모드로 실행 (샘플 데이터 사용)
./gradlew bootRun --args='--spring.profiles.active=test'
```

## 📁 파일 구조

```
quantum-trading-app/
├── .env.example          # 환경변수 템플릿
├── .env                  # 실제 환경변수 (git ignore됨)
├── .gitignore           # 시크릿 파일 제외 설정
├── SECRETS-SETUP.md     # 이 가이드
└── src/main/resources/
    ├── application.yml         # 기본 설정 (공개)
    ├── application-local.yml   # 로컬 설정 (git ignore됨)
    └── application-test.yml    # 테스트 설정
```

## ⚡ 빠른 시작 (개발용)

DINO 테스트만 확인하고 싶다면:

1. **테스트 모드로 실행** (API 키 불필요)
```bash
./gradlew bootRun --args='--spring.profiles.active=test'
```

2. **브라우저에서 접속**
```
http://localhost:8080/dino
```

3. **삼성전자(005930) 입력하여 테스트**

## 🔧 문제 해결

### "API 키가 없습니다" 오류
- `.env` 파일이나 `application-local.yml`에 실제 값을 입력했는지 확인
- 환경변수가 제대로 로드되는지 확인: `echo $KIS_MY_APP`

### "계좌번호 형식 오류" 오류
- 계좌번호는 8자리 숫자로 입력
- 하이픈(-) 없이 입력

### Java 25 빌드 오류
- 문서에 명시된 대로 여러 번 시도: `./gradlew build`
- Gradle daemon 재시작: `./gradlew --stop && ./gradlew build`

## 📞 도움

더 자세한 내용은 프로젝트 CLAUDE.md 파일을 참고하세요.