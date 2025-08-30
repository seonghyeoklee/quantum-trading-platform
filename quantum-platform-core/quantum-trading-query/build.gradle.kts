// Disable Spring Boot plugin for library module
tasks.bootJar {
    enabled = false
}

tasks.jar {
    enabled = true
    archiveClassifier = ""
}

dependencies {
    // Platform Core Dependencies
    implementation(project(":quantum-platform-core:quantum-shared-kernel"))

    // Spring Data JPA for Query Side Persistence
    implementation("org.springframework.boot:spring-boot-starter-data-jpa")

    // PostgreSQL Driver
    runtimeOnly("org.postgresql:postgresql")

    // Jackson for JSON processing in views
    implementation("com.fasterxml.jackson.core:jackson-databind")
    implementation("com.fasterxml.jackson.datatype:jackson-datatype-jsr310")

    // Test Dependencies
    testImplementation("com.h2database:h2")
}
