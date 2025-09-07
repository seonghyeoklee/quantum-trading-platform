-- 기존 테이블 모두 삭제
-- DDD 리팩토링 전 레거시 테이블 제거

-- 기존 KIS 관련 테이블들
DROP TABLE IF EXISTS kis_market_data CASCADE;
DROP TABLE IF EXISTS kis_domestic_stock_master CASCADE;
DROP TABLE IF EXISTS kis_overseas_stock_master CASCADE;

-- 기존 stock_* 테이블들
DROP TABLE IF EXISTS stock_popularity CASCADE;
DROP TABLE IF EXISTS analysis_summary CASCADE;
DROP TABLE IF EXISTS stock_analysis CASCADE;
DROP TABLE IF EXISTS stock_master CASCADE;

-- 기존 히스토리 테이블들
DROP TABLE IF EXISTS domestic_stock_master_history CASCADE;
DROP TABLE IF EXISTS overseas_stock_master_history CASCADE;

-- 기존 API 사용량 테이블
DROP TABLE IF EXISTS kis_api_usage_log CASCADE;

-- 기존 뷰들 삭제
DROP VIEW IF EXISTS v_latest_analysis CASCADE;
DROP VIEW IF EXISTS v_sector_top_stocks CASCADE;
DROP VIEW IF EXISTS v_golden_cross_signals CASCADE;

-- 기존 함수들 삭제
DROP FUNCTION IF EXISTS insert_sample_stock_master() CASCADE;
DROP FUNCTION IF EXISTS cleanup_old_duplicate_data() CASCADE;

-- 기존 사용자/토큰 테이블들은 유지 (인증 시스템)
-- users, kis_accounts, kis_tokens 테이블은 삭제하지 않음

COMMIT;