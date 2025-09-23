package com.quantum.kis.config;

import com.quantum.kis.domain.KisEnvironment;

/**
 * KIS API 설정 데이터 (kis_devlp.yaml 구조 기반)
 */
public record KisConfig(
        // API 키 정보
        String myApp,           // 실전 앱키
        String mySec,           // 실전 시크릿
        String paperApp,        // 모의 앱키
        String paperSec,        // 모의 시크릿

        // HTS ID
        String myHtsId,         // HTS ID

        // 계좌 정보
        String myAcctStock,     // 실전 주식계좌 (8자리)
        String myAcctFuture,    // 실전 선물옵션계좌 (8자리)
        String myPaperStock,    // 모의 주식계좌 (8자리)
        String myPaperFuture,   // 모의 선물옵션계좌 (8자리)
        String myProd,          // 계좌 상품코드 (01: 종합계좌, 03: 선물옵션, 08: 해외선물옵션)

        // 도메인 정보
        String prod,            // 실전 REST API URL
        String ops,             // 실전 WebSocket URL
        String vps,             // 모의 REST API URL
        String vops,            // 모의 WebSocket URL

        // 기타
        String myAgent          // User-Agent
) {
    /**
     * 환경에 따른 앱키를 반환한다.
     * @param env KIS 환경
     * @return 앱키
     */
    public String getAppKey(KisEnvironment env) {
        return env == KisEnvironment.PROD ? myApp : paperApp;
    }

    /**
     * 환경에 따른 시크릿키를 반환한다.
     * @param env KIS 환경
     * @return 시크릿키
     */
    public String getSecretKey(KisEnvironment env) {
        return env == KisEnvironment.PROD ? mySec : paperSec;
    }

    /**
     * 환경에 따른 계좌번호를 반환한다.
     * @param env KIS 환경
     * @return 계좌번호 (8자리)
     */
    public String getStockAccount(KisEnvironment env) {
        return env == KisEnvironment.PROD ? myAcctStock : myPaperStock;
    }

    /**
     * 환경에 따른 선물옵션 계좌번호를 반환한다.
     * @param env KIS 환경
     * @return 선물옵션 계좌번호 (8자리)
     */
    public String getFutureAccount(KisEnvironment env) {
        return env == KisEnvironment.PROD ? myAcctFuture : myPaperFuture;
    }

    /**
     * 환경에 따른 REST API URL을 반환한다.
     * @param env KIS 환경
     * @return REST API URL
     */
    public String getRestApiUrl(KisEnvironment env) {
        return env == KisEnvironment.PROD ? prod : vps;
    }

    /**
     * 환경에 따른 WebSocket URL을 반환한다.
     * @param env KIS 환경
     * @return WebSocket URL
     */
    public String getWebSocketUrl(KisEnvironment env) {
        return env == KisEnvironment.PROD ? ops : vops;
    }
}