plugins {
    kotlin("jvm") version "1.9.25"
    kotlin("plugin.spring") version "1.9.25"
    id("org.springframework.boot") version "3.5.5"
    id("io.spring.dependency-management") version "1.1.7"
}

group = "com.quantum"
version = "0.0.1-SNAPSHOT"
description = "quantum-web-api"

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(21)
    }
}

repositories {
    mavenCentral()
}

dependencies {
    // Spring Boot Starters
    implementation("org.springframework.boot:spring-boot-starter-web")
    implementation("org.springframework.boot:spring-boot-starter-webflux") // WebClient for KIS API
    implementation("org.springframework.boot:spring-boot-starter-data-jpa")
    implementation("org.springframework.boot:spring-boot-starter-security")
    implementation("org.springframework.boot:spring-boot-starter-validation")
    implementation("org.springframework.boot:spring-boot-starter-cache")
    
    // Kotlin Support
    implementation("com.fasterxml.jackson.module:jackson-module-kotlin")
    implementation("org.jetbrains.kotlin:kotlin-reflect")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core") // Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-reactor") // Reactor integration
    
    // JWT
    implementation("io.jsonwebtoken:jjwt-api:0.11.5")
    runtimeOnly("io.jsonwebtoken:jjwt-impl:0.11.5")
    runtimeOnly("io.jsonwebtoken:jjwt-jackson:0.11.5")
    
    // Database
    implementation("org.postgresql:postgresql")
    runtimeOnly("com.h2database:h2") // 개발용
    
    // OpenAPI Documentation
    implementation("org.springdoc:springdoc-openapi-starter-webmvc-ui:2.2.0")
    
    // macOS DNS 네이티브 리졸버 (WebClient 성능 최적화)
    runtimeOnly("io.netty:netty-resolver-dns-native-macos")
    
    // Spring Boot Actuator (모니터링/헬스체크)
    implementation("org.springframework.boot:spring-boot-starter-actuator")
    
    // Micrometer Prometheus (메트릭 수집)
    implementation("io.micrometer:micrometer-registry-prometheus")
    
    // HTTP 로깅 - Logbook
    implementation("org.zalando:logbook-spring-boot-starter:3.5.0")
    
    // SQL 로깅 - p6spy
    implementation("com.github.gavlyukovskiy:p6spy-spring-boot-starter:1.9.0")
    
    // JSON 로깅 - Logstash Encoder (Grafana 연동용)
    implementation("net.logstash.logback:logstash-logback-encoder:7.4")
    
    // Testing
    testImplementation("org.springframework.boot:spring-boot-starter-test")
    testImplementation("org.springframework.security:spring-security-test")
    testImplementation("org.jetbrains.kotlin:kotlin-test-junit5")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

kotlin {
    compilerOptions {
        freeCompilerArgs.addAll("-Xjsr305=strict")
    }
}

tasks.withType<Test> {
    useJUnitPlatform()
}
