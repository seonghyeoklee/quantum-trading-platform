plugins {
    id("org.springframework.boot")
    id("io.spring.dependency-management")
    kotlin("jvm") version "1.9.10" apply false
}

dependencies {
    // Platform Core Dependencies
    implementation(project(":quantum-platform-core:quantum-shared-kernel"))
    implementation(project(":quantum-platform-core:quantum-trading-command"))
    implementation(project(":quantum-platform-core:quantum-trading-query"))

    // Spring Boot Web
    implementation("org.springframework.boot:spring-boot-starter-web")
    implementation("org.springframework.boot:spring-boot-starter-validation")
    implementation("org.springframework.boot:spring-boot-starter-actuator")

    // Spring Data JPA (Query Side 접근용)
    implementation("org.springframework.boot:spring-boot-starter-data-jpa")
    runtimeOnly("org.postgresql:postgresql")

    // H2 Database (테스트 및 개발용)
    runtimeOnly("com.h2database:h2")

    // Redis (실시간 데이터 캐싱)
    implementation("org.springframework.boot:spring-boot-starter-data-redis")

    // Apache Kafka (실시간 이벤트 스트리밍)
    implementation("org.springframework.kafka:spring-kafka")
    implementation("org.apache.kafka:kafka-streams")

    // WebSocket Support (실시간 데이터 브로드캐스트)
    implementation("org.springframework.boot:spring-boot-starter-websocket")

    // InfluxDB (시계열 데이터베이스)
    implementation("com.influxdb:influxdb-client-java:6.10.0")

    // Spring Security & JWT
    implementation("org.springframework.boot:spring-boot-starter-security")
    implementation("org.springframework.security:spring-security-web")
    implementation("org.springframework.security:spring-security-config")
    implementation("io.jsonwebtoken:jjwt-api:0.12.3")
    runtimeOnly("io.jsonwebtoken:jjwt-impl:0.12.3")
    runtimeOnly("io.jsonwebtoken:jjwt-jackson:0.12.3")

    // QR Code & TOTP for 2FA
    implementation("com.google.zxing:core:3.5.3")
    implementation("com.google.zxing:javase:3.5.3")
    implementation("com.eatthepath:java-otp:0.4.0")
    implementation("commons-codec:commons-codec:1.16.0")

    // JSON Processing
    implementation("com.fasterxml.jackson.core:jackson-databind")
    implementation("com.fasterxml.jackson.datatype:jackson-datatype-jsr310")

    // Axon Framework (Query만 사용)
    implementation("org.axonframework:axon-spring-boot-starter:4.9.1")
    implementation("org.axonframework:axon-server-connector:4.9.1")

    // API Documentation
    implementation("org.springdoc:springdoc-openapi-starter-webmvc-ui:2.2.0")

    // Metrics & Monitoring (Prometheus)
    implementation("io.micrometer:micrometer-registry-prometheus")
    
    // Distributed Tracing (OpenTelemetry -> Tempo)
    implementation("io.micrometer:micrometer-tracing-bridge-otel")
    implementation("io.opentelemetry:opentelemetry-exporter-otlp")
    
    // Structured Logging (JSON)
    implementation("net.logstash.logback:logstash-logback-encoder:7.4")

    // Development
    developmentOnly("org.springframework.boot:spring-boot-devtools")

    // Testing
    testImplementation("org.springframework.boot:spring-boot-starter-test")
    testImplementation("org.springframework:spring-test")
    testImplementation("org.testcontainers:junit-jupiter")
    testImplementation("org.testcontainers:postgresql")
}
