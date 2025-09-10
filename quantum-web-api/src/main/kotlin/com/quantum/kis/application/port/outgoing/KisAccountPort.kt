package com.quantum.kis.application.port.outgoing

import com.quantum.kis.domain.KisAccount
import com.quantum.kis.domain.KisEnvironment
import java.util.*

/**
 * KIS 계좌 관련 출력 포트 (헥사고날 아키텍처)
 * 
 * Application 계층이 Infrastructure 계층에 직접 의존하지 않도록
 * 인터페이스를 통해 의존성 역전
 */
interface KisAccountPort {
    
    /**
     * 사용자 ID로 활성화된 KIS 계정 조회
     */
    fun findByUserIdAndIsActiveTrue(userId: Long): List<KisAccount>
    
    /**
     * 사용자 ID와 환경으로 첫 번째 활성 계정 조회
     */
    fun findFirstByUserIdAndEnvironmentAndIsActiveTrueOrderByCreatedAtAsc(
        userId: Long, 
        environment: KisEnvironment
    ): Optional<KisAccount>
    
    /**
     * 사용자가 활성 KIS 계정을 가지고 있는지 확인
     */
    fun existsByUserIdAndIsActiveTrue(userId: Long): Boolean
    
    /**
     * KIS 계정 저장
     */
    fun save(kisAccount: KisAccount): KisAccount
}