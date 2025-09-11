-- 디노 테스트 결과 및 Raw 데이터 저장 테이블 생성
-- 생성일: 2025-01-12
-- 목적: DINO 테스트 결과와 분석에 사용된 모든 Raw 데이터 저장

-- 1. 디노 테스트 결과 메인 테이블
CREATE TABLE IF NOT EXISTS dino_test_results (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    company_name VARCHAR(100),
    user_id BIGINT DEFAULT 1, -- 기본값: admin 사용자
    
    -- 9개 분석 영역 점수 (각 영역별 0-5점 또는 -1~+1점)
    finance_score INTEGER DEFAULT 0,           -- D001: 재무 분석 점수 (0-5)
    technical_score INTEGER DEFAULT 0,         -- 기술적 분석 점수 (0-5)
    price_score INTEGER DEFAULT 0,            -- 가격 분석 점수 (0-5)
    material_score INTEGER DEFAULT 0,         -- D003: 소재 분석 점수 (0-5)
    event_score INTEGER DEFAULT 0,            -- D001: 이벤트 분석 점수 (0 or 1)
    theme_score INTEGER DEFAULT 0,            -- D002: 테마 분석 점수 (0 or 1)
    positive_news_score INTEGER DEFAULT 0,    -- D008: 호재뉴스 도배 점수 (-1, 0, 1)
    interest_coverage_score INTEGER DEFAULT 0, -- D009: 이자보상배율 점수 (0-5)
    
    -- 종합 점수 (자동 계산) - 모든 점수의 합계
    total_score INTEGER GENERATED ALWAYS AS (
        finance_score + technical_score + price_score + material_score + 
        event_score + theme_score + positive_news_score + interest_coverage_score
    ) STORED,
    
    -- 분석 등급 (S, A, B, C, D)
    analysis_grade CHAR(1) DEFAULT 'C',
    
    -- 메타데이터
    analysis_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 분석 상태 (PENDING, RUNNING, COMPLETED, FAILED)
    status VARCHAR(20) DEFAULT 'PENDING',
    
    -- 유니크 제약: 종목코드 + 분석일자별 하루 1회 분석 보장
    CONSTRAINT uk_dino_test_daily UNIQUE (stock_code, analysis_date)
);

-- 2. 디노 테스트 Raw 데이터 저장 테이블
CREATE TABLE IF NOT EXISTS dino_test_raw_data (
    id BIGSERIAL PRIMARY KEY,
    dino_test_result_id BIGINT REFERENCES dino_test_results(id) ON DELETE CASCADE,
    
    -- 외부 API Raw 데이터 (JSONB 형태로 저장)
    news_raw_data JSONB,               -- 뉴스 API 원본 응답 데이터
    disclosure_raw_data JSONB,         -- DART 공시 API 원본 응답 데이터
    financial_raw_data JSONB,          -- KIS 재무 API 원본 응답 데이터
    technical_raw_data JSONB,          -- KIS 차트/기술적 분석 원본 데이터
    price_raw_data JSONB,              -- KIS 가격 분석 원본 데이터
    material_raw_data JSONB,           -- 소재 분석 관련 원본 데이터
    
    -- AI 분석 응답 원문 (Claude API 응답 전문)
    ai_theme_response TEXT,            -- Claude 테마 분석 응답 전문
    ai_news_response TEXT,             -- Claude 뉴스 분석 응답 전문
    ai_event_response TEXT,            -- Claude 이벤트 분석 응답 전문
    ai_positive_news_response TEXT,    -- Claude 호재뉴스 분석 응답 전문
    
    -- 분석 실행 환경 정보
    analysis_environment JSONB,        -- 분석 실행 시점의 환경 정보
    ai_model_info JSONB,              -- 사용된 AI 모델 정보
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_dino_results_stock_code ON dino_test_results(stock_code);
CREATE INDEX IF NOT EXISTS idx_dino_results_analysis_date ON dino_test_results(analysis_date);
CREATE INDEX IF NOT EXISTS idx_dino_results_total_score ON dino_test_results(total_score DESC);
CREATE INDEX IF NOT EXISTS idx_dino_results_status ON dino_test_results(status);

CREATE INDEX IF NOT EXISTS idx_dino_raw_result_id ON dino_test_raw_data(dino_test_result_id);

-- 4. 트리거 함수 생성 (분석 등급 자동 계산)
CREATE OR REPLACE FUNCTION calculate_dino_grade()
RETURNS TRIGGER AS $$
BEGIN
    -- 총점에 따른 등급 산정
    -- S: 35점 이상, A: 30-34점, B: 25-29점, C: 20-24점, D: 19점 이하
    IF NEW.total_score >= 35 THEN
        NEW.analysis_grade = 'S';
    ELSIF NEW.total_score >= 30 THEN
        NEW.analysis_grade = 'A';
    ELSIF NEW.total_score >= 25 THEN
        NEW.analysis_grade = 'B';
    ELSIF NEW.total_score >= 20 THEN
        NEW.analysis_grade = 'C';
    ELSE
        NEW.analysis_grade = 'D';
    END IF;
    
    -- updated_at 자동 갱신
    NEW.updated_at = CURRENT_TIMESTAMP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 5. 트리거 생성
DROP TRIGGER IF EXISTS trg_dino_grade_update ON dino_test_results;
CREATE TRIGGER trg_dino_grade_update
    BEFORE INSERT OR UPDATE ON dino_test_results
    FOR EACH ROW
    EXECUTE FUNCTION calculate_dino_grade();

-- 6. 테이블 코멘트 추가
COMMENT ON TABLE dino_test_results IS 'DINO 테스트 분석 결과 저장 테이블 - 하루 1회 분석 제한';
COMMENT ON TABLE dino_test_raw_data IS 'DINO 테스트 분석에 사용된 모든 Raw 데이터 저장';

COMMENT ON COLUMN dino_test_results.total_score IS '자동 계산되는 종합 점수 (모든 영역 점수 합계)';
COMMENT ON COLUMN dino_test_results.analysis_grade IS '자동 계산되는 분석 등급 (S/A/B/C/D)';
COMMENT ON COLUMN dino_test_raw_data.news_raw_data IS '뉴스 API 원본 응답 데이터 (JSONB)';
COMMENT ON COLUMN dino_test_raw_data.ai_theme_response IS 'Claude API 테마 분석 응답 전문';

-- 스크립트 실행 완료 메시지
SELECT 'DINO 테스트 테이블 생성 완료: dino_test_results, dino_test_raw_data' AS status;