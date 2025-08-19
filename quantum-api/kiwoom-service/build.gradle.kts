dependencies {
    // Spring WebFlux (Reactive Web)
    implementation("org.springframework.boot:spring-boot-starter-webflux")
    implementation("org.springframework.boot:spring-boot-starter-validation")
    implementation("org.springframework.boot:spring-boot-starter-actuator")

    // Swagger for WebFlux
    implementation("org.springdoc:springdoc-openapi-starter-webflux-ui:2.3.0")

    // Reactive Redis for caching (optional)
    implementation("org.springframework.boot:spring-boot-starter-data-redis-reactive")

    // Configuration Processing
    annotationProcessor("org.springframework.boot:spring-boot-configuration-processor")

    // Testing
    testImplementation("io.projectreactor:reactor-test")
}
