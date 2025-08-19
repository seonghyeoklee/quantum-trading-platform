plugins {
    id("java-library")
    id("io.spring.dependency-management")
}

// Spring Cloud BOM 의존성 관리
dependencyManagement {
    imports {
        mavenBom("org.springframework.cloud:spring-cloud-dependencies:2023.0.6")
    }
}

dependencies {
    // Remove circular dependency

    // Spring Boot Web for API clients
    implementation(libs.spring.boot.starter.web)

    // External API clients (Feign + WebClient)
    implementation(libs.bundles.reactive)
    implementation(libs.bundles.http.clients)

    // JSON Processing
    implementation(libs.jackson.databind)
    implementation(libs.jackson.datatype.jsr310)

    // Monitoring & Observability
    implementation(libs.bundles.monitoring)

    // Utilities
    compileOnly(libs.lombok)
    annotationProcessor(libs.lombok)

    // Testing
    testImplementation(libs.spring.boot.starter.test)
    testImplementation(libs.reactor.test)
    testCompileOnly(libs.lombok)
    testAnnotationProcessor(libs.lombok)
}
