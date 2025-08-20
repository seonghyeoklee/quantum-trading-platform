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
 * 업종현재가요청 DTO (ka20001)
 * 특정 업종의 현재가 정보 및 상위/하위 종목 조회
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(callSuper=false)
@Schema(description = "업종현재가요청 (ka20001)")
public class SectorCurrentPriceRequest extends BaseSectorRequest {

    @Schema(description = "업종코드 (3자리)", example = "001", required = true)
    private String sectorCode;

    @Schema(description = "시장구분 (0:코스피, 1:코스닥, 2:코스피200)", example = "0", required = true)
    private String marketType;

    @Schema(description = "조회범위 (1:업종지수만, 2:업종지수+상위종목, 3:업종지수+하위종목)", example = "2", required = true)
    private String searchScope;

    @Schema(description = "종목개수 (상위/하위 종목 개수, 1-30)", example = "10", required = true)
    private String stockCount;

    @Override
    public SectorApiType getApiType() {
        return SectorApiType.SECTOR_INFO;
    }

    @Override
    public String getApiId() {
        return "ka20001";
    }

    @Override
    public void validate() {
        super.validate();
        
        // 업종코드 검증
        validateSectorCode(sectorCode);
        
        // 시장구분 검증
        validateMarketType(marketType);
        
        // 조회범위 검증
        if (searchScope == null || !searchScope.matches("[1-3]")) {
            throw new IllegalArgumentException("조회범위는 1(업종지수만), 2(업종지수+상위종목), 3(업종지수+하위종목) 중 하나여야 합니다: " + searchScope);
        }
        
        // 종목개수 검증
        if (stockCount == null || stockCount.trim().isEmpty()) {
            throw new IllegalArgumentException("종목개수는 필수입니다");
        }
        
        try {
            int count = Integer.parseInt(stockCount.trim());
            if (count < 1 || count > 30) {
                throw new IllegalArgumentException("종목개수는 1-30 사이여야 합니다: " + count);
            }
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("종목개수는 숫자여야 합니다: " + stockCount);
        }
    }
}