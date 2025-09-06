-- =====================================================
-- 기존 stock_* 테이블들 완전 삭제
-- 새로운 kis_market_data 구조로 전환 후 정리 작업
-- =====================================================

-- 안전을 위한 확인 메시지
DO $$
BEGIN
    RAISE NOTICE '기존 stock_* 테이블들을 삭제합니다...';
    RAISE NOTICE '새로운 kis_market_data 테이블을 사용하세요.';
END $$;

-- 기존 뷰들 삭제
DROP VIEW IF EXISTS v_latest_analysis CASCADE;
DROP VIEW IF EXISTS v_sector_top_stocks CASCADE;
DROP VIEW IF EXISTS v_golden_cross_signals CASCADE;

-- 기존 함수들 삭제
DROP FUNCTION IF EXISTS insert_sample_stock_master() CASCADE;
DROP FUNCTION IF EXISTS cleanup_old_duplicate_data() CASCADE;

-- 기존 테이블들 삭제 (CASCADE로 관련 인덱스도 함께 삭제)
DROP TABLE IF EXISTS stock_popularity CASCADE;
DROP TABLE IF EXISTS analysis_summary CASCADE;
DROP TABLE IF EXISTS stock_analysis CASCADE;
DROP TABLE IF EXISTS stock_master CASCADE;

-- 정리 완료 확인
DO $$
BEGIN
    RAISE NOTICE '기존 stock_* 테이블 삭제 완료!';
    RAISE NOTICE 'kis_market_data 테이블을 생성하려면 create_kis_market_data_table.sql을 실행하세요.';
END $$;