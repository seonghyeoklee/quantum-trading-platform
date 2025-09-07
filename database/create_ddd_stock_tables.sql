-- =====================================================
-- DDD 기반 주식 테이블 설계
-- kis_domestic_holidays는 제외하고 핵심 주식 테이블만 재설계
-- =====================================================

-- 기존 새 테이블들 삭제 (재생성 시)
DROP TABLE IF EXISTS overseas_stock_data CASCADE;
DROP TABLE IF EXISTS domestic_stock_data CASCADE;
DROP TABLE IF EXISTS overseas_stocks CASCADE;
DROP TABLE IF EXISTS domestic_stocks CASCADE;

-- =====================================================
-- 1. 국내주식종목 (domestic_stocks)
-- =====================================================
CREATE TABLE domestic_stocks (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    
    -- 기본 종목 정보
    stock_code VARCHAR(6) NOT NULL UNIQUE,     -- 종목코드 (005930)
    stock_name VARCHAR(100) NOT NULL,          -- 종목명 (삼성전자)
    market_type VARCHAR(10) NOT NULL,          -- 시장구분 (KOSPI/KOSDAQ)
    
    -- 추가 정보
    isin_code VARCHAR(12),                     -- ISIN 코드 (12자리)
    sector_code VARCHAR(6),                    -- 업종코드
    listing_date DATE,                         -- 상장일
    
    -- 원본 데이터 보존
    raw_data TEXT,                             -- 원본 고정길이 데이터
    
    -- 메타 정보
    is_active BOOLEAN DEFAULT TRUE,            -- 활성 상태
    created_at TIMESTAMP DEFAULT NOW(),        -- 생성 일시
    updated_at TIMESTAMP DEFAULT NOW(),        -- 수정 일시
    
    -- 제약조건
    CONSTRAINT chk_domestic_market_type CHECK (market_type IN ('KOSPI', 'KOSDAQ')),
    CONSTRAINT chk_domestic_stock_code_format CHECK (stock_code ~ '^[A-Z0-9]{6}$')
);

-- =====================================================
-- 2. 해외주식종목 (overseas_stocks)
-- =====================================================
CREATE TABLE overseas_stocks (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    
    -- 기본 종목 정보
    symbol VARCHAR(10) NOT NULL,               -- 종목 심볼 (AAPL, MSFT)
    stock_name_eng VARCHAR(200) NOT NULL,      -- 종목명 영어 (Apple Inc.)
    stock_name_kor VARCHAR(200),               -- 종목명 한국어 (애플)
    exchange VARCHAR(10) NOT NULL,             -- 거래소 (NAS, NYS, HKS 등)
    
    -- 해외 고유 필드
    country_code VARCHAR(3) NOT NULL DEFAULT 'US', -- 국가코드
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',    -- 통화
    stock_type VARCHAR(2),                     -- 종목타입 (2: 주식, 3: ETF)
    sector_code VARCHAR(3),                    -- 섹터코드
    
    -- 거래 정보
    tick_size DECIMAL(10,4),                   -- 호가단위
    lot_size INTEGER DEFAULT 1,                -- 거래단위
    trading_start_time VARCHAR(4),             -- 거래시작시간 (HHMM)
    trading_end_time VARCHAR(4),               -- 거래종료시간 (HHMM)
    
    -- 원본 데이터 보존
    raw_data TEXT,                             -- 원본 고정길이 데이터
    
    -- 메타 정보
    is_active BOOLEAN DEFAULT TRUE,            -- 활성 상태
    created_at TIMESTAMP DEFAULT NOW(),        -- 생성 일시
    updated_at TIMESTAMP DEFAULT NOW(),        -- 수정 일시
    
    -- 제약조건
    CONSTRAINT chk_overseas_exchange CHECK (exchange IN ('NAS', 'NYS', 'HKS', 'TSE', 'SHS', 'SZS')),
    CONSTRAINT chk_overseas_symbol_format CHECK (symbol ~ '^[A-Z0-9.-]+$'),
    UNIQUE(symbol, exchange)
);

-- =====================================================
-- 3. 국내주식정보 (domestic_stock_data)
-- =====================================================
CREATE TABLE domestic_stock_data (
    id BIGSERIAL PRIMARY KEY,
    
    -- 종목 참조 (외래키)
    stock_code VARCHAR(6) NOT NULL,            -- domestic_stocks 참조
    
    -- API 정보
    api_endpoint VARCHAR(100) NOT NULL,        -- 사용된 KIS API 엔드포인트
    data_type VARCHAR(20) NOT NULL,            -- 'price', 'chart', 'index'
    request_params JSONB,                      -- API 요청 파라미터
    request_timestamp TIMESTAMP NOT NULL,      -- API 호출 시간 (KST)
    
    -- KIS API 원본 응답 (핵심)
    raw_response JSONB NOT NULL,               -- 전체 KIS API JSON 응답
    
    -- 성능 최적화를 위한 추출 필드들
    response_code VARCHAR(10),                 -- rt_cd (0: 성공, 기타: 오류)
    current_price BIGINT,                      -- 현재가 (빠른 조회용)
    trade_date DATE,                           -- 거래일 (차트 데이터의 경우)
    volume BIGINT,                             -- 거래량 (빠른 조회용)
    
    -- 메타데이터
    created_at TIMESTAMP DEFAULT NOW(),        -- 레코드 생성 시간
    data_quality VARCHAR(20) DEFAULT 'GOOD',   -- 데이터 품질 추적
    
    -- 제약조건
    CONSTRAINT chk_domestic_data_type CHECK (data_type IN ('price', 'chart', 'index')),
    CONSTRAINT chk_domestic_data_quality CHECK (data_quality IN ('EXCELLENT', 'GOOD', 'FAIR', 'POOR')),
    
    -- 외래키
    FOREIGN KEY (stock_code) REFERENCES domestic_stocks(stock_code) ON DELETE CASCADE
);

-- =====================================================
-- 4. 해외주식정보 (overseas_stock_data)
-- =====================================================
CREATE TABLE overseas_stock_data (
    id BIGSERIAL PRIMARY KEY,
    
    -- 종목 참조 (외래키)
    symbol VARCHAR(10) NOT NULL,               -- overseas_stocks 참조
    exchange VARCHAR(10) NOT NULL,             -- 거래소 (overseas_stocks 참조)
    
    -- API 정보
    api_endpoint VARCHAR(100) NOT NULL,        -- 사용된 KIS API 엔드포인트
    data_type VARCHAR(20) NOT NULL,            -- 'price', 'chart', 'index'
    request_params JSONB,                      -- API 요청 파라미터
    request_timestamp TIMESTAMP NOT NULL,      -- API 호출 시간 (KST)
    
    -- KIS API 원본 응답 (핵심)
    raw_response JSONB NOT NULL,               -- 전체 KIS API JSON 응답
    
    -- 성능 최적화를 위한 추출 필드들
    response_code VARCHAR(10),                 -- rt_cd (0: 성공, 기타: 오류)
    current_price DECIMAL(15,2),               -- 현재가 USD (해외는 소수점)
    trade_date DATE,                           -- 거래일 (차트 데이터의 경우)
    volume BIGINT,                             -- 거래량 (빠른 조회용)
    
    -- 메타데이터
    created_at TIMESTAMP DEFAULT NOW(),        -- 레코드 생성 시간
    data_quality VARCHAR(20) DEFAULT 'GOOD',   -- 데이터 품질 추적
    
    -- 제약조건
    CONSTRAINT chk_overseas_data_type CHECK (data_type IN ('price', 'chart', 'index')),
    CONSTRAINT chk_overseas_data_quality CHECK (data_quality IN ('EXCELLENT', 'GOOD', 'FAIR', 'POOR')),
    
    -- 외래키
    FOREIGN KEY (symbol, exchange) REFERENCES overseas_stocks(symbol, exchange) ON DELETE CASCADE
);

-- =====================================================
-- 인덱스 생성 (성능 최적화)
-- =====================================================

-- 국내주식종목 인덱스
CREATE INDEX idx_domestic_stocks_code ON domestic_stocks(stock_code);
CREATE INDEX idx_domestic_stocks_market ON domestic_stocks(market_type);
CREATE INDEX idx_domestic_stocks_name ON domestic_stocks(stock_name);
CREATE INDEX idx_domestic_stocks_active ON domestic_stocks(is_active);

-- 해외주식종목 인덱스
CREATE INDEX idx_overseas_stocks_symbol ON overseas_stocks(symbol);
CREATE INDEX idx_overseas_stocks_exchange ON overseas_stocks(exchange);
CREATE INDEX idx_overseas_stocks_name_eng ON overseas_stocks(stock_name_eng);
CREATE INDEX idx_overseas_stocks_active ON overseas_stocks(is_active);
CREATE INDEX idx_overseas_stocks_symbol_exchange ON overseas_stocks(symbol, exchange);

-- 국내주식정보 인덱스
CREATE INDEX idx_domestic_data_stock_date ON domestic_stock_data(stock_code, trade_date DESC);
CREATE INDEX idx_domestic_data_stock_type ON domestic_stock_data(stock_code, data_type, request_timestamp DESC);
CREATE INDEX idx_domestic_data_timestamp ON domestic_stock_data(request_timestamp DESC);
CREATE INDEX idx_domestic_data_endpoint ON domestic_stock_data(api_endpoint, request_timestamp DESC);

-- JSONB 고성능 검색을 위한 GIN 인덱스
CREATE INDEX idx_domestic_data_raw_gin ON domestic_stock_data USING GIN (raw_response);
CREATE INDEX idx_domestic_data_params_gin ON domestic_stock_data USING GIN (request_params);

-- 해외주식정보 인덱스
CREATE INDEX idx_overseas_data_symbol_date ON overseas_stock_data(symbol, exchange, trade_date DESC);
CREATE INDEX idx_overseas_data_symbol_type ON overseas_stock_data(symbol, exchange, data_type, request_timestamp DESC);
CREATE INDEX idx_overseas_data_timestamp ON overseas_stock_data(request_timestamp DESC);
CREATE INDEX idx_overseas_data_endpoint ON overseas_stock_data(api_endpoint, request_timestamp DESC);

-- JSONB 고성능 검색을 위한 GIN 인덱스
CREATE INDEX idx_overseas_data_raw_gin ON overseas_stock_data USING GIN (raw_response);
CREATE INDEX idx_overseas_data_params_gin ON overseas_stock_data USING GIN (request_params);

-- =====================================================
-- 뷰 생성 (편의 기능)
-- =====================================================

-- 국내 최신 현재가 조회 뷰
CREATE OR REPLACE VIEW v_domestic_latest_prices AS
SELECT DISTINCT ON (d.stock_code)
    d.stock_code,
    s.stock_name,
    s.market_type,
    d.current_price,
    d.request_timestamp,
    d.raw_response->'output'->>'prdy_vrss' as price_change,
    d.raw_response->'output'->>'prdy_ctrt' as price_change_rate,
    d.volume
FROM domestic_stock_data d
JOIN domestic_stocks s ON d.stock_code = s.stock_code
WHERE d.data_type = 'price' 
  AND d.response_code = '0'
  AND d.data_quality IN ('EXCELLENT', 'GOOD')
  AND s.is_active = true
ORDER BY d.stock_code, d.request_timestamp DESC;

-- 해외 최신 현재가 조회 뷰
CREATE OR REPLACE VIEW v_overseas_latest_prices AS
SELECT DISTINCT ON (d.symbol, d.exchange)
    d.symbol,
    d.exchange,
    s.stock_name_eng,
    s.stock_name_kor,
    s.currency,
    d.current_price,
    d.request_timestamp,
    d.volume
FROM overseas_stock_data d
JOIN overseas_stocks s ON d.symbol = s.symbol AND d.exchange = s.exchange
WHERE d.data_type = 'price' 
  AND d.response_code = '0'
  AND d.data_quality IN ('EXCELLENT', 'GOOD')
  AND s.is_active = true
ORDER BY d.symbol, d.exchange, d.request_timestamp DESC;

-- =====================================================
-- 테이블 코멘트
-- =====================================================
COMMENT ON TABLE domestic_stocks IS '국내주식종목 - KOSPI/KOSDAQ 상장 종목 정보 (DDD 설계)';
COMMENT ON TABLE overseas_stocks IS '해외주식종목 - NYSE/NASDAQ 등 해외 상장 종목 정보 (DDD 설계)';
COMMENT ON TABLE domestic_stock_data IS '국내주식정보 - 국내 종목의 가격/차트 데이터 (DDD 설계)';
COMMENT ON TABLE overseas_stock_data IS '해외주식정보 - 해외 종목의 가격/차트 데이터 (DDD 설계)';

COMMENT ON VIEW v_domestic_latest_prices IS '국내 종목 최신 현재가 조회 뷰';
COMMENT ON VIEW v_overseas_latest_prices IS '해외 종목 최신 현재가 조회 뷰';

-- 초기 설정 완료 로그
SELECT 'DDD 기반 주식 테이블 생성 완료 - 4개 핵심 테이블' as status;