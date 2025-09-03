# Quantum Trading Platform - Web Client

이 프로젝트는 [Next.js](https://nextjs.org) 기반의 Quantum Trading Platform 프론트엔드 애플리케이션입니다.

## 🏗️ 아키텍처 개요

### 서버 중심 KIS 인증 아키텍처
- **Frontend (3000)**: Next.js 15 + React 19
- **Backend (8080)**: Spring Boot Kotlin API 
- **KIS Adapter (8000)**: FastAPI Python adapter
- **인증 방식**: JWT (클라이언트) + 서버 관리 KIS 토큰

### 주요 특징
- ✅ **서버 중심 KIS 토큰 관리**: 클라이언트에서 KIS 토큰을 직접 관리하지 않음
- ✅ **단순화된 API 호출**: X-KIS-Token 헤더나 trading_mode 파라미터 불필요
- ✅ **보안 강화**: 모든 KIS 인증 정보는 서버에서만 처리
- ✅ **실시간 차트**: lightweight-charts 기반 TradingView 스타일 차트

## 🚀 시작하기

### 개발 서버 실행

```bash
npm run dev
# 또는
yarn dev
# 또는
pnpm dev
# 또는
bun dev
```

[http://localhost:3000](http://localhost:3000)에서 확인할 수 있습니다.

### 사용자 정의 호스트 (옵션)
```bash
npm run dev        # quantum-trading.com에서 실행 (설정됨)
npm run dev:local  # localhost:3000에서 실행
```

## 📁 프로젝트 구조

```
src/
├── app/                    # Next.js 13+ App Router
├── components/             # React 컴포넌트
│   ├── ui/                # shadcn/ui 기본 컴포넌트
│   ├── charts/            # 차트 관련 컴포넌트
│   └── kis/               # KIS 관련 컴포넌트 (단순화됨)
├── contexts/              # React Context (서버 중심으로 단순화)
├── lib/                   # 유틸리티 및 서비스
│   └── services/          # API 서비스 (서버 중심 호출)
└── hooks/                 # 커스텀 React Hook
```

## 🔧 주요 기능

### 인증 시스템
- **JWT 기반 사용자 인증** (accessToken/refreshToken)
- **KIS 계정 설정**: 서버에서 관리되는 API 키
- **자동 로그인 유지** 및 토큰 갱신

### 차트 시스템
- **TradingChart 컴포넌트**: lightweight-charts v4.1.3 기반
- **한국식 차트 색상**: 빨강(상승), 파랑(하락)
- **이동평균선**: 5일(분홍), 20일(노랑), 60일(하양)
- **실시간 업데이트**: WebSocket 연동 준비

### API 통신
```typescript
// 단순화된 API 호출 (서버가 모든 인증 처리)
const response = await fetch(`http://localhost:8000/domestic/price/005930`);

// JWT 인증이 필요한 백엔드 API
const response = await apiClient.get('/api/v1/auth/me', true);
```

## 🛠️ 개발 도구

- **UI 라이브러리**: Radix UI + Tailwind CSS + shadcn/ui
- **차트**: lightweight-charts
- **상태 관리**: React Context (단순화됨)
- **타입스크립트**: 완전한 타입 안전성
- **린팅**: ESLint + Prettier

## 📚 개발 가이드

### KIS API 호출
모든 KIS API 호출은 서버에서 인증을 처리합니다:

```typescript
// ❌ 이전 방식 (더 이상 사용 안 함)
fetch(url, { 
  headers: { 'X-KIS-Token': token } 
});

// ✅ 현재 방식 (서버 중심 관리)
fetch(`http://localhost:8000/domestic/price/005930`);
```

### 환경 변수
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8080
NEXT_PUBLIC_KIS_API_URL=http://adapter.quantum-trading.com:8000
```

## 🔐 보안

- **KIS 토큰**: 서버에서만 관리, 클라이언트 노출 없음
- **JWT 토큰**: httpOnly 쿠키 또는 secure storage 사용 권장
- **CORS 설정**: 개발 환경에서만 허용된 오리진
- **API 키 암호화**: 서버측에서 암호화 저장

## 📖 자세한 정보

- [Next.js 문서](https://nextjs.org/docs) - Next.js 기능과 API 학습
- [React 문서](https://react.dev) - React 사용법
- [Tailwind CSS](https://tailwindcss.com) - 유틸리티 CSS 프레임워크
- [shadcn/ui](https://ui.shadcn.com) - 재사용 가능한 컴포넌트

## 🚢 배포

Vercel Platform을 사용한 배포가 가장 간단합니다:

[Vercel 배포 문서](https://nextjs.org/docs/app/building-your-application/deploying)에서 자세한 내용을 확인하세요.

---

**참고**: 이 프로젝트는 서버 중심 KIS 토큰 관리 아키텍처를 사용하여 보안을 강화하고 클라이언트 코드를 단순화했습니다.