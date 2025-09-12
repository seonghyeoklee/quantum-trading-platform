plugins {
    kotlin("jvm") version "1.9.25"
    kotlin("plugin.spring") version "1.9.25"
    id("org.springframework.boot") version "3.3.4"
    id("io.spring.dependency-management") version "1.1.6"
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
    mavenLocal() // 로컬 Maven 저장소를 우선으로
    mavenCentral()
    // Spring AI 마일스톤 및 스냅샷 레포지토리
    maven { url = uri("https://repo.spring.io/milestone") }
    maven { url = uri("https://repo.spring.io/snapshot") }
    // JitPack repository for our Swagger LLM library
    maven { url = uri("https://jitpack.io") }
}

dependencies {
    // Spring Boot Starters
    implementation("org.springframework.boot:spring-boot-starter-web")
    implementation("org.springframework.boot:spring-boot-starter-webflux")
    implementation("org.springframework.boot:spring-boot-starter-data-jpa")
    implementation("org.springframework.boot:spring-boot-starter-security")
    implementation("org.springframework.boot:spring-boot-starter-validation")
    implementation("org.springframework.boot:spring-boot-starter-cache")
    
    // Spring AI - Spring Boot 3.3과 호환되는 안정 버전
    implementation("org.springframework.ai:spring-ai-openai:1.0.0-M2")
    implementation("org.springframework.ai:spring-ai-spring-boot-autoconfigure:1.0.0-M2")
    
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
    
    // OpenAPI Documentation - Spring Boot 3.3과 확실히 호환되는 검증된 버전
    implementation("org.springdoc:springdoc-openapi-starter-webmvc-ui:2.2.0")
    
    // Swagger LLM Spring Boot Starter - LLM 친화적 API 문서 자동 생성 (GitHub JitPack)
    implementation("com.github.seonghyeoklee:swagger-llm-spring-boot-starter:v1.0.3")
    
    // macOS DNS 네이티브 리졸버 (WebClient 성능 최적화)
    runtimeOnly("io.netty:netty-resolver-dns-native-macos")
    
    // Spring Boot Actuator (헬스체크만 사용)
    implementation("org.springframework.boot:spring-boot-starter-actuator")
    
    // Micrometer Prometheus (메트릭 수집)
    implementation("io.micrometer:micrometer-registry-prometheus")
    
    // JSON 로깅 - Logstash Encoder (Grafana 연동용)
    implementation("net.logstash.logback:logstash-logback-encoder:7.4")
    
    // 개발 필수 도구만 활성화
    implementation("org.zalando:logbook-spring-boot-starter:3.5.0")  // HTTP 로깅 (개발용)
    implementation("com.github.gavlyukovskiy:p6spy-spring-boot-starter:1.9.0")  // SQL 로깅 (개발용)
    
    // Testing
    testImplementation("org.springframework.boot:spring-boot-starter-test")
    testImplementation("org.springframework.security:spring-security-test")
    testImplementation("org.jetbrains.kotlin:kotlin-test-junit5")
    testImplementation("com.tngtech.archunit:archunit-junit5:1.2.1")
    testImplementation("com.tngtech.archunit:archunit:1.2.1")
    testImplementation("io.mockk:mockk:1.13.8")
    testImplementation("org.assertj:assertj-core:3.24.2")
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
