package com.quantum.api.kiwoom.controller;

import io.swagger.v3.oas.annotations.Hidden;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

/**
 * 루트 도메인에서 Swagger UI로 리다이렉트하는 컨트롤러
 */
@Controller
@Slf4j
@Hidden // Swagger 문서에서 제외
public class SwaggerRedirectController {
    
    /**
     * 루트 경로 접속 시 Swagger UI로 리다이렉트
     */
    @GetMapping("/")
    public String redirectToSwagger() {
        log.debug("Root path accessed, redirecting to Swagger UI");
        return "redirect:/swagger-ui.html";
    }
}