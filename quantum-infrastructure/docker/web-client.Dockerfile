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
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# package.json과 package-lock.json 복사
COPY package*.json ./

# 의존성 설치 (빌드에 필요한 devDependencies 포함)
RUN npm ci && npm cache clean --force

# 소스 코드 복사
COPY . .

# Next.js 빌드
RUN npm run build

# 프로덕션용 의존성만 재설치 (빌드 완료 후 용량 최적화)
RUN npm prune --production

# 헬스체크 스크립트 생성
RUN echo '#!/bin/sh\ncurl -f http://localhost:10301/api/health || exit 1' > /app/healthcheck.sh && \
    chmod +x /app/healthcheck.sh

# 애플리케이션 실행
CMD ["npm", "start"]