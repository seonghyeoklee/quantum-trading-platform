package com.quantum.web.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 종목 분석 서비스
 *
 * 자동매매를 위한 종목 분석 및 전략 적합성 평가 서비스
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class TradingAnalysisService {

    private final ChartDataService chartDataService;

    /**
     * 종목 분석
     *
     * @param symbol 종목 코드
     * @return 분석 결과
     */
    public Map<String, Object> analyzeStock(String symbol) {
        log.info("Analyzing stock: {}", symbol);

        // 1. 종목 코드 유효성 검증
        validateSymbol(symbol);

        // 2. 현재가 및 기본 정보 조회 (Mock 데이터)
        Map<String, Object> basicInfo = getBasicStockInfo(symbol);

        // 3. 기술적 지표 계산
        Map<String, Object> technicalIndicators = calculateTechnicalIndicators(symbol);

        // 4. 시장 강도 분석
        Map<String, Object> marketStrength = analyzeMarketStrength(symbol);

        // 5. 변동성 분석
        Map<String, Object> volatilityAnalysis = analyzeVolatility(symbol);

        // 6. 종합 분석 결과 생성
        Map<String, Object> analysis = new HashMap<>();
        analysis.put("symbol", symbol);
        analysis.put("timestamp", LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME));
        analysis.put("basic_info", basicInfo);
        analysis.put("technical_indicators", technicalIndicators);
        analysis.put("market_strength", marketStrength);
        analysis.put("volatility", volatilityAnalysis);
        analysis.put("overall_score", calculateOverallScore(technicalIndicators, marketStrength, volatilityAnalysis));

        log.info("Stock analysis completed for: {}", symbol);
        return analysis;
    }

    /**
     * 전략 적합성 분석
     *
     * @param symbol 종목 코드
     * @param strategyName 전략명
     * @return 적합성 분석 결과
     */
    public Map<String, Object> analyzeStrategyFit(String symbol, String strategyName) {
        log.info("Analyzing strategy fit - symbol: {}, strategy: {}", symbol, strategyName);

        // 1. 유효성 검증
        validateSymbol(symbol);
        validateStrategyName(strategyName);

        // 2. 종목 기본 분석
        Map<String, Object> stockAnalysis = analyzeStock(symbol);

        // 3. 전략별 적합성 점수 계산
        Map<String, Object> strategyScore = calculateStrategyScore(stockAnalysis, strategyName);

        // 4. 추천 설정값 계산
        Map<String, Object> recommendedSettings = getRecommendedSettings(stockAnalysis, strategyName);

        // 5. 리스크 평가
        Map<String, Object> riskAssessment = assessRisk(stockAnalysis, strategyName);

        // 6. 결과 조합
        Map<String, Object> result = new HashMap<>();
        result.put("symbol", symbol);
        result.put("strategy_name", strategyName);
        result.put("timestamp", LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME));
        result.put("fit_score", strategyScore);
        result.put("recommended_settings", recommendedSettings);
        result.put("risk_assessment", riskAssessment);
        result.put("stock_analysis", stockAnalysis);

        log.info("Strategy fit analysis completed - symbol: {}, strategy: {}, score: {}", 
                symbol, strategyName, strategyScore.get("total_score"));
        
        return result;
    }

    /**
     * 시장 전체 분석
     *
     * @return 시장 분석 결과
     */
    public Map<String, Object> analyzeMarket() {
        log.info("Analyzing overall market conditions");

        Map<String, Object> analysis = new HashMap<>();

        // 1. 주요 지수 분석 (Mock 데이터)
        analysis.put("kospi", generateIndexAnalysis("KOSPI", 2500 + (int)(Math.random() * 200) - 100));
        analysis.put("kosdaq", generateIndexAnalysis("KOSDAQ", 800 + (int)(Math.random() * 100) - 50));

        // 2. 시장 심리 지표
        Map<String, Object> sentiment = new HashMap<>();
        sentiment.put("fear_greed_index", 45 + (int)(Math.random() * 40)); // 0-100
        sentiment.put("volatility_index", 15 + (int)(Math.random() * 20)); // VIX 스타일
        sentiment.put("market_breadth", 0.6 + Math.random() * 0.4); // 상승종목 비율
        analysis.put("market_sentiment", sentiment);

        // 3. 섹터 분석
        analysis.put("sector_performance", generateSectorPerformance());

        // 4. 자동매매 적합성 점수
        analysis.put("auto_trading_score", calculateMarketTradingScore(sentiment));

        // 5. 추천 전략
        analysis.put("recommended_strategies", getRecommendedStrategies(analysis));

        analysis.put("timestamp", LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME));
        analysis.put("market_status", determineMarketStatus(sentiment));

        log.info("Market analysis completed");
        return analysis;
    }

    /**
     * 배치 종목 분석
     *
     * @param symbols 종목 코드 목록
     * @param strategyName 전략명
     * @return 배치 분석 결과
     */
    public Map<String, Object> analyzeBatchStocks(List<String> symbols, String strategyName) {
        log.info("Batch analyzing {} stocks for strategy: {}", symbols.size(), strategyName);

        if (symbols == null || symbols.isEmpty()) {
            throw new IllegalArgumentException("종목 목록이 비어있습니다");
        }

        if (symbols.size() > 50) {
            throw new IllegalArgumentException("한번에 최대 50개 종목까지 분석 가능합니다");
        }

        List<Map<String, Object>> results = symbols.parallelStream()
                .map(symbol -> {
                    try {
                        Map<String, Object> analysis = analyzeStrategyFit(symbol, strategyName);
                        Map<String, Object> fitScore = (Map<String, Object>) analysis.get("fit_score");
                        
                        Map<String, Object> summary = new HashMap<>();
                        summary.put("symbol", symbol);
                        summary.put("score", fitScore.get("total_score"));
                        summary.put("recommendation", fitScore.get("recommendation"));
                        summary.put("risk_level", ((Map<String, Object>) analysis.get("risk_assessment")).get("level"));
                        
                        return summary;
                    } catch (Exception e) {
                        log.warn("Failed to analyze symbol: {}", symbol, e);
                        Map<String, Object> errorResult = new HashMap<>();
                        errorResult.put("symbol", symbol);
                        errorResult.put("error", e.getMessage());
                        return errorResult;
                    }
                })
                .collect(Collectors.toList());

        // 점수순으로 정렬
        List<Map<String, Object>> ranked = results.stream()
                .filter(result -> result.containsKey("score"))
                .sorted((a, b) -> {
                    Integer scoreA = (Integer) a.get("score");
                    Integer scoreB = (Integer) b.get("score");
                    return scoreB.compareTo(scoreA);
                })
                .collect(Collectors.toList());

        Map<String, Object> batchResult = new HashMap<>();
        batchResult.put("strategy_name", strategyName);
        batchResult.put("total_analyzed", symbols.size());
        batchResult.put("successful_analysis", ranked.size());
        batchResult.put("failed_analysis", results.size() - ranked.size());
        batchResult.put("ranked_results", ranked);
        batchResult.put("top_picks", ranked.stream().limit(5).collect(Collectors.toList()));
        batchResult.put("timestamp", LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME));

        log.info("Batch analysis completed - analyzed: {}, successful: {}", 
                symbols.size(), ranked.size());
        
        return batchResult;
    }

    /**
     * 실시간 시장 상태
     *
     * @return 실시간 시장 상태
     */
    public Map<String, Object> getRealtimeMarketStatus() {
        Map<String, Object> status = new HashMap<>();
        
        // 실시간 지수 정보 (Mock)
        status.put("kospi", Map.of(
            "value", 2500 + (int)(Math.random() * 100) - 50,
            "change", -5 + (int)(Math.random() * 10),
            "change_percent", -0.5 + Math.random()
        ));
        
        status.put("market_open", isMarketOpen());
        status.put("active_traders", 15000 + (int)(Math.random() * 5000));
        status.put("volume_today", "500억원");
        status.put("timestamp", LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME));
        
        return status;
    }

    /**
     * 백테스팅 실행
     *
     * @param symbol 종목 코드
     * @param strategyName 전략명
     * @param startDate 시작일
     * @param endDate 종료일
     * @param initialCapital 초기 자본금
     * @return 백테스팅 결과
     */
    public Map<String, Object> runBacktest(String symbol, String strategyName, 
                                          String startDate, String endDate, Long initialCapital) {
        log.info("Running backtest - symbol: {}, strategy: {}, period: {} to {}", 
                symbol, strategyName, startDate, endDate);

        // Mock 백테스팅 결과 생성
        Map<String, Object> result = new HashMap<>();
        
        // 성과 지표
        double totalReturn = -10 + Math.random() * 30; // -10% ~ +20%
        int totalTrades = 50 + (int)(Math.random() * 100);
        double winRate = 0.4 + Math.random() * 0.4; // 40% ~ 80%
        
        Map<String, Object> performance = new HashMap<>();
        performance.put("total_return", Math.round(totalReturn * 100) / 100.0);
        performance.put("annual_return", Math.round((totalReturn / 2) * 100) / 100.0);
        performance.put("max_drawdown", Math.round((5 + Math.random() * 15) * 100) / 100.0);
        performance.put("sharpe_ratio", Math.round((0.5 + Math.random() * 1.5) * 100) / 100.0);
        performance.put("total_trades", totalTrades);
        performance.put("win_rate", Math.round(winRate * 10000) / 100.0);
        performance.put("profit_factor", Math.round((1.0 + Math.random() * 1.0) * 100) / 100.0);
        
        result.put("symbol", symbol);
        result.put("strategy_name", strategyName);
        result.put("period", startDate + " ~ " + endDate);
        result.put("initial_capital", initialCapital);
        result.put("final_capital", Math.round(initialCapital * (1 + totalReturn / 100)));
        result.put("performance", performance);
        result.put("timestamp", LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME));
        
        return result;
    }

    // Private helper methods

    private void validateSymbol(String symbol) {
        if (symbol == null || !symbol.matches("^[A-Z0-9]{6}$")) {
            throw new IllegalArgumentException("유효하지 않은 종목 코드입니다: " + symbol);
        }
    }

    private void validateStrategyName(String strategyName) {
        List<String> validStrategies = Arrays.asList(
            "moving_average_crossover", "rsi_reversal", "bollinger_bands",
            "macd_signal", "momentum_breakout", "mean_reversion"
        );
        
        if (!validStrategies.contains(strategyName)) {
            throw new IllegalArgumentException("지원하지 않는 전략입니다: " + strategyName);
        }
    }

    private Map<String, Object> getBasicStockInfo(String symbol) {
        Map<String, Object> info = new HashMap<>();
        info.put("symbol", symbol);
        info.put("name", getStockName(symbol));
        info.put("current_price", 50000 + (int)(Math.random() * 50000));
        info.put("open", 50000 + (int)(Math.random() * 50000));
        info.put("high", 55000 + (int)(Math.random() * 50000));
        info.put("low", 45000 + (int)(Math.random() * 50000));
        info.put("volume", 1000000 + (int)(Math.random() * 5000000));
        info.put("market_cap", "50조원");
        return info;
    }

    private String getStockName(String symbol) {
        return switch (symbol) {
            case "005930" -> "삼성전자";
            case "000660" -> "SK하이닉스";
            case "035420" -> "NAVER";
            case "005380" -> "현대차";
            default -> "테스트종목";
        };
    }

    private Map<String, Object> calculateTechnicalIndicators(String symbol) {
        Map<String, Object> indicators = new HashMap<>();
        
        // Mock 기술적 지표 데이터
        indicators.put("rsi", 30 + (int)(Math.random() * 40)); // 30-70
        indicators.put("macd", Map.of(
            "macd", Math.round((Math.random() * 2000 - 1000) * 100) / 100.0,
            "signal", Math.round((Math.random() * 2000 - 1000) * 100) / 100.0,
            "histogram", Math.round((Math.random() * 1000 - 500) * 100) / 100.0
        ));
        indicators.put("bollinger_bands", Map.of(
            "upper", 55000 + (int)(Math.random() * 5000),
            "middle", 50000 + (int)(Math.random() * 5000),
            "lower", 45000 + (int)(Math.random() * 5000)
        ));
        indicators.put("moving_averages", Map.of(
            "ma5", 50000 + (int)(Math.random() * 5000),
            "ma20", 49000 + (int)(Math.random() * 5000),
            "ma60", 48000 + (int)(Math.random() * 5000)
        ));
        indicators.put("stochastic", Map.of(
            "k", 20 + (int)(Math.random() * 60),
            "d", 25 + (int)(Math.random() * 50)
        ));
        
        return indicators;
    }

    private Map<String, Object> analyzeMarketStrength(String symbol) {
        Map<String, Object> strength = new HashMap<>();
        strength.put("trend_strength", 3 + (int)(Math.random() * 5)); // 1-7
        strength.put("momentum", -3 + (int)(Math.random() * 7)); // -3 to +3
        strength.put("support_resistance", Map.of(
            "support", 45000 + (int)(Math.random() * 5000),
            "resistance", 55000 + (int)(Math.random() * 5000)
        ));
        return strength;
    }

    private Map<String, Object> analyzeVolatility(String symbol) {
        Map<String, Object> volatility = new HashMap<>();
        volatility.put("daily_volatility", Math.round((2 + Math.random() * 8) * 100) / 100.0); // 2-10%
        volatility.put("volatility_rank", 1 + (int)(Math.random() * 10)); // 1-10
        volatility.put("average_true_range", Math.round((1000 + Math.random() * 3000) * 100) / 100.0);
        return volatility;
    }

    private int calculateOverallScore(Map<String, Object> technical, Map<String, Object> strength, Map<String, Object> volatility) {
        // 간단한 종합 점수 계산 로직
        int rsi = (Integer) technical.get("rsi");
        int trendStrength = (Integer) strength.get("trend_strength");
        double dailyVol = (Double) volatility.get("daily_volatility");
        
        int score = 50; // 기본 점수
        
        // RSI 기반 조정
        if (rsi > 30 && rsi < 70) score += 10;
        
        // 추세 강도 기반 조정
        score += trendStrength * 2;
        
        // 변동성 기반 조정 (적당한 변동성이 좋음)
        if (dailyVol > 3 && dailyVol < 8) score += 10;
        
        return Math.max(0, Math.min(100, score));
    }

    private Map<String, Object> calculateStrategyScore(Map<String, Object> stockAnalysis, String strategyName) {
        Map<String, Object> score = new HashMap<>();
        
        int totalScore = switch (strategyName) {
            case "moving_average_crossover" -> 70 + (int)(Math.random() * 25);
            case "rsi_reversal" -> 65 + (int)(Math.random() * 30);
            case "bollinger_bands" -> 60 + (int)(Math.random() * 35);
            default -> 50 + (int)(Math.random() * 40);
        };
        
        score.put("total_score", totalScore);
        score.put("recommendation", getRecommendation(totalScore));
        score.put("confidence", (totalScore / 100.0) > 0.7 ? "high" : "medium");
        
        return score;
    }

    private String getRecommendation(int score) {
        if (score >= 80) return "strong_buy";
        if (score >= 70) return "buy";
        if (score >= 60) return "hold";
        if (score >= 50) return "weak_hold";
        return "avoid";
    }

    private Map<String, Object> getRecommendedSettings(Map<String, Object> stockAnalysis, String strategyName) {
        Map<String, Object> settings = new HashMap<>();
        
        // 변동성에 따른 추천 설정
        Map<String, Object> volatility = (Map<String, Object>) stockAnalysis.get("volatility");
        double dailyVol = (Double) volatility.get("daily_volatility");
        
        if (dailyVol < 3) {
            settings.put("stop_loss_percent", 3.0);
            settings.put("take_profit_percent", 6.0);
        } else if (dailyVol < 6) {
            settings.put("stop_loss_percent", 5.0);
            settings.put("take_profit_percent", 10.0);
        } else {
            settings.put("stop_loss_percent", 7.0);
            settings.put("take_profit_percent", 15.0);
        }
        
        settings.put("max_position_size", 20 + (int)(Math.random() * 30));
        settings.put("recommended_capital", 5000000 + (int)(Math.random() * 10000000));
        
        return settings;
    }

    private Map<String, Object> assessRisk(Map<String, Object> stockAnalysis, String strategyName) {
        Map<String, Object> risk = new HashMap<>();
        
        Map<String, Object> volatility = (Map<String, Object>) stockAnalysis.get("volatility");
        double dailyVol = (Double) volatility.get("daily_volatility");
        
        String level = dailyVol < 3 ? "low" : dailyVol < 6 ? "medium" : "high";
        risk.put("level", level);
        risk.put("score", (int) (dailyVol * 10));
        risk.put("factors", Arrays.asList("시장 변동성", "유동성", "뉴스 민감도"));
        
        return risk;
    }

    private Map<String, Object> generateIndexAnalysis(String indexName, int value) {
        Map<String, Object> analysis = new HashMap<>();
        analysis.put("name", indexName);
        analysis.put("value", value);
        analysis.put("change", -20 + (int)(Math.random() * 40));
        analysis.put("change_percent", Math.round((-1 + Math.random() * 2) * 100) / 100.0);
        analysis.put("trend", Math.random() > 0.5 ? "up" : "down");
        return analysis;
    }

    private Map<String, Object> generateSectorPerformance() {
        List<String> sectors = Arrays.asList("IT", "금융", "바이오", "자동차", "화학", "건설");
        
        return sectors.stream().collect(Collectors.toMap(
            sector -> sector,
            sector -> Map.of(
                "return", Math.round((-5 + Math.random() * 10) * 100) / 100.0,
                "volume", 100000000 + (int)(Math.random() * 500000000)
            )
        ));
    }

    private int calculateMarketTradingScore(Map<String, Object> sentiment) {
        int fearGreedIndex = (Integer) sentiment.get("fear_greed_index");
        int volatilityIndex = (Integer) sentiment.get("volatility_index");
        
        int score = 50;
        
        // Fear & Greed 지수 (30-70이 적정)
        if (fearGreedIndex > 30 && fearGreedIndex < 70) score += 20;
        
        // 변동성 지수 (15-25가 적정)
        if (volatilityIndex > 15 && volatilityIndex < 25) score += 15;
        
        return Math.max(0, Math.min(100, score));
    }

    private List<String> getRecommendedStrategies(Map<String, Object> analysis) {
        Map<String, Object> sentiment = (Map<String, Object>) analysis.get("market_sentiment");
        int fearGreedIndex = (Integer) sentiment.get("fear_greed_index");
        
        if (fearGreedIndex < 40) {
            return Arrays.asList("mean_reversion", "rsi_reversal");
        } else if (fearGreedIndex > 60) {
            return Arrays.asList("momentum_breakout", "moving_average_crossover");
        } else {
            return Arrays.asList("bollinger_bands", "macd_signal");
        }
    }

    private String determineMarketStatus(Map<String, Object> sentiment) {
        int fearGreedIndex = (Integer) sentiment.get("fear_greed_index");
        
        if (fearGreedIndex < 30) return "극단적 공포";
        if (fearGreedIndex < 50) return "공포";
        if (fearGreedIndex < 70) return "중립";
        if (fearGreedIndex < 80) return "탐욕";
        return "극단적 탐욕";
    }

    private boolean isMarketOpen() {
        // 간단한 시장 시간 체크 (9-15시)
        int hour = LocalDateTime.now().getHour();
        return hour >= 9 && hour < 15;
    }
}