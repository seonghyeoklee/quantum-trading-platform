-- ====================================
-- ETL: domestic_stocks_detail → daily_chart_data 마이그레이션
-- CHART 데이터를 차트 전용 테이블로 이관
-- ====================================

-- 1. 기존 daily_chart_data 테이블 데이터 백업 (혹시 모를 상황 대비)
-- CREATE TABLE daily_chart_data_backup AS SELECT * FROM daily_chart_data;

-- 2. 마이그레이션 실행
INSERT INTO daily_chart_data (
    stock_code,
    trade_date,
    open_price,
    high_price,
    low_price,
    close_price,
    volume,
    amount,
    price_change,
    price_change_rate,
    data_source,
    data_quality,
    created_at,
    updated_at
)
SELECT 
    dsd.stock_code,
    dsd.trade_date,
    
    -- OHLCV 데이터 추출 (parsed_ohlcv 또는 원본 데이터에서)
    COALESCE(
        (dsd.raw_response->'parsed_ohlcv'->>'open')::decimal(12,2),
        (dsd.raw_response->>'stck_oprc')::decimal(12,2)
    ) as open_price,
    
    COALESCE(
        (dsd.raw_response->'parsed_ohlcv'->>'high')::decimal(12,2),
        (dsd.raw_response->>'stck_hgpr')::decimal(12,2)
    ) as high_price,
    
    COALESCE(
        (dsd.raw_response->'parsed_ohlcv'->>'low')::decimal(12,2),
        (dsd.raw_response->>'stck_lwpr')::decimal(12,2)
    ) as low_price,
    
    COALESCE(
        (dsd.raw_response->'parsed_ohlcv'->>'close')::decimal(12,2),
        (dsd.raw_response->>'stck_clpr')::decimal(12,2),
        dsd.current_price
    ) as close_price,
    
    COALESCE(
        (dsd.raw_response->'parsed_ohlcv'->>'volume')::bigint,
        (dsd.raw_response->>'acml_vol')::bigint,
        dsd.volume
    ) as volume,
    
    COALESCE(
        (dsd.raw_response->'parsed_ohlcv'->>'amount')::decimal(18,2),
        (dsd.raw_response->>'acml_tr_pbmn')::decimal(18,2),
        0
    ) as amount,
    
    -- 전일대비 계산 (가능한 경우)
    COALESCE(
        (dsd.raw_response->>'prdy_vrss')::decimal(12,2),
        0
    ) as price_change,
    
    -- 변동률 계산 (전일대비 / 전일종가 * 100)
    CASE 
        WHEN (dsd.raw_response->>'prdy_vrss') IS NOT NULL 
             AND (dsd.raw_response->>'stck_clpr') IS NOT NULL
             AND (dsd.raw_response->>'stck_clpr')::decimal > (dsd.raw_response->>'prdy_vrss')::decimal
        THEN 
            ROUND(
                ((dsd.raw_response->>'prdy_vrss')::decimal / 
                 ((dsd.raw_response->>'stck_clpr')::decimal - (dsd.raw_response->>'prdy_vrss')::decimal)) * 100,
                4
            )
        ELSE 0.0000
    END as price_change_rate,
    
    -- 메타데이터
    'KIS_API' as data_source,
    CASE 
        WHEN dsd.data_quality = 'EXCELLENT' THEN 'EXCELLENT'
        WHEN dsd.data_quality = 'GOOD' THEN 'GOOD' 
        ELSE 'GOOD'
    END as data_quality,
    
    -- 시스템 필드
    dsd.created_at,
    NOW() as updated_at

FROM domestic_stocks_detail dsd
WHERE dsd.data_type = 'CHART'
  AND dsd.raw_response IS NOT NULL
  
-- 중복 방지 (이미 존재하는 데이터는 제외)
AND NOT EXISTS (
    SELECT 1 FROM daily_chart_data dcd 
    WHERE dcd.stock_code = dsd.stock_code 
      AND dcd.trade_date = dsd.trade_date
)

ORDER BY dsd.stock_code, dsd.trade_date;

-- 3. 마이그레이션 결과 확인
SELECT 
    '마이그레이션 완료!' as status,
    COUNT(*) as migrated_records,
    COUNT(DISTINCT stock_code) as unique_stocks,
    MIN(trade_date) as earliest_date,
    MAX(trade_date) as latest_date
FROM daily_chart_data;

-- 4. 데이터 품질 검증
SELECT 
    '데이터 품질 검증' as check_type,
    COUNT(*) as total_records,
    
    -- OHLC 관계 검증
    COUNT(*) FILTER (
        WHERE low_price <= open_price 
          AND open_price <= high_price 
          AND low_price <= close_price 
          AND close_price <= high_price
    ) as valid_ohlc_records,
    
    -- 양수 값 검증  
    COUNT(*) FILTER (
        WHERE open_price > 0 
          AND high_price > 0 
          AND low_price > 0 
          AND close_price > 0 
          AND volume >= 0
    ) as valid_positive_records,
    
    -- 데이터 완성도
    COUNT(*) FILTER (
        WHERE open_price IS NOT NULL 
          AND high_price IS NOT NULL 
          AND low_price IS NOT NULL 
          AND close_price IS NOT NULL 
          AND volume IS NOT NULL
    ) as complete_records

FROM daily_chart_data;

-- 5. 종목별 데이터 현황 (상위 10개 종목)
SELECT 
    '종목별 현황' as info_type,
    dcd.stock_code,
    ds.stock_name,
    COUNT(*) as days_count,
    MIN(dcd.trade_date) as first_date,
    MAX(dcd.trade_date) as last_date,
    ROUND(AVG(dcd.close_price), 2) as avg_price,
    MAX(dcd.close_price) as max_price,
    MIN(dcd.close_price) as min_price,
    SUM(dcd.volume) as total_volume
FROM daily_chart_data dcd
LEFT JOIN domestic_stocks ds ON dcd.stock_code = ds.stock_code
GROUP BY dcd.stock_code, ds.stock_name
ORDER BY days_count DESC, total_volume DESC
LIMIT 10;