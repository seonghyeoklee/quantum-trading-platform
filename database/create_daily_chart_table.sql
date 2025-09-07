-- ====================================
-- 일봉 차트 데이터 테이블 생성 SQL
-- 백테스팅 및 차트 구현을 위한 전용 테이블
-- ====================================

-- 기존 테이블이 있으면 삭제 (개발 단계에서만 사용)
-- DROP TABLE IF EXISTS daily_chart_data CASCADE;

-- 일봉 차트 데이터 테이블 생성
CREATE TABLE IF NOT EXISTS daily_chart_data (
    id BIGSERIAL PRIMARY KEY,
    
    -- 종목 기본 정보
    stock_code VARCHAR(6) NOT NULL,                    -- 종목코드 (6자리)
    trade_date DATE NOT NULL,                          -- 거래일 (YYYY-MM-DD)
    
    -- OHLCV 핵심 데이터 (차트용)
    open_price DECIMAL(12,2) NOT NULL,                 -- 시가
    high_price DECIMAL(12,2) NOT NULL,                 -- 고가  
    low_price DECIMAL(12,2) NOT NULL,                  -- 저가
    close_price DECIMAL(12,2) NOT NULL,                -- 종가 (현재가)
    volume BIGINT NOT NULL DEFAULT 0,                  -- 거래량
    amount DECIMAL(18,2) DEFAULT 0,                    -- 거래대금
    
    -- 추가 시장 데이터
    price_change DECIMAL(12,2),                        -- 전일대비 가격변동
    price_change_rate DECIMAL(8,4),                    -- 전일대비 변동률 (%)
    market_cap DECIMAL(18,2),                          -- 시가총액 (optional)
    
    -- 메타데이터
    data_source VARCHAR(20) DEFAULT 'KIS_API',         -- 데이터 출처
    collection_method VARCHAR(20) DEFAULT 'BATCH',     -- 수집 방식
    data_quality VARCHAR(20) DEFAULT 'GOOD',           -- 데이터 품질 (EXCELLENT/GOOD/POOR)
    
    -- 시스템 필드
    created_at TIMESTAMP DEFAULT NOW(),                -- 생성일시
    updated_at TIMESTAMP DEFAULT NOW(),                -- 수정일시
    
    -- 복합 Primary Key (종목코드 + 거래일 고유성 보장)
    CONSTRAINT uk_daily_chart_stock_date UNIQUE (stock_code, trade_date),
    
    -- Foreign Key 제약조건 (domestic_stocks 테이블 참조)
    CONSTRAINT fk_daily_chart_stock 
        FOREIGN KEY (stock_code) 
        REFERENCES domestic_stocks(stock_code) 
        ON DELETE CASCADE ON UPDATE CASCADE,
        
    -- OHLC 관계 검증 제약조건
    CONSTRAINT chk_ohlc_relationship 
        CHECK (low_price <= open_price AND open_price <= high_price 
               AND low_price <= close_price AND close_price <= high_price
               AND low_price <= high_price),
               
    -- 양수 값 검증
    CONSTRAINT chk_positive_values
        CHECK (open_price > 0 AND high_price > 0 AND low_price > 0 
               AND close_price > 0 AND volume >= 0 AND amount >= 0)
);

-- 성능 최적화를 위한 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_daily_chart_stock_code ON daily_chart_data(stock_code);
CREATE INDEX IF NOT EXISTS idx_daily_chart_trade_date ON daily_chart_data(trade_date);
CREATE INDEX IF NOT EXISTS idx_daily_chart_stock_date ON daily_chart_data(stock_code, trade_date DESC);
CREATE INDEX IF NOT EXISTS idx_daily_chart_close_price ON daily_chart_data(close_price);
CREATE INDEX IF NOT EXISTS idx_daily_chart_volume ON daily_chart_data(volume DESC);

-- 파티셔닝 (대용량 데이터 처리용) - PostgreSQL 11+
-- 연도별 파티셔닝으로 쿼리 성능 향상
-- CREATE TABLE daily_chart_data_2024 PARTITION OF daily_chart_data
--     FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
-- CREATE TABLE daily_chart_data_2025 PARTITION OF daily_chart_data
--     FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

-- 테이블 코멘트
COMMENT ON TABLE daily_chart_data IS '일봉 차트 데이터 - 백테스팅 및 차트 구현용 전용 테이블';
COMMENT ON COLUMN daily_chart_data.stock_code IS '6자리 종목코드 (예: 005930=삼성전자)';
COMMENT ON COLUMN daily_chart_data.trade_date IS '거래일 (주말/공휴일 제외)';
COMMENT ON COLUMN daily_chart_data.open_price IS '시가 (당일 시작가격)';
COMMENT ON COLUMN daily_chart_data.high_price IS '고가 (당일 최고가격)';
COMMENT ON COLUMN daily_chart_data.low_price IS '저가 (당일 최저가격)';
COMMENT ON COLUMN daily_chart_data.close_price IS '종가 (당일 마감가격/현재가)';
COMMENT ON COLUMN daily_chart_data.volume IS '거래량 (주식 수)';
COMMENT ON COLUMN daily_chart_data.amount IS '거래대금 (원)';
COMMENT ON COLUMN daily_chart_data.data_quality IS 'EXCELLENT: 완전한 OHLCV, GOOD: 일부 누락, POOR: 추정값';

-- 권한 설정
GRANT SELECT, INSERT, UPDATE, DELETE ON daily_chart_data TO quantum;
GRANT USAGE, SELECT ON SEQUENCE daily_chart_data_id_seq TO quantum;

-- 테이블 생성 확인
SELECT 
    table_name, 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'daily_chart_data' 
ORDER BY ordinal_position;