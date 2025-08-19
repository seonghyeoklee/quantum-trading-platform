-- ============================================================================
-- Quantum Trading Platform - Query Side Database Initialization
-- CQRS Read Model 테이블 초기화 및 인덱스 생성
-- ============================================================================

-- OrderView 테이블 인덱스 최적화
-- 사용자별 주문 조회 최적화
CREATE INDEX IF NOT EXISTS idx_order_view_user_id_created_at 
ON order_view (user_id, created_at DESC);

-- 종목별 주문 조회 최적화
CREATE INDEX IF NOT EXISTS idx_order_view_symbol_created_at 
ON order_view (symbol, created_at DESC);

-- 주문 상태별 조회 최적화
CREATE INDEX IF NOT EXISTS idx_order_view_status_created_at 
ON order_view (status, created_at DESC);

-- 사용자 + 상태별 조회 최적화
CREATE INDEX IF NOT EXISTS idx_order_view_user_status 
ON order_view (user_id, status, created_at DESC);

-- 브로커별 주문 조회 최적화
CREATE INDEX IF NOT EXISTS idx_order_view_broker_type 
ON order_view (broker_type, created_at DESC);

-- 브로커 주문 ID 조회 최적화
CREATE INDEX IF NOT EXISTS idx_order_view_broker_order_id 
ON order_view (broker_order_id) WHERE broker_order_id IS NOT NULL;

-- 체결 시간 기준 조회 최적화
CREATE INDEX IF NOT EXISTS idx_order_view_filled_at 
ON order_view (filled_at DESC) WHERE filled_at IS NOT NULL;

-- 사용자별 활성 주문 조회 최적화
CREATE INDEX IF NOT EXISTS idx_order_view_active_orders 
ON order_view (user_id, status, created_at DESC) 
WHERE status IN ('PENDING', 'SUBMITTED', 'PARTIALLY_FILLED');

-- PortfolioView 테이블 인덱스 최적화
-- 사용자별 포트폴리오 조회 (고유 인덱스)
CREATE UNIQUE INDEX IF NOT EXISTS idx_portfolio_view_user_id 
ON portfolio_view (user_id);

-- 수익률 기준 정렬 최적화
CREATE INDEX IF NOT EXISTS idx_portfolio_view_profit_loss_pct 
ON portfolio_view (profit_loss_percentage DESC) 
WHERE total_invested > 0;

-- 포트폴리오 규모 기준 정렬 최적화
CREATE INDEX IF NOT EXISTS idx_portfolio_view_total_value 
ON portfolio_view ((cash_balance + total_market_value) DESC);

-- 현금 잔액 기준 조회 최적화
CREATE INDEX IF NOT EXISTS idx_portfolio_view_cash_balance 
ON portfolio_view (cash_balance DESC);

-- 활성 포트폴리오 조회 최적화
CREATE INDEX IF NOT EXISTS idx_portfolio_view_active 
ON portfolio_view (position_count, cash_balance) 
WHERE position_count > 0 OR cash_balance > 0;

-- PositionView 테이블 인덱스 최적화
-- 포트폴리오별 포지션 조회 최적화
CREATE INDEX IF NOT EXISTS idx_position_view_portfolio_id 
ON position_view (portfolio_id, symbol);

-- 종목별 포지션 조회 최적화
CREATE INDEX IF NOT EXISTS idx_position_view_symbol 
ON position_view (symbol);

-- 수익률 기준 포지션 조회 최적화
CREATE INDEX IF NOT EXISTS idx_position_view_unrealized_pnl_pct 
ON position_view (unrealized_pnl_percentage DESC) 
WHERE unrealized_pnl_percentage IS NOT NULL;

-- 마지막 업데이트 시간 기준 조회 최적화
CREATE INDEX IF NOT EXISTS idx_position_view_last_updated 
ON position_view (last_updated DESC);

-- ============================================================================
-- 테스트용 초기 데이터 (개발 환경에서만 사용)
-- ============================================================================

-- 테스트 포트폴리오 생성 (실제 운영에서는 제거)
INSERT INTO portfolio_view (
    portfolio_id, user_id, cash_balance, 
    total_invested, total_market_value, total_profit_loss, profit_loss_percentage,
    position_count, created_at, updated_at, version
) VALUES (
    'PORTFOLIO-TEST-001', 'test-user-001', 1000000.00,
    0.00, 0.00, 0.00, 0.00,
    0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0
) ON CONFLICT (portfolio_id) DO NOTHING;

-- 테스트 주문 생성 (실제 운영에서는 제거)
INSERT INTO order_view (
    order_id, user_id, symbol, order_type, side, 
    price, quantity, status, 
    filled_quantity, created_at, updated_at, version
) VALUES (
    'ORDER-TEST-001', 'test-user-001', '005930', 'LIMIT', 'BUY',
    75000.00, 10, 'PENDING',
    0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0
) ON CONFLICT (order_id) DO NOTHING;

-- ============================================================================
-- 성능 최적화를 위한 VACUUM 및 ANALYZE
-- ============================================================================

-- 통계 정보 업데이트 (PostgreSQL 자동 실행되지만 명시적으로 실행)
ANALYZE order_view;
ANALYZE portfolio_view;
ANALYZE position_view;

-- ============================================================================
-- 파티셔닝 준비 (향후 대용량 데이터 처리용)
-- ============================================================================

-- 주문 테이블 월별 파티셔닝을 위한 함수 (향후 사용)
-- CREATE OR REPLACE FUNCTION create_monthly_partition_for_orders(table_date DATE)
-- RETURNS VOID AS $$
-- DECLARE
--     partition_name TEXT;
--     start_date DATE;
--     end_date DATE;
-- BEGIN
--     partition_name := 'order_view_' || to_char(table_date, 'YYYY_MM');
--     start_date := date_trunc('month', table_date);
--     end_date := start_date + interval '1 month';
--     
--     EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF order_view 
--                     FOR VALUES FROM (%L) TO (%L)', 
--                     partition_name, start_date, end_date);
-- END;
-- $$ LANGUAGE plpgsql;

-- 초기화 완료 로그
-- SELECT 'Trading Query Database Initialization Completed' AS status;