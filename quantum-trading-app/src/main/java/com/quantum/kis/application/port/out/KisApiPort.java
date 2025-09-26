package com.quantum.kis.application.port.out;

import com.quantum.kis.domain.KisEnvironment;
import com.quantum.kis.dto.AccessTokenResponse;
import com.quantum.kis.dto.ChartDataResponse;
import com.quantum.kis.dto.WebSocketKeyResponse;

import java.time.LocalDate;

/**
 * KIS API 호출 포트
 * 외부 KIS API와의 통신을 추상화
 */
public interface KisApiPort {

    /**
     * 액세스 토큰을 발급한다.
     * @param environment KIS 환경
     * @return 액세스 토큰 응답
     */
    AccessTokenResponse issueAccessToken(KisEnvironment environment);

    /**
     * 웹소켓 키를 발급한다.
     * @param environment KIS 환경
     * @return 웹소켓 키 응답
     */
    WebSocketKeyResponse issueWebSocketKey(KisEnvironment environment);

    /**
     * 국내주식 일봉차트 데이터를 조회한다.
     * @param environment KIS 환경
     * @param stockCode 종목코드 (6자리, 예: 005930)
     * @param startDate 조회 시작일
     * @param endDate 조회 종료일
     * @return 차트 데이터 응답
     */
    ChartDataResponse getDailyChartData(KisEnvironment environment, String stockCode,
                                       LocalDate startDate, LocalDate endDate);
}