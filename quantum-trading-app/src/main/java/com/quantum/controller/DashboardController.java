package com.quantum.controller;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

@Slf4j
@Controller
@RequiredArgsConstructor
public class DashboardController {

    @GetMapping("/")
    public String dashboard(Model model) {
        log.info("Loading dashboard page");

        // 페이지 메타데이터 설정
        model.addAttribute("title", "대시보드 - 퀀텀 트레이딩");
        model.addAttribute("breadcrumb", "대시보드");

        // 대시보드 데이터 (현재는 하드코딩, 추후 서비스에서 가져올 예정)
        model.addAttribute("kospiValue", "2,547.83");
        model.addAttribute("kospiChange", "+1.24%");
        model.addAttribute("kosdaqValue", "845.67");
        model.addAttribute("kosdaqChange", "-0.83%");
        model.addAttribute("portfolioValue", "₩15.2M");
        model.addAttribute("portfolioChange", "+2.45%");
        model.addAttribute("activeOrders", "127");
        model.addAttribute("orderChange", "+12");

        return "dashboard";
    }

    @GetMapping("/stocks")
    public String stocks(Model model) {
        log.info("Loading stocks page");

        model.addAttribute("title", "종목 관리 - 퀀텀 트레이딩");
        model.addAttribute("breadcrumb", "종목 관리");

        // TODO: 종목 페이지 구현
        return "stocks";
    }

    @GetMapping("/news")
    public String news(Model model) {
        log.info("Loading news page");

        model.addAttribute("title", "뉴스 모니터 - 퀀텀 트레이딩");
        model.addAttribute("breadcrumb", "뉴스 모니터");

        // TODO: 뉴스 페이지 구현
        return "news";
    }


    @GetMapping("/orders")
    public String orders(Model model) {
        log.info("Loading orders page");

        model.addAttribute("title", "주문 관리 - 퀀텀 트레이딩");
        model.addAttribute("breadcrumb", "주문 관리");

        // TODO: 주문 관리 페이지 구현
        return "orders";
    }

    @GetMapping("/system")
    public String system(Model model) {
        log.info("Loading system page");

        model.addAttribute("title", "시스템 상태 - 퀀텀 트레이딩");
        model.addAttribute("breadcrumb", "시스템 상태");

        // TODO: 시스템 상태 페이지 구현
        return "system";
    }

    @GetMapping("/logs")
    public String logs(Model model) {
        log.info("Loading logs page");

        model.addAttribute("title", "로그 뷰어 - 퀀텀 트레이딩");
        model.addAttribute("breadcrumb", "로그 뷰어");

        // TODO: 로그 뷰어 페이지 구현
        return "logs";
    }

    @GetMapping("/settings")
    public String settings(Model model) {
        log.info("Loading settings page");

        model.addAttribute("title", "설정 - 퀀텀 트레이딩");
        model.addAttribute("breadcrumb", "설정");

        // TODO: 설정 페이지 구현
        return "settings";
    }
}