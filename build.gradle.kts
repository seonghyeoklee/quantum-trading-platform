plugins {
    java
    `java-library`
    id("org.springframework.boot") version "3.3.2" apply false
    id("io.spring.dependency-management") version "1.1.6" apply false
    id("org.graalvm.buildtools.native") version "0.10.2" apply false
}

allprojects {
    group = "com.quantum.trading"
    version = "1.0.0"
    
    repositories {
        mavenCentral()
        maven("https://repo.spring.io/milestone")
    }
}

subprojects {
    apply(plugin = "java")
    apply(plugin = "java-library")
    apply(plugin = "org.springframework.boot")
    apply(plugin = "io.spring.dependency-management")

    java {
        toolchain {
            languageVersion = JavaLanguageVersion.of(21)
        }
    }

    configurations {
        compileOnly {
            extendsFrom(configurations.annotationProcessor.get())
        }
    }

    dependencies {
        // Spring Boot Starters
        implementation("org.springframework.boot:spring-boot-starter")
        implementation("org.springframework.boot:spring-boot-starter-validation")
        implementation("org.springframework.boot:spring-boot-starter-actuator")
        
        // Axon Framework
        implementation("org.axonframework:axon-spring-boot-starter:4.9.1")
        implementation("org.axonframework:axon-server-connector:4.9.1")
        
        // Lombok
        compileOnly("org.projectlombok:lombok")
        annotationProcessor("org.projectlombok:lombok")
        
        // Testing
        testImplementation("org.springframework.boot:spring-boot-starter-test")
        testImplementation("org.axonframework:axon-test:4.9.1")
        testImplementation("org.testcontainers:junit-jupiter")
        testImplementation("org.testcontainers:postgresql")
        
        // Development
        runtimeOnly("org.springframework.boot:spring-boot-devtools")
    }

    tasks.withType<Test> {
        useJUnitPlatform()
    }

    tasks.withType<JavaCompile> {
        options.encoding = "UTF-8"
        options.compilerArgs.addAll(listOf("-parameters", "-Xlint:unchecked"))
    }
}

// Apply to all subprojects
allprojects {
    configurations.all {
        resolutionStrategy {
            // Force versions for consistency
            force("org.springframework.cloud:spring-cloud-dependencies:2023.0.3")
            force("org.testcontainers:testcontainers-bom:1.19.8")
        }
    }
}