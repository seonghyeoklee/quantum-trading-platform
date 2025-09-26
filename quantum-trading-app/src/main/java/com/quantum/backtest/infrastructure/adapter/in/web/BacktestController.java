package com.quantum.backtest.infrastructure.adapter.in.web;

import com.quantum.backtest.application.port.in.CancelBacktestUseCase;
import com.quantum.backtest.application.port.in.GetBacktestUseCase;
import com.quantum.backtest.application.port.in.RunBacktestUseCase;
import com.quantum.backtest.application.port.out.MarketDataPort;
import com.quantum.backtest.domain.*;
import com.quantum.backtest.infrastructure.persistence.JpaStrategyExecutionLogRepository;
import com.quantum.backtest.infrastructure.persistence.StrategyExecutionLogEntity;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * 백테스팅 웹 컨트롤러
 * Inbound Adapter for Web Interface
 */
@Controller
@RequestMapping("/backtest")
public class BacktestController {

    private static final Logger log = LoggerFactory.getLogger(BacktestController.class);

    private final RunBacktestUseCase runBacktestUseCase;
    private final GetBacktestUseCase getBacktestUseCase;
    private final CancelBacktestUseCase cancelBacktestUseCase;
    private final MarketDataPort marketDataPort;
    private final JpaStrategyExecutionLogRepository strategyLogRepository;

    public BacktestController(RunBacktestUseCase runBacktestUseCase,
                            GetBacktestUseCase getBacktestUseCase,
                            CancelBacktestUseCase cancelBacktestUseCase,
                            MarketDataPort marketDataPort,
                            JpaStrategyExecutionLogRepository strategyLogRepository) {
        this.runBacktestUseCase = runBacktestUseCase;
        this.getBacktestUseCase = getBacktestUseCase;
        this.cancelBacktestUseCase = cancelBacktestUseCase;
        this.marketDataPort = marketDataPort;
        this.strategyLogRepository = strategyLogRepository;
    }

    /**
     * 백테스팅 목록 페이지
     */
    @GetMapping
    public String backtestList(@RequestParam(defaultValue = "0") int page,
                              @RequestParam(defaultValue = "10") int size,
                              Model model) {
        log.info("백테스팅 목록 조회 - 페이지: {}, 크기: {}", page, size);

        Pageable pageable = PageRequest.of(page, size);
        Page<Backtest> backtests = getBacktestUseCase.getAllBacktests(pageable);

        model.addAttribute("backtests", backtests);
        model.addAttribute("currentPage", page);
        model.addAttribute("totalPages", backtests.getTotalPages());
        model.addAttribute("title", "백테스팅 목록");

        return "backtest/list";
    }

    /**
     * 백테스팅 생성 폼
     */
    @GetMapping("/new")
    public String newBacktest(Model model) {
        log.info("🟢 GET /backtest/new - 백테스팅 생성 폼 접근");

        // 전략 타입 목록
        model.addAttribute("strategyTypes", StrategyType.values());

        // 기본값 설정
        model.addAttribute("stockCode", "005930");
        model.addAttribute("startDate", LocalDate.now().minusMonths(6).toString());
        model.addAttribute("endDate", LocalDate.now().toString());
        model.addAttribute("initialCapital", "10000000");
        model.addAttribute("strategyType", StrategyType.BUY_AND_HOLD);
        model.addAttribute("title", "백테스팅 생성");

        return "backtest/create";
    }

    /**
     * 백테스팅 실행
     */
    @PostMapping
    public String createBacktest(@RequestParam String stockCode,
                               @RequestParam String startDate,
                               @RequestParam String endDate,
                               @RequestParam BigDecimal initialCapital,
                               @RequestParam StrategyType strategyType,
                               RedirectAttributes redirectAttributes,
                               Model model) {
        log.info("🔴 POST /backtest - 백테스팅 생성 요청 - 종목: {}, 기간: {} ~ {}, 전략: {}",
                stockCode, startDate, endDate, strategyType);

        try {
            // 입력 검증
            LocalDate start = LocalDate.parse(startDate);
            LocalDate end = LocalDate.parse(endDate);

            if (start.isAfter(end)) {
                throw new IllegalArgumentException("시작일은 종료일보다 이전이어야 합니다.");
            }

            if (initialCapital.compareTo(BigDecimal.valueOf(1000000)) < 0) {
                throw new IllegalArgumentException("최소 투자금액은 100만원입니다.");
            }

            // 종목 유효성 검증
            if (!marketDataPort.isValidStock(stockCode)) {
                throw new IllegalArgumentException("유효하지 않은 종목코드입니다: " + stockCode);
            }

            String stockName = marketDataPort.getStockName(stockCode);

            // 백테스팅 설정 생성 (시장 구분 자동 감지)
            BacktestConfig config = BacktestConfig.createWithAutoDetection(
                    stockCode,
                    stockName,
                    start,
                    end,
                    initialCapital,
                    strategyType,
                    new HashMap<>() // 현재는 파라미터 없음
            );

            // 백테스팅 실행
            BacktestId backtestId = runBacktestUseCase.runBacktest(config);

            redirectAttributes.addFlashAttribute("successMessage",
                    "백테스팅이 실행되었습니다. ID: " + backtestId);

            return "redirect:/backtest/" + backtestId.value();

        } catch (Exception e) {
            log.error("백테스팅 생성 실패: {}", e.getMessage());

            model.addAttribute("errorMessage", e.getMessage());
            model.addAttribute("strategyTypes", StrategyType.values());
            model.addAttribute("stockCode", stockCode);
            model.addAttribute("startDate", startDate);
            model.addAttribute("endDate", endDate);
            model.addAttribute("initialCapital", initialCapital);
            model.addAttribute("strategyType", strategyType);
            model.addAttribute("title", "백테스팅 생성");

            return "backtest/create";
        }
    }

    /**
     * 백테스팅 상세 페이지
     */
    @GetMapping("/{id}")
    public String backtestDetail(@PathVariable String id, Model model) {
        log.info("백테스팅 상세 조회: {}", id);

        try {
            BacktestId backtestId = BacktestId.from(id);
            Optional<Backtest> backtestOpt = getBacktestUseCase.getBacktestDetail(backtestId);

            if (backtestOpt.isEmpty()) {
                model.addAttribute("errorMessage", "백테스팅을 찾을 수 없습니다: " + id);
                return "backtest/list";
            }

            Backtest backtest = backtestOpt.get();
            model.addAttribute("backtest", backtest);
            model.addAttribute("title", "백테스팅 상세");

            // 결과가 있는 경우 추가 정보
            if (backtest.getResult() != null) {
                BacktestResult result = backtest.getResult();
                model.addAttribute("profitLoss", result.getProfitLoss(backtest.getConfig().initialCapital()));
                model.addAttribute("isProfitable", result.isProfitable());
            }

            // 전략 실행 로그 조회 (올바른 백테스트 UUID 사용)
            List<StrategyExecutionLogEntity> strategyLogs =
                strategyLogRepository.findByBacktestIdOrderByTimestampAscStepSequenceAsc(backtest.getId().value());
            model.addAttribute("strategyLogs", strategyLogs);

            log.info("백테스팅 상세 조회 완료: {} (로그 {}개)", id, strategyLogs.size());

            return "backtest/detail";

        } catch (Exception e) {
            log.error("백테스팅 상세 조회 실패: {}", e.getMessage());
            model.addAttribute("errorMessage", "백테스팅 조회 중 오류가 발생했습니다: " + e.getMessage());
            return "backtest/list";
        }
    }

    /**
     * 백테스팅 취소
     */
    @PostMapping("/{id}/cancel")
    public String cancelBacktest(@PathVariable String id, RedirectAttributes redirectAttributes) {
        log.info("백테스팅 취소 요청: {}", id);

        try {
            BacktestId backtestId = BacktestId.from(id);
            cancelBacktestUseCase.cancelBacktest(backtestId);

            redirectAttributes.addFlashAttribute("successMessage", "백테스팅이 취소되었습니다.");

        } catch (Exception e) {
            log.error("백테스팅 취소 실패: {}", e.getMessage());
            redirectAttributes.addFlashAttribute("errorMessage",
                    "백테스팅 취소 중 오류가 발생했습니다: " + e.getMessage());
        }

        return "redirect:/backtest/" + id;
    }

    /**
     * 진행률 조회 (AJAX)
     */
    @GetMapping("/{id}/progress")
    @ResponseBody
    public Map<String, Object> getProgress(@PathVariable String id) {
        Map<String, Object> response = new HashMap<>();

        try {
            BacktestId backtestId = BacktestId.from(id);
            Optional<Backtest> backtestOpt = getBacktestUseCase.getBacktest(backtestId);

            if (backtestOpt.isPresent()) {
                Backtest backtest = backtestOpt.get();
                response.put("status", backtest.getStatus().name());
                response.put("progress", backtest.getProgressPercentage());
                response.put("statusDisplay", backtest.getStatus().getDisplayName());

                if (backtest.isFinished() && backtest.getResult() != null) {
                    BacktestResult result = backtest.getResult();
                    response.put("totalReturn", result.totalReturn());
                    response.put("totalTrades", result.totalTrades());
                }

                if (backtest.getErrorMessage() != null) {
                    response.put("errorMessage", backtest.getErrorMessage());
                }
            } else {
                response.put("error", "백테스팅을 찾을 수 없습니다.");
            }

        } catch (Exception e) {
            log.error("진행률 조회 실패: {}", e.getMessage());
            response.put("error", e.getMessage());
        }

        return response;
    }
}