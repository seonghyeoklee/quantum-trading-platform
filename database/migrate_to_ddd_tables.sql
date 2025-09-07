-- =====================================================
-- 기존 테이블에서 DDD 기반 테이블로 데이터 마이그레이션
-- =====================================================

-- 마이그레이션 시작 로그
SELECT '데이터 마이그레이션 시작 - ' || NOW() as migration_start;

-- =====================================================
-- 1. 국내주식종목 마이그레이션 (domestic_stock_master → domestic_stocks)
-- =====================================================

INSERT INTO domestic_stocks (
    stock_code,
    stock_name,
    market_type,
    isin_code,
    sector_code,
    listing_date,
    raw_data,
    is_active,
    created_at,
    updated_at
)
SELECT 
    stock_code,
    stock_name,
    market_type,
    isin_code,
    sector_code,
    listing_date,
    raw_data,
    is_active,
    created_at,
    updated_at
FROM domestic_stock_master
WHERE is_active = true;

-- 마이그레이션 결과 확인
SELECT 'domestic_stocks 마이그레이션 완료: ' || COUNT(*) || '건' as domestic_result
FROM domestic_stocks;

-- =====================================================
-- 2. 해외주식종목 마이그레이션 (overseas_stock_master → overseas_stocks)
-- =====================================================

INSERT INTO overseas_stocks (
    symbol,
    stock_name_eng,
    stock_name_kor,
    exchange,
    country_code,
    currency,
    stock_type,
    sector_code,
    tick_size,
    lot_size,
    trading_start_time,
    trading_end_time,
    raw_data,
    is_active,
    created_at,
    updated_at
)
SELECT 
    symbol,
    stock_name_eng,
    stock_name_kor,
    exchange,
    country_code,
    currency,
    stock_type,
    sector_code,
    tick_size,
    lot_size,
    trading_start_time,
    trading_end_time,
    raw_data,
    is_active,
    created_at,
    updated_at
FROM overseas_stock_master
WHERE is_active = true;

-- 마이그레이션 결과 확인
SELECT 'overseas_stocks 마이그레이션 완료: ' || COUNT(*) || '건' as overseas_result
FROM overseas_stocks;

-- =====================================================
-- 3. 국내주식정보 마이그레이션 (kis_market_data → domestic_stock_data)
-- =====================================================

INSERT INTO domestic_stock_data (
    stock_code,
    api_endpoint,
    data_type,
    request_params,
    request_timestamp,
    raw_response,
    response_code,
    current_price,
    trade_date,
    volume,
    created_at,
    data_quality
)
SELECT 
    symbol as stock_code,                      -- symbol → stock_code로 변경
    api_endpoint,
    data_type,
    request_params,
    request_timestamp,
    raw_response,
    response_code,
    current_price,
    trade_date,
    volume,
    created_at,
    data_quality
FROM kis_market_data 
WHERE market_type = 'domestic'                 -- 국내 데이터만 추출
  AND symbol IN (                              -- 존재하는 종목만 마이그레이션
    SELECT stock_code FROM domestic_stocks
  );

-- 마이그레이션 결과 확인
SELECT 'domestic_stock_data 마이그레이션 완료: ' || COUNT(*) || '건' as domestic_data_result
FROM domestic_stock_data;

-- =====================================================
-- 4. 해외주식정보 마이그레이션 (kis_market_data → overseas_stock_data)
-- =====================================================

INSERT INTO overseas_stock_data (
    symbol,
    exchange,
    api_endpoint,
    data_type,
    request_params,
    request_timestamp,
    raw_response,
    response_code,
    current_price,
    trade_date,
    volume,
    created_at,
    data_quality
)
SELECT 
    k.symbol,
    COALESCE(o.exchange, 'NAS') as exchange,   -- 기본값으로 NASDAQ 설정
    k.api_endpoint,
    k.data_type,
    k.request_params,
    k.request_timestamp,
    k.raw_response,
    k.response_code,
    k.current_price,
    k.trade_date,
    k.volume,
    k.created_at,
    k.data_quality
FROM kis_market_data k
LEFT JOIN overseas_stocks o ON k.symbol = o.symbol  -- 해외주식종목과 조인
WHERE k.market_type = 'overseas'               -- 해외 데이터만 추출
  AND (k.symbol, COALESCE(o.exchange, 'NAS')) IN ( -- 존재하는 종목만 마이그레이션
    SELECT symbol, exchange FROM overseas_stocks
  );

-- 마이그레이션 결과 확인
SELECT 'overseas_stock_data 마이그레이션 완료: ' || COUNT(*) || '건' as overseas_data_result
FROM overseas_stock_data;

-- =====================================================
-- 5. 마이그레이션 결과 종합 확인
-- =====================================================

-- 전체 마이그레이션 결과 요약
SELECT 
    'domestic_stocks' as table_name,
    COUNT(*) as record_count,
    MIN(created_at) as oldest_record,
    MAX(updated_at) as newest_record
FROM domestic_stocks
UNION ALL
SELECT 
    'overseas_stocks' as table_name,
    COUNT(*) as record_count,
    MIN(created_at) as oldest_record,
    MAX(updated_at) as newest_record
FROM overseas_stocks
UNION ALL
SELECT 
    'domestic_stock_data' as table_name,
    COUNT(*) as record_count,
    MIN(created_at) as oldest_record,
    MAX(created_at) as newest_record
FROM domestic_stock_data
UNION ALL
SELECT 
    'overseas_stock_data' as table_name,
    COUNT(*) as record_count,
    MIN(created_at) as oldest_record,
    MAX(created_at) as newest_record
FROM overseas_stock_data;

-- =====================================================
-- 6. 데이터 무결성 검증
-- =====================================================

-- 국내주식정보의 외래키 무결성 검증
SELECT 
    '국내주식정보 외래키 검증: ' || 
    CASE 
        WHEN COUNT(*) = 0 THEN '✅ 모든 데이터가 유효함'
        ELSE '⚠️ ' || COUNT(*) || '건의 고아 레코드 발견'
    END as domestic_integrity_check
FROM domestic_stock_data d
LEFT JOIN domestic_stocks s ON d.stock_code = s.stock_code
WHERE s.stock_code IS NULL;

-- 해외주식정보의 외래키 무결성 검증  
SELECT 
    '해외주식정보 외래키 검증: ' ||
    CASE 
        WHEN COUNT(*) = 0 THEN '✅ 모든 데이터가 유효함'
        ELSE '⚠️ ' || COUNT(*) || '건의 고아 레코드 발견'
    END as overseas_integrity_check
FROM overseas_stock_data d
LEFT JOIN overseas_stocks s ON d.symbol = s.symbol AND d.exchange = s.exchange
WHERE s.symbol IS NULL;

-- =====================================================
-- 7. 인덱스 성능 확인
-- =====================================================

-- 주요 인덱스들이 제대로 생성되었는지 확인
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename IN ('domestic_stocks', 'overseas_stocks', 'domestic_stock_data', 'overseas_stock_data')
ORDER BY tablename, indexname;

-- =====================================================
-- 8. 마이그레이션 완료 로그
-- =====================================================

SELECT 
    '🎉 DDD 테이블 마이그레이션 완료 - ' || NOW() || 
    ' | 총 ' || (
        SELECT SUM(record_count)::TEXT FROM (
            SELECT COUNT(*) as record_count FROM domestic_stocks
            UNION ALL SELECT COUNT(*) FROM overseas_stocks  
            UNION ALL SELECT COUNT(*) FROM domestic_stock_data
            UNION ALL SELECT COUNT(*) FROM overseas_stock_data
        ) counts
    ) || '건 마이그레이션' 
as migration_complete;