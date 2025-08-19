plugins {
    `java-library`
}

dependencies {
    // Core domain dependencies
    api(libs.spring.context)
    api(libs.jackson.databind)
    api(libs.jackson.datatype.jsr310)
    api(libs.jakarta.validation)

    // JPA for infrastructure layer
    api(libs.spring.boot.starter.data.jpa)

    // QueryDSL for infrastructure layer
    implementation(libs.querydsl.jpa)
    annotationProcessor(libs.querydsl.apt)


    // Utilities
    compileOnly(libs.lombok)
    annotationProcessor(libs.lombok)

    // Database drivers
    runtimeOnly(libs.bundles.database.drivers)

    // Testing
    testImplementation(libs.spring.boot.starter.test)
    testImplementation(libs.testcontainers.postgresql)
    testCompileOnly(libs.lombok)
    testAnnotationProcessor(libs.lombok)
}
