package com.quantum.api.kiwoom.dto.sector.info;

import com.quantum.api.kiwoom.dto.sector.common.BaseSectorRequest;
import com.quantum.api.kiwoom.dto.sector.common.SectorApiType;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;

/**
 * 전업종지수요청 DTO (ka20003)
 * 전체 업종 지수의 현재가 정보 조회
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(callSuper=false)
@Schema(description = "전업종지수요청 (ka20003)")
public class AllSectorIndicesRequest extends BaseSectorRequest {

    @Schema(description = "시장구분 (0:코스피, 1:코스닥, 2:코스피200, 9:전체)", example = "9", required = true)
    private String marketType;

    @Schema(description = "정렬기준 (1:지수순, 2:등락률순, 3:거래량순)", example = "2", required = true)
    private String sortType;

    @Schema(description = "정렬방향 (1:내림차순, 2:오름차순)", example = "1", required = true)
    private String sortOrder;

    @Schema(description = "업종분류 (1:전체, 2:대분류만, 3:중분류만, 4:소분류만)", example = "1", required = true)
    private String categoryType;

    @Override
    public SectorApiType getApiType() {
        return SectorApiType.SECTOR_INFO;
    }

    @Override
    public String getApiId() {
        return "ka20003";
    }

    @Override
    public void validate() {
        super.validate();
        
        // 시장구분 검증 (전업종은 9도 허용)
        if (marketType == null || !marketType.matches("[0-2]|9")) {
            throw new IllegalArgumentException("시장구분은 0(코스피), 1(코스닥), 2(코스피200), 9(전체) 중 하나여야 합니다: " + marketType);
        }
        
        // 정렬기준 검증
        if (sortType == null || !sortType.matches("[1-3]")) {
            throw new IllegalArgumentException("정렬기준은 1(지수순), 2(등락률순), 3(거래량순) 중 하나여야 합니다: " + sortType);
        }
        
        // 정렬방향 검증
        if (sortOrder == null || !sortOrder.matches("[1-2]")) {
            throw new IllegalArgumentException("정렬방향은 1(내림차순), 2(오름차순) 중 하나여야 합니다: " + sortOrder);
        }
        
        // 업종분류 검증
        if (categoryType == null || !categoryType.matches("[1-4]")) {
            throw new IllegalArgumentException("업종분류는 1(전체), 2(대분류만), 3(중분류만), 4(소분류만) 중 하나여야 합니다: " + categoryType);
        }
    }
}