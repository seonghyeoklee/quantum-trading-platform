package com.quantum.web.controller

import org.springframework.stereotype.Controller
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.servlet.ModelAndView

/**
 * 루트 경로 컨트롤러
 * 
 * localhost:8080/ 접근 시 Swagger UI로 리다이렉트
 */
@Controller
class RootController {
    
    /**
     * 루트 경로 접근 시 Swagger UI로 리다이렉트
     */
    @GetMapping("/")
    fun redirectToSwagger(): ModelAndView {
        return ModelAndView("redirect:/docs")
    }
}