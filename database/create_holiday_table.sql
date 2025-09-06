-- KIS API 국내 휴장일 정보 테이블 생성
CREATE TABLE IF NOT EXISTS kis_domestic_holidays (
    id SERIAL PRIMARY KEY,
    holiday_date DATE NOT NULL UNIQUE,          -- 기준일자 (YYYYMMDD)
    business_day_yn CHAR(1),                   -- 영업일여부 (Y/N)  
    trade_day_yn CHAR(1),                      -- 거래일여부 (Y/N)
    opening_day_yn CHAR(1),                    -- 개장일여부 (Y/N) 
    settlement_day_yn CHAR(1),                 -- 결제일여부 (Y/N)
    holiday_name VARCHAR(255),                 -- 휴일명 (만약 제공된다면)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_kis_domestic_holidays_date ON kis_domestic_holidays (holiday_date);
CREATE INDEX IF NOT EXISTS idx_kis_domestic_holidays_opening ON kis_domestic_holidays (opening_day_yn, holiday_date);

-- 업데이트 시간 자동 갱신 트리거
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_kis_domestic_holidays_updated_at 
    BEFORE UPDATE ON kis_domestic_holidays 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 코멘트 추가
COMMENT ON TABLE kis_domestic_holidays IS 'KIS API 국내 휴장일 정보';
COMMENT ON COLUMN kis_domestic_holidays.holiday_date IS '기준일자';
COMMENT ON COLUMN kis_domestic_holidays.business_day_yn IS '영업일여부 (Y/N)';
COMMENT ON COLUMN kis_domestic_holidays.trade_day_yn IS '거래일여부 (Y/N)';
COMMENT ON COLUMN kis_domestic_holidays.opening_day_yn IS '개장일여부 (Y/N) - 주문 가능 여부 확인용';
COMMENT ON COLUMN kis_domestic_holidays.settlement_day_yn IS '결제일여부 (Y/N)';