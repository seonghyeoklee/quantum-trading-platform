package com.quantum.core.domain.port.service;

import com.quantum.core.domain.model.StockCandle;
import com.quantum.core.domain.model.analysis.TechnicalIndicatorResult;
import com.quantum.core.domain.model.common.TechnicalIndicatorType;
import com.quantum.core.domain.model.common.TimeframeCode;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * 기술적 분석 서비스 포트
 * 주식 캔들 데이터를 기반으로 다양한 기술적 지표를 계산
 */
public interface TechnicalAnalysisService {

    /**
     * 단일 기술적 지표 계산
     *
     * @param symbol 종목코드
     * @param indicatorType 지표 타입
     * @param timeframe 시간 프레임
     * @param candleData 캔들 데이터 (최신순)
     * @param parameters 계산 파라미터 (예: MA 기간, RSI 기간 등)
     * @return 계산된 지표 결과
     */
    TechnicalIndicatorResult calculateIndicator(
        String symbol,
        TechnicalIndicatorType indicatorType,
        TimeframeCode timeframe,
        List<StockCandle> candleData,
        Map<String, Object> parameters
    );

    /**
     * 여러 기술적 지표 일괄 계산
     *
     * @param symbol 종목코드
     * @param indicatorTypes 계산할 지표 타입들
     * @param timeframe 시간 프레임
     * @param candleData 캔들 데이터
     * @return 지표별 계산 결과 맵
     */
    Map<TechnicalIndicatorType, TechnicalIndicatorResult> calculateMultipleIndicators(
        String symbol,
        List<TechnicalIndicatorType> indicatorTypes,
        TimeframeCode timeframe,
        List<StockCandle> candleData
    );

    /**
     * 이동평균 계산
     *
     * @param candleData 캔들 데이터
     * @param period 기간
     * @return 이동평균 값
     */
    BigDecimal calculateMovingAverage(List<StockCandle> candleData, int period);

    /**
     * 지수이동평균 계산
     *
     * @param candleData 캔들 데이터
     * @param period 기간
     * @return 지수이동평균 값
     */
    BigDecimal calculateEMA(List<StockCandle> candleData, int period);

    /**
     * RSI 계산
     *
     * @param candleData 캔들 데이터
     * @param period 기간 (일반적으로 14)
     * @return RSI 값 (0~100)
     */
    BigDecimal calculateRSI(List<StockCandle> candleData, int period);

    /**
     * MACD 계산
     *
     * @param candleData 캔들 데이터
     * @param fastPeriod 빠른 EMA 기간 (기본 12)
     * @param slowPeriod 느린 EMA 기간 (기본 26)
     * @param signalPeriod 시그널 EMA 기간 (기본 9)
     * @return MACD 결과 (MACD Line, Signal Line, Histogram)
     */
    Map<String, BigDecimal> calculateMACD(
        List<StockCandle> candleData, 
        int fastPeriod, 
        int slowPeriod, 
        int signalPeriod
    );

    /**
     * 볼린저 밴드 계산
     *
     * @param candleData 캔들 데이터
     * @param period 이동평균 기간 (기본 20)
     * @param standardDeviation 표준편차 배수 (기본 2.0)
     * @return 볼린저 밴드 (상단선, 중간선, 하단선)
     */
    Map<String, BigDecimal> calculateBollingerBands(
        List<StockCandle> candleData, 
        int period, 
        double standardDeviation
    );

    /**
     * 스토캐스틱 계산
     *
     * @param candleData 캔들 데이터
     * @param kPeriod %K 기간 (기본 14)
     * @param dPeriod %D 기간 (기본 3)
     * @return 스토캐스틱 (%K, %D)
     */
    Map<String, BigDecimal> calculateStochastic(
        List<StockCandle> candleData, 
        int kPeriod, 
        int dPeriod
    );

    /**
     * ATR (Average True Range) 계산
     *
     * @param candleData 캔들 데이터
     * @param period 기간 (기본 14)
     * @return ATR 값
     */
    BigDecimal calculateATR(List<StockCandle> candleData, int period);

    /**
     * 피봇 포인트 계산
     *
     * @param previousCandle 전일 캔들
     * @return 피봇 포인트 (PP, R1, R2, S1, S2)
     */
    Map<String, BigDecimal> calculatePivotPoints(StockCandle previousCandle);

    /**
     * 종합 매매 신호 생성
     *
     * @param symbol 종목코드
     * @param timeframe 시간 프레임
     * @param candleData 캔들 데이터
     * @return 종합 신호 ("STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL")
     */
    String generateOverallSignal(
        String symbol, 
        TimeframeCode timeframe, 
        List<StockCandle> candleData
    );

    /**
     * 특정 기간의 기술적 지표 결과 조회
     *
     * @param symbol 종목코드
     * @param indicatorType 지표 타입
     * @param timeframe 시간 프레임
     * @param startTime 시작 시간
     * @param endTime 종료 시간
     * @return 기술적 지표 결과 목록
     */
    List<TechnicalIndicatorResult> getIndicatorResults(
        String symbol,
        TechnicalIndicatorType indicatorType,
        TimeframeCode timeframe,
        LocalDateTime startTime,
        LocalDateTime endTime
    );
}