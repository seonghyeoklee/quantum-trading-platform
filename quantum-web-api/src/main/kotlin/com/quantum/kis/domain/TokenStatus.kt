package com.quantum.kis.domain

/**
 * KIS 토큰 상태 열거형
 * 
 * 하이브리드 토큰 아키텍처에서 토큰의 생명주기 관리
 */
enum class TokenStatus(
    val displayName: String,
    val description: String,
    val canUseForApiCall: Boolean
) {
    /**
     * 활성 상태 - API 호출 가능
     */
    ACTIVE("활성", "정상적으로 사용 가능한 토큰", true),
    
    /**
     * 만료 상태 - 갱신 필요
     */
    EXPIRED("만료", "만료된 토큰, 갱신 필요", false),
    
    /**
     * 폐기 상태 - 재사용 불가
     */
    REVOKED("폐기", "보안상 폐기된 토큰, 재발급 필요", false),
    
    /**
     * 갱신 중 상태 - 임시 상태
     */
    REFRESHING("갱신중", "토큰 갱신 진행 중", false),
    
    /**
     * 오류 상태 - 발급 실패
     */
    ERROR("오류", "토큰 발급/갱신 중 오류 발생", false);
    
    /**
     * 토큰이 사용 가능한 상태인지 확인
     */
    fun isUsable(): Boolean {
        return canUseForApiCall
    }
    
    /**
     * 토큰이 갱신이 필요한 상태인지 확인
     */
    fun needsRefresh(): Boolean {
        return this == EXPIRED || this == ERROR
    }
    
    /**
     * 토큰이 재발급이 필요한 상태인지 확인
     */
    fun needsReissue(): Boolean {
        return this == REVOKED
    }
    
    /**
     * 토큰이 처리 중인 상태인지 확인
     */
    fun isProcessing(): Boolean {
        return this == REFRESHING
    }
    
    companion object {
        /**
         * 사용 가능한 상태 목록
         */
        fun getUsableStatuses(): List<TokenStatus> {
            return values().filter { it.canUseForApiCall }
        }
        
        /**
         * 갱신이 필요한 상태 목록
         */
        fun getRefreshNeededStatuses(): List<TokenStatus> {
            return listOf(EXPIRED, ERROR)
        }
        
        /**
         * 재발급이 필요한 상태 목록
         */
        fun getReissueNeededStatuses(): List<TokenStatus> {
            return listOf(REVOKED)
        }
    }
}