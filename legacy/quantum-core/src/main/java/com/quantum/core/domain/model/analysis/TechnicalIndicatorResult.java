package com.quantum.core.domain.model.analysis;

import com.quantum.core.domain.model.common.TechnicalIndicatorType;
import com.quantum.core.domain.model.common.TimeframeCode;
import com.quantum.core.infrastructure.common.BaseTimeEntity;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.Comment;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.Map;

/**
 * 기술적 지표 계산 결과 엔티티
 * 차트 분석을 위한 다양한 기술적 지표들의 계산 결과를 저장
 */
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Entity
@Table(
    name = "tb_technical_indicator_result",
    uniqueConstraints = @UniqueConstraint(columnNames = {"symbol", "indicator_type", "timeframe", "calculation_time"}),
    indexes = {
        @Index(name = "idx_indicator_symbol_type", columnList = "symbol, indicator_type"),
        @Index(name = "idx_indicator_calculation_time", columnList = "calculation_time"),
        @Index(name = "idx_indicator_symbol_timeframe", columnList = "symbol, timeframe")
    }
)
public class TechnicalIndicatorResult extends BaseTimeEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "symbol", nullable = false, length = 20)
    @Comment("종목코드")
    private String symbol;

    @Enumerated(EnumType.STRING)
    @Column(name = "indicator_type", nullable = false, length = 30)
    @Comment("기술적 지표 타입")
    private TechnicalIndicatorType indicatorType;

    @Enumerated(EnumType.STRING)
    @Column(name = "timeframe", nullable = false, length = 10)
    @Comment("시간 프레임")
    private TimeframeCode timeframe;

    @Column(name = "main_value", precision = 15, scale = 6)
    @Comment("주요 값 (예: RSI 값, MA 값)")
    private BigDecimal mainValue;

    @Column(name = "sub_value", precision = 15, scale = 6)
    @Comment("보조 값 (예: MACD Signal, BB 상단선)")
    private BigDecimal subValue;

    @Column(name = "third_value", precision = 15, scale = 6)
    @Comment("3차 값 (예: MACD Histogram, BB 하단선)")
    private BigDecimal thirdValue;

    @Column(name = "signal", length = 10)
    @Comment("매매 신호 (BUY, SELL, HOLD, STRONG_BUY, STRONG_SELL)")
    private String signal;

    @Column(name = "confidence_score", precision = 5, scale = 2)
    @Comment("신뢰도 점수 (0.00 ~ 100.00)")
    private BigDecimal confidenceScore;

    @Column(name = "calculation_time", nullable = false)
    @Comment("계산 시점")
    private LocalDateTime calculationTime;

    @Column(name = "parameters", columnDefinition = "TEXT")
    @Comment("계산 파라미터 (JSON 형태)")
    private String parameters;

    @Builder
    public TechnicalIndicatorResult(
            String symbol,
            TechnicalIndicatorType indicatorType,
            TimeframeCode timeframe,
            BigDecimal mainValue,
            BigDecimal subValue,
            BigDecimal thirdValue,
            String signal,
            BigDecimal confidenceScore,
            LocalDateTime calculationTime,
            String parameters) {
        
        this.symbol = symbol;
        this.indicatorType = indicatorType;
        this.timeframe = timeframe;
        this.mainValue = mainValue;
        this.subValue = subValue;
        this.thirdValue = thirdValue;
        this.signal = signal;
        this.confidenceScore = confidenceScore;
        this.calculationTime = calculationTime != null ? calculationTime : LocalDateTime.now();
        this.parameters = parameters;
    }

    /**
     * 매수 신호 여부
     */
    public boolean isBuySignal() {
        return "BUY".equals(signal) || "STRONG_BUY".equals(signal);
    }

    /**
     * 매도 신호 여부
     */
    public boolean isSellSignal() {
        return "SELL".equals(signal) || "STRONG_SELL".equals(signal);
    }

    /**
     * 강한 신호 여부 (Strong Buy/Sell)
     */
    public boolean isStrongSignal() {
        return "STRONG_BUY".equals(signal) || "STRONG_SELL".equals(signal);
    }

    /**
     * 신뢰도가 높은 신호인지 확인 (80% 이상)
     */
    public boolean isHighConfidence() {
        return confidenceScore != null && confidenceScore.compareTo(BigDecimal.valueOf(80)) >= 0;
    }

    /**
     * 지표별 특화 해석
     */
    public String getIndicatorInterpretation() {
        return switch (indicatorType) {
            case RSI -> interpretRSI();
            case STOCHASTIC -> interpretStochastic();
            case MACD -> interpretMACD();
            case BOLLINGER_BANDS -> interpretBollingerBands();
            default -> "일반적인 " + indicatorType.getKoreanName() + " 신호";
        };
    }

    private String interpretRSI() {
        if (mainValue == null) return "RSI 값 없음";
        
        double rsi = mainValue.doubleValue();
        if (rsi >= 70) return "과매수 구간 (매도 고려)";
        if (rsi <= 30) return "과매도 구간 (매수 고려)";
        if (rsi >= 50) return "상승 모멘텀";
        return "하락 모멘텀";
    }

    private String interpretStochastic() {
        if (mainValue == null) return "스토캐스틱 값 없음";
        
        double stoch = mainValue.doubleValue();
        if (stoch >= 80) return "과매수 (매도 신호)";
        if (stoch <= 20) return "과매도 (매수 신호)";
        return "중립 구간";
    }

    private String interpretMACD() {
        if (mainValue == null || subValue == null) return "MACD 값 불완전";
        
        boolean isPositive = mainValue.compareTo(BigDecimal.ZERO) > 0;
        boolean isAboveSignal = mainValue.compareTo(subValue) > 0;
        
        if (isPositive && isAboveSignal) return "강한 상승 추세";
        if (isPositive && !isAboveSignal) return "상승 추세 약화";
        if (!isPositive && isAboveSignal) return "하락 추세 약화";
        return "강한 하락 추세";
    }

    private String interpretBollingerBands() {
        if (mainValue == null) return "볼린저밴드 값 없음";
        
        // mainValue는 현재가의 밴드 내 위치 (0~1)로 가정
        double position = mainValue.doubleValue();
        if (position >= 0.8) return "상단 근접 (과매수)";
        if (position <= 0.2) return "하단 근접 (과매도)";
        if (position >= 0.6) return "상단 편향";
        if (position <= 0.4) return "하단 편향";
        return "중앙 위치";
    }
}