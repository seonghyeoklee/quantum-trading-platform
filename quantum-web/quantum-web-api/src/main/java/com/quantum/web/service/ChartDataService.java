package com.quantum.web.service;

import com.quantum.web.dto.ChartDataResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

/**
 * Chart Data Service
 * 
 * 차트 데이터 제공 및 캐싱을 담당하는 서비스
 * - 실제 환경에서는 Query Side Repository와 연동
 * - Redis 캐싱을 통한 성능 최적화
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class ChartDataService {

    private final RedisTemplate<String, Object> redisTemplate;

    public ChartDataResponse getChartData(String symbol, String timeframe, int limit) {
        log.debug("Getting chart data for symbol: {}, timeframe: {}, limit: {}", symbol, timeframe, limit);
        
        String cacheKey = String.format("chart:%s:%s:%d", symbol, timeframe, limit);
        
        // Redis 캐시에서 조회 시도
        ChartDataResponse cachedData = (ChartDataResponse) redisTemplate.opsForValue().get(cacheKey);
        if (cachedData != null) {
            log.debug("Chart data found in cache for key: {}", cacheKey);
            return cachedData;
        }
        
        // 캐시에 없으면 데이터 생성 (실제로는 Query Side Repository에서 조회)
        ChartDataResponse chartData = generateMockChartData(symbol, timeframe, limit);
        
        // Redis 캐시에 저장 (TTL: 시간프레임에 따라 차등 적용)
        int cacheTtlMinutes = getCacheTtlMinutes(timeframe);
        redisTemplate.opsForValue().set(cacheKey, chartData, cacheTtlMinutes, TimeUnit.MINUTES);
        
        log.debug("Chart data cached with key: {}, TTL: {} minutes", cacheKey, cacheTtlMinutes);
        
        return chartData;
    }

    public List<Object> searchSymbols(String keyword, int limit) {
        log.debug("Searching symbols with keyword: {}, limit: {}", keyword, limit);
        
        // 실제 환경에서는 Symbol Master Table에서 검색
        List<Object> mockResults = generateMockSearchResults(keyword, limit);
        
        return mockResults;
    }

    public Object getIndicatorData(String symbol, String indicator, int period, int limit) {
        log.debug("Getting indicator data - symbol: {}, indicator: {}, period: {}, limit: {}", 
                 symbol, indicator, period, limit);
        
        String cacheKey = String.format("indicator:%s:%s:%d:%d", symbol, indicator, period, limit);
        
        // Redis 캐시에서 조회
        Object cachedData = redisTemplate.opsForValue().get(cacheKey);
        if (cachedData != null) {
            return cachedData;
        }
        
        // 지표 데이터 생성 (실제로는 계산된 지표 데이터)
        Object indicatorData = generateMockIndicatorData(symbol, indicator, period, limit);
        
        // 캐시 저장 (지표는 5분간 캐시)
        redisTemplate.opsForValue().set(cacheKey, indicatorData, 5, TimeUnit.MINUTES);
        
        return indicatorData;
    }

    private ChartDataResponse generateMockChartData(String symbol, String timeframe, int limit) {
        List<ChartDataResponse.CandleData> candles = new ArrayList<>();
        List<ChartDataResponse.VolumeData.VolumePoint> volumePoints = new ArrayList<>();
        
        // 시작 시간 계산
        LocalDateTime startTime = LocalDateTime.now().minusHours(limit);
        
        // Mock 데이터 생성
        BigDecimal basePrice = BigDecimal.valueOf(50000); // 기준가 50,000원
        
        for (int i = 0; i < limit; i++) {
            LocalDateTime timestamp = startTime.plusHours(i);
            
            // 단순한 랜덤 워크로 가격 데이터 생성
            double variation = (Math.random() - 0.5) * 0.02; // ±1% 변동
            BigDecimal open = basePrice.multiply(BigDecimal.valueOf(1 + variation));
            BigDecimal high = open.multiply(BigDecimal.valueOf(1 + Math.random() * 0.01));
            BigDecimal low = open.multiply(BigDecimal.valueOf(1 - Math.random() * 0.01));
            BigDecimal close = low.add(high.subtract(low).multiply(BigDecimal.valueOf(Math.random())));
            
            long volume = (long) (1000000 + Math.random() * 2000000); // 100만~300만주
            
            candles.add(ChartDataResponse.CandleData.builder()
                    .timestamp(timestamp)
                    .open(open)
                    .high(high)
                    .low(low)
                    .close(close)
                    .volume(volume)
                    .build());
                    
            volumePoints.add(ChartDataResponse.VolumeData.VolumePoint.builder()
                    .timestamp(timestamp)
                    .volume(volume)
                    .build());
                    
            basePrice = close; // 다음 캔들의 기준가로 사용
        }
        
        ChartDataResponse.VolumeData volumeData = ChartDataResponse.VolumeData.builder()
                .points(volumePoints)
                .build();
        
        return ChartDataResponse.builder()
                .symbol(symbol)
                .timeframe(timeframe)
                .candles(candles)
                .volume(volumeData)
                .build();
    }
    
    private List<Object> generateMockSearchResults(String keyword, int limit) {
        List<Object> results = new ArrayList<>();
        
        // Mock 검색 결과 (실제로는 DB 검색)
        String[] companies = {
            "삼성전자", "SK하이닉스", "LG화학", "삼성바이오로직스", "NAVER",
            "카카오", "셀트리온", "현대차", "기아", "POSCO홀딩스"
        };
        
        String[] codes = {
            "005930", "000660", "051910", "207940", "035420",
            "035720", "068270", "005380", "000270", "005490"
        };
        
        for (int i = 0; i < Math.min(limit, companies.length); i++) {
            if (companies[i].contains(keyword) || codes[i].contains(keyword)) {
                results.add(new SearchResult(codes[i], companies[i], "KOSPI"));
            }
        }
        
        return results;
    }
    
    private Object generateMockIndicatorData(String symbol, String indicator, int period, int limit) {
        List<Object> data = new ArrayList<>();
        LocalDateTime startTime = LocalDateTime.now().minusHours(limit);
        
        // Mock 지표 데이터 생성
        for (int i = 0; i < limit; i++) {
            LocalDateTime timestamp = startTime.plusHours(i);
            
            switch (indicator) {
                case "RSI":
                    data.add(new IndicatorPoint(timestamp, 30 + Math.random() * 40)); // RSI 30-70
                    break;
                case "MACD":
                    data.add(new MacdPoint(timestamp, Math.random() * 10 - 5, Math.random() * 10 - 5));
                    break;
                default:
                    data.add(new IndicatorPoint(timestamp, Math.random() * 100));
            }
        }
        
        return new IndicatorData(symbol, indicator, period, data);
    }
    
    private int getCacheTtlMinutes(String timeframe) {
        return switch (timeframe) {
            case "1m" -> 1;      // 1분 캐시
            case "5m" -> 5;      // 5분 캐시
            case "15m" -> 15;    // 15분 캐시
            case "1h" -> 60;     // 1시간 캐시
            case "1d" -> 360;    // 6시간 캐시
            default -> 60;       // 기본 1시간
        };
    }
    
    // Inner classes for mock data
    public record SearchResult(String code, String name, String market) {}
    public record IndicatorPoint(LocalDateTime timestamp, double value) {}
    public record MacdPoint(LocalDateTime timestamp, double macd, double signal) {}
    public record IndicatorData(String symbol, String indicator, int period, List<Object> data) {}
}