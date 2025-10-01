package com.quantum.external.infrastructure.adapter.out.dart;

import com.quantum.external.application.port.out.DisclosureApiPort;
import com.quantum.external.domain.disclosure.Disclosure;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.time.LocalDate;
import java.util.List;

/**
 * DART(금융감독원 전자공시) API 어댑터
 * TODO: DART Open API 스펙 확인 후 구현
 *
 * 참고 사항:
 * - API 엔드포인트: https://opendart.fss.or.kr/api/list.json
 * - 인증 방식: API Key (쿼리 파라미터)
 * - 요청 파라미터: crtfc_key, corp_code, bgn_de, end_de, pblntf_ty
 * - 종목코드 → 법인코드 매핑 필요 (별도 API 또는 매핑 테이블)
 * - 응답 구조: JSON (list 배열)
 * - Rate Limit: 일 10,000건
 */
@Component
public class DartAdapter implements DisclosureApiPort {

    private static final Logger log = LoggerFactory.getLogger(DartAdapter.class);

    private final RestClient restClient;

    public DartAdapter(RestClient restClient) {
        this.restClient = restClient;
    }

    @Override
    public List<Disclosure> searchDisclosures(String stockCode, LocalDate startDate, LocalDate endDate) {
        log.info("DART 공시 검색 시작: stockCode={}, startDate={}, endDate={}", stockCode, startDate, endDate);

        // TODO: DART API 호출 구현
        // 1. API 키 설정 확인 (application-secrets.yml)
        // 2. 종목코드 → 법인코드 매핑 (별도 API 또는 DB)
        // 3. RestClient로 API 호출
        // 4. 응답 JSON 파싱
        // 5. Disclosure 도메인 객체로 변환
        // 6. 공시 유형 분류

        throw new UnsupportedOperationException("DART API 구현 필요 - API 스펙 및 법인코드 매핑 확인 필요");
    }
}
