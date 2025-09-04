-- =====================================================
-- 주식 분석 시스템 테이블 설계
-- 국내/해외, 섹터, 시장 등 다양한 분석 기반 지원
-- =====================================================

-- 1. 종목 마스터 테이블 (국내/해외 종목 정보)
DROP TABLE IF EXISTS stock_master CASCADE;
CREATE TABLE stock_master (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,        -- 종목코드 (005930, AAPL, etc)
    name VARCHAR(100) NOT NULL,                -- 종목명
    name_en VARCHAR(100),                      -- 영문명
    
    -- 시장 구분
    market_type VARCHAR(20) NOT NULL,          -- DOMESTIC, OVERSEAS
    exchange_code VARCHAR(10),                 -- KRX, KOSPI, KOSDAQ, NYSE, NASDAQ, etc
    market_cap_tier VARCHAR(20),               -- LARGE, MID, SMALL
    
    -- 섹터 정보
    sector_l1 VARCHAR(50),                     -- 대분류 (IT, 바이오, 금융, etc)
    sector_l2 VARCHAR(50),                     -- 중분류 (소프트웨어, 제약, 은행, etc)
    sector_l3 VARCHAR(50),                     -- 소분류
    industry VARCHAR(100),                     -- 업종
    
    -- 기본 정보
    country VARCHAR(10),                       -- KR, US, JP, CN, etc
    currency VARCHAR(10),                      -- KRW, USD, JPY, CNY, etc
    listing_date DATE,                         -- 상장일
    market_cap BIGINT,                         -- 시가총액
    
    -- 메타데이터
    is_active BOOLEAN DEFAULT TRUE,            -- 활성 여부
    last_updated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. 주식 분석 결과 테이블 (메인)
DROP TABLE IF EXISTS stock_analysis CASCADE;
CREATE TABLE stock_analysis (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    analyzed_date DATE NOT NULL,
    
    -- 기본 정보 (조인 최적화를 위한 비정규화)
    symbol_name VARCHAR(100),
    market_type VARCHAR(20),                   -- DOMESTIC, OVERSEAS
    exchange_code VARCHAR(10),
    sector_l1 VARCHAR(50),
    sector_l2 VARCHAR(50),
    country VARCHAR(10),
    
    -- 분석 결과 - 투자 평가
    investment_score DECIMAL(5,2),             -- 0-100 투자 적합성 점수
    recommendation VARCHAR(30),                -- 매수추천, 매수고려, 보유, 매수비추천
    risk_level VARCHAR(20),                    -- HIGH, MEDIUM, LOW
    confidence_level VARCHAR(20),              -- HIGH, MEDIUM, LOW
    
    -- 신호 정보
    signal_type VARCHAR(30),                   -- GOLDEN_CROSS, DEAD_CROSS, BREAKOUT, NONE
    signal_strength INTEGER,                   -- 0-100 신호 강도
    signal_confidence VARCHAR(20),             -- CONFIRMED, TENTATIVE, WEAK
    signal_confirmation_days INTEGER,          -- 최적 확정 기간 (1-7일)
    signal_reason TEXT,                        -- 신호 판단 근거
    
    -- 백테스팅 결과
    backtest_total_return DECIMAL(8,4),        -- 총 수익률
    backtest_annual_return DECIMAL(8,4),       -- 연간 수익률
    backtest_trades INTEGER,                   -- 거래 횟수
    backtest_win_rate DECIMAL(5,2),            -- 승률
    backtest_max_profit DECIMAL(6,2),          -- 최대 수익
    backtest_max_loss DECIMAL(6,2),            -- 최대 손실
    backtest_sharpe_ratio DECIMAL(6,3),        -- 샤프 비율
    backtest_vs_market DECIMAL(6,2),           -- 시장 대비 수익률
    backtest_period_days INTEGER,              -- 백테스팅 기간
    
    -- 현재 시장 데이터
    current_price BIGINT,                      -- 현재가
    price_change DECIMAL(8,2),                 -- 전일대비
    price_change_rate DECIMAL(5,2),            -- 전일대비율
    volume BIGINT,                             -- 거래량
    market_cap BIGINT,                         -- 시가총액
    
    -- 기술적 지표
    rsi DECIMAL(5,2),                          -- RSI
    sma5 BIGINT,                               -- 5일 이동평균
    sma20 BIGINT,                              -- 20일 이동평균
    sma60 BIGINT,                              -- 60일 이동평균
    sma120 BIGINT,                             -- 120일 이동평균
    ema12 BIGINT,                              -- 12일 지수이동평균
    ema26 BIGINT,                              -- 26일 지수이동평균
    macd DECIMAL(10,2),                        -- MACD
    macd_signal DECIMAL(10,2),                 -- MACD Signal
    macd_histogram DECIMAL(10,2),              -- MACD Histogram
    bollinger_upper BIGINT,                    -- 볼린저 상단
    bollinger_lower BIGINT,                    -- 볼린저 하단
    volatility DECIMAL(5,2),                   -- 변동성
    volume_ratio DECIMAL(5,2),                 -- 거래량 비율
    
    -- 펀더멘털 지표 (향후 확장)
    per DECIMAL(8,2),                          -- PER
    pbr DECIMAL(8,2),                          -- PBR
    roe DECIMAL(5,2),                          -- ROE
    debt_ratio DECIMAL(5,2),                   -- 부채비율
    
    -- 원본 분석 데이터 (JSON)
    raw_analysis JSONB,
    
    -- 메타데이터
    analysis_duration_ms INTEGER,              -- 분석 소요 시간
    data_source VARCHAR(20),                   -- PYKRX, FDR, YFINANCE, KIS
    data_quality VARCHAR(20),                  -- EXCELLENT, GOOD, FAIR, POOR
    data_period_days INTEGER,                  -- 분석 기간 (일)
    analysis_engine_version VARCHAR(20),       -- 분석 엔진 버전
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT unique_symbol_date UNIQUE(symbol, analyzed_date)
);

-- 3. 분석 히스토리 요약 테이블 (성능 최적화)
DROP TABLE IF EXISTS analysis_summary CASCADE;
CREATE TABLE analysis_summary (
    id BIGSERIAL PRIMARY KEY,
    
    -- 집계 기준
    summary_date DATE NOT NULL,
    market_type VARCHAR(20),                   -- DOMESTIC, OVERSEAS, ALL
    exchange_code VARCHAR(10),                 -- KRX, NYSE, NASDAQ, ALL
    sector_l1 VARCHAR(50),                     -- 섹터별 집계
    
    -- 집계 결과
    total_stocks INTEGER,                      -- 분석 종목 수
    avg_investment_score DECIMAL(5,2),         -- 평균 투자 점수
    median_investment_score DECIMAL(5,2),      -- 중간값 투자 점수
    
    -- 신호별 집계
    golden_cross_count INTEGER,               -- 골든크로스 종목 수
    dead_cross_count INTEGER,                 -- 데드크로스 종목 수
    no_signal_count INTEGER,                  -- 신호 없음 종목 수
    
    -- 추천별 집계
    buy_recommend_count INTEGER,              -- 매수추천 종목 수
    buy_consider_count INTEGER,               -- 매수고려 종목 수
    hold_count INTEGER,                       -- 보유 종목 수
    sell_recommend_count INTEGER,             -- 매수비추천 종목 수
    
    -- 백테스팅 집계
    avg_backtest_return DECIMAL(8,4),         -- 평균 백테스팅 수익률
    positive_return_rate DECIMAL(5,2),        -- 수익 종목 비율
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT unique_summary UNIQUE(summary_date, market_type, exchange_code, sector_l1)
);

-- 4. 종목별 관심도/인기도 테이블
DROP TABLE IF EXISTS stock_popularity CASCADE;
CREATE TABLE stock_popularity (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    
    -- 인기도 지표
    search_rank INTEGER,                       -- 검색 순위
    analysis_count INTEGER,                    -- 분석 요청 횟수
    watchlist_count INTEGER,                   -- 관심종목 등록 횟수
    
    -- 소셜 지표 (향후 확장)
    news_mention_count INTEGER,               -- 뉴스 언급 횟수
    social_sentiment DECIMAL(3,2),            -- 소셜 감정 점수 (-1 ~ 1)
    
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_stock_popularity UNIQUE(symbol, date)
);

-- =====================================================
-- 인덱스 생성 (성능 최적화)
-- =====================================================

-- stock_master 인덱스
CREATE INDEX idx_stock_master_market_type ON stock_master(market_type);
CREATE INDEX idx_stock_master_sector ON stock_master(sector_l1, sector_l2);
CREATE INDEX idx_stock_master_exchange ON stock_master(exchange_code);
CREATE INDEX idx_stock_master_country ON stock_master(country);

-- stock_analysis 인덱스
CREATE INDEX idx_analysis_date ON stock_analysis(analyzed_date);
CREATE INDEX idx_analysis_symbol_date ON stock_analysis(symbol, analyzed_date DESC);
CREATE INDEX idx_analysis_market_date ON stock_analysis(market_type, analyzed_date);
CREATE INDEX idx_analysis_sector_date ON stock_analysis(sector_l1, analyzed_date);
CREATE INDEX idx_analysis_exchange_date ON stock_analysis(exchange_code, analyzed_date);
CREATE INDEX idx_analysis_score ON stock_analysis(analyzed_date, investment_score DESC);
CREATE INDEX idx_analysis_signal ON stock_analysis(analyzed_date, signal_type) WHERE signal_type != 'NONE';
CREATE INDEX idx_analysis_recommendation ON stock_analysis(analyzed_date, recommendation);

-- 복합 인덱스 (자주 사용되는 쿼리 패턴)
CREATE INDEX idx_analysis_market_sector_score ON stock_analysis(analyzed_date, market_type, sector_l1, investment_score DESC);
CREATE INDEX idx_analysis_signal_score ON stock_analysis(analyzed_date, signal_type, signal_strength DESC) WHERE signal_type != 'NONE';

-- JSONB 인덱스 (원본 분석 데이터 검색용)
CREATE INDEX idx_analysis_raw_gin ON stock_analysis USING GIN (raw_analysis);

-- analysis_summary 인덱스
CREATE INDEX idx_summary_date ON analysis_summary(summary_date);
CREATE INDEX idx_summary_market ON analysis_summary(summary_date, market_type);
CREATE INDEX idx_summary_sector ON analysis_summary(summary_date, sector_l1);

-- =====================================================
-- 뷰 생성 (자주 사용하는 쿼리 최적화)
-- =====================================================

-- 최신 분석 결과 뷰
CREATE OR REPLACE VIEW v_latest_analysis AS
SELECT 
    sa.*,
    sm.name_en,
    sm.listing_date,
    sm.industry
FROM stock_analysis sa
JOIN stock_master sm ON sa.symbol = sm.symbol
WHERE sa.analyzed_date = (
    SELECT MAX(analyzed_date) 
    FROM stock_analysis sa2 
    WHERE sa2.symbol = sa.symbol
);

-- 섹터별 TOP 종목 뷰
CREATE OR REPLACE VIEW v_sector_top_stocks AS
SELECT 
    sector_l1,
    sector_l2,
    symbol,
    symbol_name,
    investment_score,
    recommendation,
    signal_type,
    ROW_NUMBER() OVER (PARTITION BY sector_l1 ORDER BY investment_score DESC) as sector_rank
FROM v_latest_analysis
WHERE investment_score IS NOT NULL;

-- 골든크로스 신호 종목 뷰
CREATE OR REPLACE VIEW v_golden_cross_signals AS
SELECT 
    sa.*,
    sm.sector_l1,
    sm.sector_l2,
    sm.market_cap_tier
FROM stock_analysis sa
JOIN stock_master sm ON sa.symbol = sm.symbol
WHERE sa.analyzed_date >= CURRENT_DATE - INTERVAL '7 days'
  AND sa.signal_type = 'GOLDEN_CROSS'
  AND sa.signal_confidence IN ('CONFIRMED', 'TENTATIVE')
ORDER BY sa.analyzed_date DESC, sa.signal_strength DESC;

-- =====================================================
-- 샘플 데이터 함수
-- =====================================================

-- 종목 마스터 데이터 삽입 함수
CREATE OR REPLACE FUNCTION insert_sample_stock_master()
RETURNS void AS $$
BEGIN
    -- 국내 주요 종목
    INSERT INTO stock_master (symbol, name, name_en, market_type, exchange_code, market_cap_tier, sector_l1, sector_l2, sector_l3, country, currency) VALUES
    ('005930', '삼성전자', 'Samsung Electronics', 'DOMESTIC', 'KRX', 'LARGE', 'IT', '반도체', '종합반도체', 'KR', 'KRW'),
    ('000660', 'SK하이닉스', 'SK Hynix', 'DOMESTIC', 'KRX', 'LARGE', 'IT', '반도체', '메모리반도체', 'KR', 'KRW'),
    ('035720', '카카오', 'Kakao', 'DOMESTIC', 'KRX', 'LARGE', 'IT', '인터넷서비스', '플랫폼', 'KR', 'KRW'),
    ('035420', 'NAVER', 'NAVER', 'DOMESTIC', 'KRX', 'LARGE', 'IT', '인터넷서비스', '포털', 'KR', 'KRW'),
    ('207940', '삼성바이오로직스', 'Samsung Biologics', 'DOMESTIC', 'KRX', 'LARGE', '바이오', '바이오의약품', 'CDMO', 'KR', 'KRW'),
    ('068270', '셀트리온', 'Celltrion', 'DOMESTIC', 'KRX', 'LARGE', '바이오', '바이오의약품', '항체의약품', 'KR', 'KRW'),
    ('373220', 'LG에너지솔루션', 'LG Energy Solution', 'DOMESTIC', 'KRX', 'LARGE', '전기전자', '2차전지', '리튬이온전지', 'KR', 'KRW'),
    ('051910', 'LG화학', 'LG Chem', 'DOMESTIC', 'KRX', 'LARGE', '화학', '종합화학', '석유화학', 'KR', 'KRW'),
    ('005380', '현대차', 'Hyundai Motor', 'DOMESTIC', 'KRX', 'LARGE', '자동차', '완성차', '승용차', 'KR', 'KRW'),
    ('012330', '현대모비스', 'Hyundai Mobis', 'DOMESTIC', 'KRX', 'LARGE', '자동차', '자동차부품', '자동차부품', 'KR', 'KRW'),
    
    -- 해외 주요 종목
    ('AAPL', 'Apple Inc', 'Apple Inc', 'OVERSEAS', 'NASDAQ', 'LARGE', 'Technology', 'Consumer Electronics', 'Smartphones', 'US', 'USD'),
    ('MSFT', 'Microsoft Corp', 'Microsoft Corp', 'OVERSEAS', 'NASDAQ', 'LARGE', 'Technology', 'Software', 'Operating Systems', 'US', 'USD'),
    ('GOOGL', 'Alphabet Inc', 'Alphabet Inc', 'OVERSEAS', 'NASDAQ', 'LARGE', 'Technology', 'Internet Services', 'Search Engine', 'US', 'USD'),
    ('TSLA', 'Tesla Inc', 'Tesla Inc', 'OVERSEAS', 'NASDAQ', 'LARGE', 'Consumer Cyclical', 'Auto Manufacturers', 'Electric Vehicles', 'US', 'USD'),
    ('NVDA', 'NVIDIA Corp', 'NVIDIA Corp', 'OVERSEAS', 'NASDAQ', 'LARGE', 'Technology', 'Semiconductors', 'Graphics Cards', 'US', 'USD'),
    ('AMZN', 'Amazon.com Inc', 'Amazon.com Inc', 'OVERSEAS', 'NASDAQ', 'LARGE', 'Consumer Cyclical', 'Internet Retail', 'E-commerce', 'US', 'USD'),
    ('META', 'Meta Platforms Inc', 'Meta Platforms Inc', 'OVERSEAS', 'NASDAQ', 'LARGE', 'Technology', 'Internet Services', 'Social Media', 'US', 'USD')
    
    ON CONFLICT (symbol) DO NOTHING;
    
    RAISE NOTICE 'Sample stock master data inserted successfully';
END;
$$ LANGUAGE plpgsql;

-- 샘플 데이터 삽입 실행
SELECT insert_sample_stock_master();

COMMENT ON TABLE stock_master IS '종목 마스터 테이블 - 국내/해외 모든 종목의 기본 정보';
COMMENT ON TABLE stock_analysis IS '주식 분석 결과 테이블 - 일별 종목 분석 데이터';
COMMENT ON TABLE analysis_summary IS '분석 요약 테이블 - 집계 데이터';
COMMENT ON TABLE stock_popularity IS '종목 인기도 테이블';