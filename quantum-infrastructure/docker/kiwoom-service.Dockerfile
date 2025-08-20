# Build stage
FROM gradle:8.5-jdk21-alpine AS builder

WORKDIR /app

# Copy gradle files
COPY gradle.properties settings.gradle.kts build.gradle.kts ./
COPY gradle ./gradle

# Copy source code
COPY quantum-platform-core ./quantum-platform-core
COPY quantum-broker-integration ./quantum-broker-integration
COPY quantum-api ./quantum-api

# Build the application
RUN gradle :quantum-api:kiwoom-service:bootJar --no-daemon

# Runtime stage
FROM eclipse-temurin:21-jre-alpine

# Install curl for health checks
RUN apk add --no-cache curl

# Create user for running application
RUN addgroup -g 1000 quantum && \
    adduser -D -u 1000 -G quantum quantum

WORKDIR /app

# Copy the built jar from builder stage
COPY --from=builder /app/quantum-api/kiwoom-service/build/libs/*.jar app.jar

# Change ownership
RUN chown -R quantum:quantum /app

USER quantum

# JVM options for container environment
ENV JAVA_OPTS="-XX:MaxRAMPercentage=75.0 \
               -XX:+UseG1GC \
               -XX:+UseStringDeduplication \
               -Djava.security.egd=file:/dev/./urandom \
               -Dspring.backgroundpreinitializer.ignore=true"

# Expose ports
EXPOSE 8080 8081

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8081/actuator/health || exit 1

# Run the application
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]