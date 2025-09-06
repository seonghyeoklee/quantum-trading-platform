-- 기존 kis_holidays 테이블에서 kis_domestic_holidays로 데이터 마이그레이션
-- (혹시 기존 데이터가 있다면)

-- 1. 기존 데이터 백업 (있을 경우)
INSERT INTO kis_domestic_holidays (
    holiday_date, 
    business_day_yn, 
    trade_day_yn, 
    opening_day_yn, 
    settlement_day_yn, 
    holiday_name, 
    created_at, 
    updated_at
)
SELECT 
    holiday_date,
    business_day_yn, 
    trade_day_yn, 
    opening_day_yn, 
    settlement_day_yn, 
    holiday_name, 
    created_at, 
    updated_at
FROM kis_holidays
WHERE NOT EXISTS (
    SELECT 1 FROM kis_domestic_holidays kd 
    WHERE kd.holiday_date = kis_holidays.holiday_date
);

-- 2. 기존 테이블 삭제
DROP TABLE IF EXISTS kis_holidays CASCADE;