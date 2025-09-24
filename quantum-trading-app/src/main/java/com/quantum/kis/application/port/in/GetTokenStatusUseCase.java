package com.quantum.kis.application.port.in;

import com.quantum.kis.domain.KisEnvironment;
import com.quantum.kis.domain.token.KisToken;
import com.quantum.kis.dto.TokenInfo;

import java.util.List;
import java.util.Map;

/**
 * 토큰 상태 조회 Use Case
 */
public interface GetTokenStatusUseCase {

    /**
     * 현재 저장된 토큰 상태를 반환한다.
     * @return 토큰 상태 맵
     */
    Map<String, TokenInfo> getAllTokenStatus();

    /**
     * 특정 환경의 토큰들을 반환한다.
     * @param environment KIS 환경
     * @return 토큰 리스트
     */
    List<KisToken> getTokensByEnvironment(KisEnvironment environment);

    /**
     * 갱신이 필요한 토큰들을 조회한다.
     * @return 갱신 필요 토큰 리스트
     */
    List<KisToken> getTokensNeedingRenewal();
}