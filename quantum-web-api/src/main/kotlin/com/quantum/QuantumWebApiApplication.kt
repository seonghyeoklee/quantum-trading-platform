package com.quantum

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication

@SpringBootApplication
class QuantumWebApiApplication

fun main(args: Array<String>) {
    runApplication<QuantumWebApiApplication>(*args)
}
