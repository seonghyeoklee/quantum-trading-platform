# Multi-stage build for quantum-batch
FROM openjdk:21-slim as builder

WORKDIR /app
COPY gradlew .
COPY gradle gradle
COPY build.gradle.kts .
COPY settings.gradle.kts .
COPY quantum-core quantum-core
COPY quantum-adapter quantum-adapter
COPY quantum-batch quantum-batch

# Gradle 캐시 최적화
RUN chmod +x gradlew
RUN ./gradlew :quantum-core:jar :quantum-adapter:jar :quantum-batch:bootJar -x test --no-daemon

# Runtime stage
FROM openjdk:21-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /app/quantum-batch/build/libs/*.jar app.jar

EXPOSE 8090

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8090/actuator/health || exit 1

ENTRYPOINT ["java", "-jar", "app.jar"]
