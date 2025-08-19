package com.quantum.batch.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

/** 루트 경로 컨트롤러 - Swagger UI로 리다이렉트 */
@Controller
public class RootController {

    /** 루트 경로 접근시 Swagger UI로 리다이렉트 */
    @GetMapping("/")
    public String redirectToSwagger() {
        return "redirect:/swagger-ui.html";
    }

    /** API 루트 경로도 Swagger로 리다이렉트 */
    @GetMapping("/api")
    public String redirectApiToSwagger() {
        return "redirect:/swagger-ui.html";
    }
}
