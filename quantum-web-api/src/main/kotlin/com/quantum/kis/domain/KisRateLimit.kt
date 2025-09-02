package com.quantum.kis.domain

/**
 * KIS API 환경별 유량 제한 정책 (2025.04.28 기준)
 * 
 * @property restCallsPerSecond REST API 초당 호출 제한
 * @property websocketSessionLimit WebSocket 세션 제한 (계좌별)
 * @property websocketDataLimit WebSocket 실시간 데이터 등록 제한
 */
enum class KisRateLimit(
    val restCallsPerSecond: Int,
    val websocketSessionLimit: Int,
    val websocketDataLimit: Int
) {
    /**
     * 실전투자 환경 유량 제한
     * - REST API: 1초당 20건
     * - WebSocket: 세션 1개, 실시간 데이터 41건
     */
    LIVE(20, 1, 41),
    
    /**
     * 모의투자 환경 유량 제한  
     * - REST API: 1초당 2건
     * - WebSocket: 세션 1개, 실시간 데이터 41건
     */
    SANDBOX(2, 1, 41);
    
    companion object {
        /**
         * 환경에 해당하는 유량 제한 정책 조회
         */
        fun forEnvironment(environment: KisEnvironment): KisRateLimit {
            return valueOf(environment.name)
        }
    }
}