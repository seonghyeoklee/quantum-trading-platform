package com.quantum.web.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

/**
 * Chart Data Response for Frontend
 * 
 * 프론트엔드 차트 라이브러리(ApexCharts, TradingView)를 위한 데이터 구조
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ChartDataResponse {
    
    private String symbol;
    private String timeframe; // 1m, 5m, 15m, 1h, 1d, 1w, 1M
    private List<CandleData> candles;
    private VolumeData volume;
    
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class CandleData {
        @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss")
        private LocalDateTime timestamp;
        private BigDecimal open;
        private BigDecimal high;
        private BigDecimal low;
        private BigDecimal close;
        private Long volume;
        
        // ApexCharts 호환 형태로 변환
        public Object[] toApexFormat() {
            return new Object[]{
                timestamp.toString(),
                open,
                high,
                low,
                close
            };
        }
        
        // TradingView 호환 형태로 변환
        public TradingViewCandle toTradingViewFormat() {
            return TradingViewCandle.builder()
                    .time(timestamp.toEpochSecond(java.time.ZoneOffset.UTC))
                    .open(open.doubleValue())
                    .high(high.doubleValue())
                    .low(low.doubleValue())
                    .close(close.doubleValue())
                    .volume(volume)
                    .build();
        }
    }
    
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class VolumeData {
        private List<VolumePoint> points;
        
        @Data
        @Builder
        @NoArgsConstructor
        @AllArgsConstructor
        public static class VolumePoint {
            @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss")
            private LocalDateTime timestamp;
            private Long volume;
        }
    }
    
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class TradingViewCandle {
        private long time;
        private double open;
        private double high;
        private double low;
        private double close;
        private Long volume;
    }
}