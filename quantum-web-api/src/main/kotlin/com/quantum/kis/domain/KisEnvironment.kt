package com.quantum.kis.domain

/**
 * KIS API 환경 정의
 * 
 * @property displayName 표시명
 * @property description 설명
 */
enum class KisEnvironment(
    val displayName: String,
    val description: String
) {
    /**
     * 실전투자 환경 (실제 거래)
     * - REST API: 20건/초
     * - WebSocket: 41개 등록 한도
     */
    LIVE("실전투자", "실제 거래가 가능한 운영 환경"),
    
    /**
     * 모의투자 환경 (테스트 거래)
     * - REST API: 2건/초
     * - WebSocket: 41개 등록 한도
     */
    SANDBOX("모의투자", "테스트 거래를 위한 시뮬레이션 환경")
}