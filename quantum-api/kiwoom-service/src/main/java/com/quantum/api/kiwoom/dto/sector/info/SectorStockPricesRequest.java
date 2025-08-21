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
 * 업종별주가요청 DTO (ka20002)
 * 특정 업종에 속한 종목들의 주가 정보 조회
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(callSuper=false)
@Schema(description = "업종별주가요청 (ka20002)")
public class SectorStockPricesRequest extends BaseSectorRequest {

    @Schema(description = "업종코드 (3자리)", example = "001", required = true)
    private String sectorCode;

    @Schema(description = "시장구분 (0:코스피, 1:코스닥, 2:코스피200)", example = "0", required = true)
    private String marketType;

    @Schema(description = "정렬기준 (1:시가총액순, 2:거래대금순, 3:등락률순, 4:종목명순)", example = "1", required = true)
    private String sortType;

    @Schema(description = "정렬방향 (1:내림차순, 2:오름차순)", example = "1", required = true)
    private String sortOrder;

    @Schema(description = "조회개수 (1-100)", example = "50", required = true)
    private String stockCount;

    @Schema(description = "조회시작번호 (페이징용, 1부터 시작)", example = "1")
    private String startIndex;

    @Override
    public SectorApiType getApiType() {
        return SectorApiType.SECTOR_INFO;
    }

    @Override
    public String getApiId() {
        return "ka20002";
    }

    @Override
    public void validate() {
        super.validate();
        
        // 업종코드 검증
        validateSectorCode(sectorCode);
        
        // 시장구분 검증
        validateMarketType(marketType);
        
        // 정렬기준 검증
        if (sortType == null || !sortType.matches("[1-4]")) {
            throw new IllegalArgumentException("정렬기준은 1(시가총액순), 2(거래대금순), 3(등락률순), 4(종목명순) 중 하나여야 합니다: " + sortType);
        }
        
        // 정렬방향 검증
        if (sortOrder == null || !sortOrder.matches("[1-2]")) {
            throw new IllegalArgumentException("정렬방향은 1(내림차순), 2(오름차순) 중 하나여야 합니다: " + sortOrder);
        }
        
        // 조회개수 검증
        if (stockCount == null || stockCount.trim().isEmpty()) {
            throw new IllegalArgumentException("조회개수는 필수입니다");
        }
        
        try {
            int count = Integer.parseInt(stockCount.trim());
            if (count < 1 || count > 100) {
                throw new IllegalArgumentException("조회개수는 1-100 사이여야 합니다: " + count);
            }
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("조회개수는 숫자여야 합니다: " + stockCount);
        }
        
        // 조회시작번호 검증 (선택적)
        if (startIndex != null && !startIndex.trim().isEmpty()) {
            try {
                int index = Integer.parseInt(startIndex.trim());
                if (index < 1) {
                    throw new IllegalArgumentException("조회시작번호는 1 이상이어야 합니다: " + index);
                }
            } catch (NumberFormatException e) {
                throw new IllegalArgumentException("조회시작번호는 숫자여야 합니다: " + startIndex);
            }
        }
    }
}