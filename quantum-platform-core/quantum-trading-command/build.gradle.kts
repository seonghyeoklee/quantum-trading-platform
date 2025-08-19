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
    
    // No additional dependencies beyond parent
}