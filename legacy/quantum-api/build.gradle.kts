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
    implementation(projects.quantumBatch)

    // Spring Boot Web Bundle
    implementation(libs.bundles.spring.web)

    // Spring Security Bundle
    implementation(libs.bundles.spring.security)

    // API Documentation
    implementation(libs.springdoc)

    // Monitoring & Observability
    implementation(libs.bundles.monitoring)

    // HTTP Clients (Feign)
    implementation(libs.bundles.http.clients)

    // Utilities
    compileOnly(libs.lombok)
    annotationProcessor(libs.lombok)
    
    // Object Mapping
    implementation(libs.mapstruct)
    annotationProcessor(libs.mapstruct.processor)

    // Test
    testImplementation(libs.spring.boot.starter.test)
    testImplementation(libs.spring.security.test)
    testCompileOnly(libs.lombok)
    testAnnotationProcessor(libs.lombok)
}
