-- ========================================
-- 종목 마스터 테이블 생성 스크립트
-- 국내종목과 해외종목 스키마 분리
-- ========================================

-- 기존 테이블들 삭제 (있는 경우)
DROP TABLE IF EXISTS domestic_stock_master_temp CASCADE;
DROP TABLE IF EXISTS domestic_stock_master CASCADE;
DROP TABLE IF EXISTS overseas_stock_master_temp CASCADE;
DROP TABLE IF EXISTS overseas_stock_master CASCADE;
DROP TABLE IF EXISTS stock_master_temp CASCADE;
DROP TABLE IF EXISTS stock_master CASCADE;

-- ========================================
-- 국내 종목 마스터 테이블 (KOSPI, KOSDAQ)
-- ========================================
CREATE TABLE domestic_stock_master (
    -- 기본 키
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    
    -- 종목 정보 (국내 기준)
    stock_code VARCHAR(6) NOT NULL UNIQUE, -- 종목코드 (6자리)
    stock_name VARCHAR(100) NOT NULL, -- 종목명 (한국어)
    market_type VARCHAR(10) NOT NULL, -- 시장구분 (KOSPI/KOSDAQ)
    
    -- 국내 고유 필드
    isin_code VARCHAR(12), -- ISIN 코드 (12자리)
    sector_code VARCHAR(6), -- 업종코드
    listing_date DATE, -- 상장일
    
    -- 원본 데이터 필드 (고정길이 파싱용)
    raw_data TEXT, -- 원본 고정길이 데이터
    
    -- 관리 정보
    is_active BOOLEAN DEFAULT TRUE, -- 활성 상태
    created_at TIMESTAMP DEFAULT NOW(), -- 생성 일시
    updated_at TIMESTAMP DEFAULT NOW(), -- 수정 일시
    
    -- 제약조건
    CONSTRAINT chk_domestic_market_type CHECK (market_type IN ('KOSPI', 'KOSDAQ')),
    CONSTRAINT chk_domestic_stock_code_format CHECK (stock_code ~ '^[A-Z0-9]{6}$')
);

-- ========================================
-- 해외 종목 마스터 테이블 (NASDAQ, NYSE 등)
-- ========================================
CREATE TABLE overseas_stock_master (
    -- 기본 키
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    
    -- 종목 정보 (해외 기준)
    symbol VARCHAR(10) NOT NULL, -- 종목 심볼
    stock_name_eng VARCHAR(200) NOT NULL, -- 종목명 (영어)
    stock_name_kor VARCHAR(200), -- 종목명 (한국어)
    exchange VARCHAR(10) NOT NULL, -- 거래소 (NAS, NYS, HKS 등)
    
    -- 해외 고유 필드
    country_code VARCHAR(3) NOT NULL DEFAULT 'US', -- 국가코드
    currency VARCHAR(3) NOT NULL DEFAULT 'USD', -- 통화
    stock_type VARCHAR(2), -- 종목타입 (2: 주식, 3: ETF)
    sector_code VARCHAR(3), -- 섹터코드
    
    -- 거래 정보
    tick_size DECIMAL(10,4), -- 호가단위
    lot_size INTEGER DEFAULT 1, -- 거래단위
    trading_start_time VARCHAR(4), -- 거래시작시간 (HHMM)
    trading_end_time VARCHAR(4), -- 거래종료시간 (HHMM)
    
    -- 원본 데이터 필드 (고정길이 파싱용)
    raw_data TEXT, -- 원본 고정길이 데이터
    
    -- 관리 정보
    is_active BOOLEAN DEFAULT TRUE, -- 활성 상태
    created_at TIMESTAMP DEFAULT NOW(), -- 생성 일시
    updated_at TIMESTAMP DEFAULT NOW(), -- 수정 일시
    
    -- 제약조건
    CONSTRAINT chk_overseas_exchange CHECK (exchange IN ('NAS', 'NYS', 'HKS', 'TSE', 'SHS', 'SZS')),
    CONSTRAINT chk_overseas_symbol_format CHECK (symbol ~ '^[A-Z0-9.-]+$'),
    UNIQUE(symbol, exchange)
);

-- ========================================
-- 국내 종목 인덱스 생성
-- ========================================
CREATE INDEX idx_domestic_stock_code ON domestic_stock_master(stock_code);
CREATE INDEX idx_domestic_market_type ON domestic_stock_master(market_type);
CREATE INDEX idx_domestic_stock_name ON domestic_stock_master(stock_name);
CREATE INDEX idx_domestic_active ON domestic_stock_master(is_active);
CREATE INDEX idx_domestic_sector ON domestic_stock_master(sector_code);
CREATE INDEX idx_domestic_listing ON domestic_stock_master(listing_date);

-- ========================================
-- 해외 종목 인덱스 생성
-- ========================================
CREATE INDEX idx_overseas_symbol ON overseas_stock_master(symbol);
CREATE INDEX idx_overseas_exchange ON overseas_stock_master(exchange);
CREATE INDEX idx_overseas_stock_name_eng ON overseas_stock_master(stock_name_eng);
CREATE INDEX idx_overseas_stock_name_kor ON overseas_stock_master(stock_name_kor);
CREATE INDEX idx_overseas_active ON overseas_stock_master(is_active);
CREATE INDEX idx_overseas_country ON overseas_stock_master(country_code);
CREATE INDEX idx_overseas_sector ON overseas_stock_master(sector_code);
CREATE INDEX idx_overseas_symbol_exchange ON overseas_stock_master(symbol, exchange);

-- ========================================
-- 테이블 코멘트
-- ========================================
COMMENT ON TABLE domestic_stock_master IS '국내 종목 마스터 테이블 - KOSPI/KOSDAQ 전체 상장 종목 정보';
COMMENT ON TABLE overseas_stock_master IS '해외 종목 마스터 테이블 - NASDAQ/NYSE 등 해외 상장 종목 정보';

-- ========================================
-- 임시 테이블들 (데이터 적재용)
-- ========================================
-- 국내 종목 임시 테이블
CREATE TABLE IF NOT EXISTS domestic_stock_master_temp (
    LIKE domestic_stock_master INCLUDING ALL
);

-- 해외 종목 임시 테이블
CREATE TABLE IF NOT EXISTS overseas_stock_master_temp (
    LIKE overseas_stock_master INCLUDING ALL
);

COMMENT ON TABLE domestic_stock_master_temp IS '국내 종목 마스터 임시 테이블 - 데이터 적재 및 검증용';
COMMENT ON TABLE overseas_stock_master_temp IS '해외 종목 마스터 임시 테이블 - 데이터 적재 및 검증용';


-- ========================================
-- 통합 뷰 생성 (호환성 유지)
-- ========================================
CREATE VIEW stock_master_unified AS
SELECT 
    'DOMESTIC' as region,
    stock_code as symbol,
    stock_name as name,
    market_type,
    is_active,
    created_at,
    updated_at
FROM domestic_stock_master
UNION ALL
SELECT 
    'OVERSEAS' as region,
    symbol,
    COALESCE(stock_name_kor, stock_name_eng) as name,
    exchange as market_type,
    is_active,
    created_at,
    updated_at
FROM overseas_stock_master;

COMMENT ON VIEW stock_master_unified IS '국내/해외 종목 통합 뷰 - 기존 시스템 호환성 유지용';