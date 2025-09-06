-- =====================================================
-- KIS API 원시 데이터 저장 테이블 설계
-- 500+ 종목 대응, 완전한 원시 데이터 보존
-- =====================================================

-- 기존 테이블 삭제 (필요한 경우)
DROP TABLE IF EXISTS kis_market_data CASCADE;

-- KIS API 원시 데이터 통합 저장 테이블
CREATE TABLE kis_market_data (
    id BIGSERIAL PRIMARY KEY,
    
    -- ========== 기본 식별 정보 ==========
    symbol VARCHAR(20) NOT NULL,                    -- 종목코드 (005930, AAPL, etc)
    api_endpoint VARCHAR(100) NOT NULL,             -- 사용된 KIS API 엔드포인트
    data_type VARCHAR(20) NOT NULL,                 -- 'price', 'chart', 'index'
    market_type VARCHAR(20) NOT NULL,               -- 'domestic', 'overseas'
    
    -- ========== 요청 정보 ==========
    request_params JSONB,                           -- API 요청 파라미터 {"period": "D", "count": 100}
    request_timestamp TIMESTAMP NOT NULL,           -- API 호출 시간 (KST)
    
    -- ========== KIS API 원본 응답 (핵심) ==========
    raw_response JSONB NOT NULL,                    -- 전체 KIS API JSON 응답 (완전한 원시 데이터)
    
    -- ========== 성능 최적화를 위한 추출 필드들 ==========
    response_code VARCHAR(10),                      -- rt_cd (0: 성공, 기타: 오류)
    current_price BIGINT,                          -- 현재가 (빠른 조회용)
    trade_date DATE,                               -- 거래일 (차트 데이터의 경우)
    volume BIGINT,                                 -- 거래량 (빠른 조회용)
    
    -- ========== 메타데이터 ==========
    created_at TIMESTAMP DEFAULT NOW(),            -- 레코드 생성 시간
    data_quality VARCHAR(20) DEFAULT 'GOOD',       -- 데이터 품질 추적 (EXCELLENT, GOOD, FAIR, POOR)
    
    -- 제약 조건
    CONSTRAINT chk_data_type CHECK (data_type IN ('price', 'chart', 'index')),
    CONSTRAINT chk_market_type CHECK (market_type IN ('domestic', 'overseas')),
    CONSTRAINT chk_data_quality CHECK (data_quality IN ('EXCELLENT', 'GOOD', 'FAIR', 'POOR'))
);

-- =====================================================
-- 성능 최적화 인덱스 (500+ 종목 대응)
-- =====================================================

-- 주요 조회 패턴별 인덱스
CREATE INDEX idx_market_data_symbol_date ON kis_market_data(symbol, trade_date DESC);
CREATE INDEX idx_market_data_symbol_type ON kis_market_data(symbol, data_type, request_timestamp DESC);
CREATE INDEX idx_market_data_symbol_timestamp ON kis_market_data(symbol, request_timestamp DESC);
CREATE INDEX idx_market_data_endpoint ON kis_market_data(api_endpoint, request_timestamp DESC);
CREATE INDEX idx_market_data_type_date ON kis_market_data(data_type, trade_date DESC);

-- JSONB 고성능 검색을 위한 GIN 인덱스
CREATE INDEX idx_market_data_raw_gin ON kis_market_data USING GIN (raw_response);
CREATE INDEX idx_market_data_params_gin ON kis_market_data USING GIN (request_params);

-- 복합 조회 최적화 (자주 사용되는 패턴)
CREATE INDEX idx_market_data_symbol_type_date ON kis_market_data(symbol, data_type, trade_date DESC, request_timestamp DESC);
CREATE INDEX idx_market_data_recent_data ON kis_market_data(data_type, request_timestamp DESC) WHERE data_quality IN ('EXCELLENT', 'GOOD');

-- =====================================================
-- 유용한 뷰 및 함수
-- =====================================================

-- 최신 현재가 조회 뷰
CREATE OR REPLACE VIEW v_latest_prices AS
SELECT DISTINCT ON (symbol)
    symbol,
    current_price,
    request_timestamp,
    raw_response->'output'->>'prdy_vrss' as price_change,
    raw_response->'output'->>'prdy_ctrt' as price_change_rate,
    volume
FROM kis_market_data 
WHERE data_type = 'price' 
  AND response_code = '0'
  AND data_quality IN ('EXCELLENT', 'GOOD')
ORDER BY symbol, request_timestamp DESC;

-- 최신 차트 데이터 조회 함수
CREATE OR REPLACE FUNCTION get_latest_chart_data(
    p_symbol VARCHAR(20),
    p_period VARCHAR(10) DEFAULT 'D',
    p_days INTEGER DEFAULT 100
)
RETURNS TABLE (
    symbol VARCHAR(20),
    trade_date DATE,
    open_price BIGINT,
    high_price BIGINT,
    low_price BIGINT,
    close_price BIGINT,
    volume BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p_symbol as symbol,
        (chart_data->>'stck_bsop_date')::DATE as trade_date,
        (chart_data->>'stck_oprc')::BIGINT as open_price,
        (chart_data->>'stck_hgpr')::BIGINT as high_price,
        (chart_data->>'stck_lwpr')::BIGINT as low_price,
        (chart_data->>'stck_clpr')::BIGINT as close_price,
        (chart_data->>'acml_vol')::BIGINT as volume
    FROM kis_market_data,
         jsonb_array_elements(raw_response->'output2') as chart_data
    WHERE kis_market_data.symbol = p_symbol
      AND data_type = 'chart'
      AND response_code = '0'
      AND request_params->>'period' = p_period
    ORDER BY request_timestamp DESC, (chart_data->>'stck_bsop_date')::DATE DESC
    LIMIT p_days;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 데이터 정리 및 유지보수
-- =====================================================

-- 파티셔닝 준비 (월별 파티션)
-- 추후 대용량 데이터 처리 시 활성화
-- CREATE TABLE kis_market_data_y2024m12 PARTITION OF kis_market_data
-- FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');

-- 데이터 정리 함수 (30일 이전 중복 데이터 정리)
CREATE OR REPLACE FUNCTION cleanup_old_duplicate_data()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- 같은 심볼, 같은 타입, 같은 날짜의 중복 데이터 중 최신 것만 유지
    WITH ranked_data AS (
        SELECT id,
               ROW_NUMBER() OVER (
                   PARTITION BY symbol, data_type, trade_date 
                   ORDER BY request_timestamp DESC
               ) as rn
        FROM kis_market_data
        WHERE request_timestamp < NOW() - INTERVAL '30 days'
    )
    DELETE FROM kis_market_data
    WHERE id IN (
        SELECT id FROM ranked_data WHERE rn > 1
    );
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 테이블 정보 및 설명
-- =====================================================

COMMENT ON TABLE kis_market_data IS 'KIS API 원시 데이터 통합 저장 테이블 - 500+ 종목 지원';
COMMENT ON COLUMN kis_market_data.symbol IS '종목코드 (005930=삼성전자, AAPL=애플 등)';
COMMENT ON COLUMN kis_market_data.api_endpoint IS '사용된 KIS API 엔드포인트 경로';
COMMENT ON COLUMN kis_market_data.data_type IS '데이터 타입: price(현재가), chart(차트), index(지수)';
COMMENT ON COLUMN kis_market_data.raw_response IS 'KIS API 완전한 원시 JSON 응답 - 모든 데이터 보존';
COMMENT ON COLUMN kis_market_data.current_price IS '빠른 조회를 위해 추출된 현재가';
COMMENT ON COLUMN kis_market_data.trade_date IS '거래일 (차트 데이터용)';

-- 초기 설정 완료 로그
SELECT 'KIS Market Data Table 생성 완료 - 500+ 종목 대응 최적화' as status;