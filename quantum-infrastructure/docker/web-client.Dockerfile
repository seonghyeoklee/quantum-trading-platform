# Quantum Web Client (Next.js) Dockerfile
FROM node:18-alpine

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apk add --no-cache \
    curl \
    libc6-compat

# 작업 디렉토리 설정
WORKDIR /app

# 포트 노출
EXPOSE 10301

# 환경변수 기본값 설정
ENV PORT=10301
ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED=1

# package.json과 package-lock.json 복사
COPY package*.json ./

# 의존성 설치 (개발 의존성 포함)
RUN npm ci && npm cache clean --force

# 소스 코드 복사
COPY . .

# 애플리케이션 실행 (개발 모드)
CMD ["npm", "run", "dev"]