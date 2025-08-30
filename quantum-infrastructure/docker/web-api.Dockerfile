# Quantum Web API (Spring Boot) Dockerfile
FROM openjdk:21-jdk-slim

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 애플리케이션 포트 노출
EXPOSE 10101

# 환경변수 기본값 설정
ENV SERVER_PORT=10101
ENV SPRING_PROFILES_ACTIVE=docker

# JAR 파일 복사를 위한 ARG 설정
ARG JAR_FILE=build/libs/*.jar

# 빌드된 JAR 파일 복사
COPY ${JAR_FILE} app.jar

# 애플리케이션 실행
ENTRYPOINT ["java", "-jar", "app.jar"]