package com.quantum.api.adapter.out.stock;

import com.quantum.kis.service.KisTokenProvider;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

/**
 * quantum-api를 위한 KisTokenProvider 구현체
 *
 * <p>현재는 토큰 기능을 사용하지 않으므로 기본 구현만 제공 필요시 quantum-batch와 유사하게 구현 가능
 */
@Slf4j
@Service
public class KisTokenProviderAdapter implements KisTokenProvider {

    @Override
    public String getValidAccessToken() {
        log.warn("KisTokenProviderAdapter: getValidAccessToken not implemented - returning null");
        return null;
    }

    @Override
    public boolean checkRateLimit(String apiEndpoint) {
        log.debug("KisTokenProviderAdapter: checkRateLimit not implemented - allowing by default");
        return true;
    }

    @Override
    public boolean acquireWithWait(String apiEndpoint) {
        log.debug("KisTokenProviderAdapter: acquireWithWait not implemented - allowing by default");
        return true;
    }
}
