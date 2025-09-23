package com.quantum.kis.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.ConstructorBinding;

/**
 * KIS API 설정 프로퍼티 (kis_devlp.yaml 구조 기반)
 * application.yml에서 kis로 시작하는 설정을 바인딩
 */
@ConfigurationProperties(prefix = "kis")
public record KisConfigProperties(
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
        String myProd,          // 계좌 상품코드

        // 도메인 정보
        String prod,            // 실전 REST API URL
        String ops,             // 실전 WebSocket URL
        String vps,             // 모의 REST API URL
        String vops,            // 모의 WebSocket URL

        // 기타
        String myAgent          // User-Agent
) {
    @ConstructorBinding
    public KisConfigProperties {
        // 필수값 검증
        if (myApp == null || myApp.isBlank()) {
            throw new IllegalArgumentException("kis.my-app은 필수값입니다.");
        }
        if (mySec == null || mySec.isBlank()) {
            throw new IllegalArgumentException("kis.my-sec는 필수값입니다.");
        }
        if (paperApp == null || paperApp.isBlank()) {
            throw new IllegalArgumentException("kis.paper-app은 필수값입니다.");
        }
        if (paperSec == null || paperSec.isBlank()) {
            throw new IllegalArgumentException("kis.paper-sec는 필수값입니다.");
        }
        if (myAgent == null || myAgent.isBlank()) {
            throw new IllegalArgumentException("kis.my-agent는 필수값입니다.");
        }
    }

    /**
     * KisConfig 객체로 변환
     * @return KisConfig 객체
     */
    public KisConfig toKisConfig() {
        return new KisConfig(
                myApp, mySec, paperApp, paperSec,
                myHtsId,
                myAcctStock, myAcctFuture, myPaperStock, myPaperFuture, myProd,
                prod, ops, vps, vops,
                myAgent
        );
    }
}