package com.quantum.kis.model;

import com.quantum.kis.model.enums.KisCustomerType;
import com.quantum.kis.model.enums.KisTransactionId;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/** KIS API 요청 헤더 모델 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class KisRequestHeader {

    private String contentType; // Content-Type
    private String authorization; // 접근토큰
    private String appkey; // 앱키
    private String appsecret; // 앱시크릿키
    private String personalSeckey; // 고객식별키 (Optional)
    private String trId; // 거래ID
    private String trCont; // 연속 거래 여부 (Optional)
    private String custtype; // 고객 타입
    private String seqNo; // 일련번호 (Optional)
    private String macAddress; // 맥주소 (Optional)
    private String phoneNumber; // 핸드폰번호 (Optional)
    private String ipAddr; // 접속 단말 공인 IP (Optional)
    private String hashkey; // 해쉬키 (Optional)
    private String gtUid; // Global UID (Optional)

    /** 주식 현재가 조회용 헤더 생성 (KIS API 공식 명세 기준) */
    public static KisRequestHeader forCurrentPrice(
            String authorization, String appkey, String appsecret) {
        return KisRequestHeader.builder()
                .contentType("application/json; charset=utf-8") // 공식 명세에 따른 Content-Type
                .authorization(authorization)
                .appkey(appkey)
                .appsecret(appsecret)
                .trId(KisTransactionId.CURRENT_PRICE.getCode()) // 주식현재가 조회 TR_ID
                .custtype(KisCustomerType.PERSONAL.getCode()) // 개인 고객
                .build();
    }
}
