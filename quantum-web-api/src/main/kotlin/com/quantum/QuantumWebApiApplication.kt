package com.quantum

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication

@SpringBootApplication(
    exclude = [
        org.springframework.cloud.function.context.config.ContextFunctionCatalogAutoConfiguration::class
    ]
)
class QuantumWebApiApplication

fun main(args: Array<String>) {
    runApplication<QuantumWebApiApplication>(*args)
}
