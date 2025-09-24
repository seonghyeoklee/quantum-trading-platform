package com.quantum.kis.infrastructure.config;

import com.quantum.kis.domain.KisEnvironment;
import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * KIS API 설정 데이터 (kis_devlp.yaml 구조 기반)
 * application.yml에서 kis로 시작하는 설정을 바인딩
 */
@ConfigurationProperties(prefix = "kis")
public class KisConfig {

    // API 키 정보
    private String myApp;           // 실전 앱키
    private String mySec;           // 실전 시크릿
    private String paperApp;        // 모의 앱키
    private String paperSec;        // 모의 시크릿

    // HTS ID
    private String myHtsId;         // HTS ID

    // 계좌 정보
    private String myAcctStock;     // 실전 주식계좌 (8자리)
    private String myAcctFuture;    // 실전 선물옵션계좌 (8자리)
    private String myPaperStock;    // 모의 주식계좌 (8자리)
    private String myPaperFuture;   // 모의 선물옵션계좌 (8자리)
    private String myProd;          // 계좌 상품코드 (01: 종합계좌, 03: 선물옵션, 08: 해외선물옵션)

    // 도메인 정보
    private String prod;            // 실전 REST API URL
    private String ops;             // 실전 WebSocket URL
    private String vps;             // 모의 REST API URL
    private String vops;            // 모의 WebSocket URL

    // 기타
    private String myAgent;         // User-Agent

    // Getters
    public String getMyApp() { return myApp; }
    public String getMySec() { return mySec; }
    public String getPaperApp() { return paperApp; }
    public String getPaperSec() { return paperSec; }
    public String getMyHtsId() { return myHtsId; }
    public String getMyAcctStock() { return myAcctStock; }
    public String getMyAcctFuture() { return myAcctFuture; }
    public String getMyPaperStock() { return myPaperStock; }
    public String getMyPaperFuture() { return myPaperFuture; }
    public String getMyProd() { return myProd; }
    public String getProd() { return prod; }
    public String getOps() { return ops; }
    public String getVps() { return vps; }
    public String getVops() { return vops; }
    public String getMyAgent() { return myAgent; }

    // Setters
    public void setMyApp(String myApp) { this.myApp = myApp; }
    public void setMySec(String mySec) { this.mySec = mySec; }
    public void setPaperApp(String paperApp) { this.paperApp = paperApp; }
    public void setPaperSec(String paperSec) { this.paperSec = paperSec; }
    public void setMyHtsId(String myHtsId) { this.myHtsId = myHtsId; }
    public void setMyAcctStock(String myAcctStock) { this.myAcctStock = myAcctStock; }
    public void setMyAcctFuture(String myAcctFuture) { this.myAcctFuture = myAcctFuture; }
    public void setMyPaperStock(String myPaperStock) { this.myPaperStock = myPaperStock; }
    public void setMyPaperFuture(String myPaperFuture) { this.myPaperFuture = myPaperFuture; }
    public void setMyProd(String myProd) { this.myProd = myProd; }
    public void setProd(String prod) { this.prod = prod; }
    public void setOps(String ops) { this.ops = ops; }
    public void setVps(String vps) { this.vps = vps; }
    public void setVops(String vops) { this.vops = vops; }
    public void setMyAgent(String myAgent) { this.myAgent = myAgent; }

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