// Library module configuration
tasks.bootJar {
    enabled = false
}

tasks.jar {
    enabled = true
}

dependencies {
    // No additional dependencies - pure domain
    // Only basic Spring Boot and Axon Framework from parent
}