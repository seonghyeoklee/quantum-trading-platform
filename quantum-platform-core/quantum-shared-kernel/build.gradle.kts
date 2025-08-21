// Library module configuration
tasks.bootJar {
    enabled = false
}

tasks.jar {
    enabled = true
}

dependencies {
    // Bean Validation for command validation
    implementation("org.springframework.boot:spring-boot-starter-validation")
    
    // Jackson for JSON serialization/deserialization
    implementation("com.fasterxml.jackson.core:jackson-annotations")
    
    // Only basic Spring Boot and Axon Framework from parent
}