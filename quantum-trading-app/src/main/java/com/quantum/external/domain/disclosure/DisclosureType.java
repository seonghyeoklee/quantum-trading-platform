package com.quantum.external.domain.disclosure;

/**
 * 공시 유형 (DART API 기반)
 */
public enum DisclosureType {
    REGULAR,                // 정기공시 (사업보고서, 분기보고서, 반기보고서)
    MAJOR_ISSUE,            // 주요사항보고 (풍문또는보도, 조회공시, 기타주요경영사항)
    ISSUANCE,               // 발행공시 (증권발행, 유상증자, 무상증자, 전환사채)
    OWNERSHIP,              // 지분공시 (임원·주요주주 특정증권, 자기주식)
    OTHER                   // 기타공시
}
