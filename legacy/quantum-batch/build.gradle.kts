plugins {
    id("org.springframework.boot")
    id("io.spring.dependency-management")
}

// Spring Cloud BOM 의존성 관리
dependencyManagement {
    imports {
        mavenBom("org.springframework.cloud:spring-cloud-dependencies:2023.0.6")
    }
}

dependencies {
    implementation(projects.quantumCore)
    implementation(projects.quantumAdapter)

    // Spring Boot Batch Bundle
    implementation(libs.bundles.batch.scheduling)

    // Web for batch management API
    implementation(libs.spring.boot.starter.web)

    // API Documentation
    implementation(libs.springdoc)

    // External API clients
    implementation(libs.bundles.reactive)

    // Monitoring & Observability
    implementation(libs.bundles.monitoring)

    // HTTP Clients (Feign)
    implementation(libs.bundles.http.clients)

    // Utilities
    compileOnly(libs.lombok)
    annotationProcessor(libs.lombok)

    // Testing
    testImplementation(libs.spring.boot.starter.test)
    testImplementation(libs.spring.batch.test)
    testCompileOnly(libs.lombok)
    testAnnotationProcessor(libs.lombok)
}
