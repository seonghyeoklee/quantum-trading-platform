-- ============================================================================
-- Quantum Trading Platform - Query Side Schema Definition
-- CQRS Read Model 테이블 스키마 정의 (JPA 자동생성 보완용)
-- ============================================================================

-- 확장 모듈 활성화 (PostgreSQL 고급 기능 사용)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- ENUM 타입 정의 (JPA가 자동 생성하지 않는 경우를 위한 백업)
-- ============================================================================

-- 주문 타입
DO $$ BEGIN
    CREATE TYPE order_type_enum AS ENUM ('MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 주문 방향
DO $$ BEGIN
    CREATE TYPE order_side_enum AS ENUM ('BUY', 'SELL');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 주문 상태
DO $$ BEGIN
    CREATE TYPE order_status_enum AS ENUM (
        'PENDING', 'SUBMITTED', 'PARTIALLY_FILLED', 
        'FILLED', 'CANCELLED', 'REJECTED', 'EXPIRED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- 테이블 코멘트 추가 (JPA 자동생성 후 실행)
-- ============================================================================

-- OrderView 테이블 코멘트
COMMENT ON TABLE order_view IS 'CQRS 주문 조회용 비정규화 테이블 - 읽기 최적화';
COMMENT ON COLUMN order_view.order_id IS '주문 고유 식별자';
COMMENT ON COLUMN order_view.user_id IS '사용자 식별자';
COMMENT ON COLUMN order_view.symbol IS '종목 코드 (6자리 한국 주식)';
COMMENT ON COLUMN order_view.order_type IS '주문 유형 (MARKET, LIMIT 등)';
COMMENT ON COLUMN order_view.side IS '매매 방향 (BUY, SELL)';
COMMENT ON COLUMN order_view.price IS '주문 가격 (원 단위)';
COMMENT ON COLUMN order_view.quantity IS '주문 수량 (주 단위)';
COMMENT ON COLUMN order_view.status IS '주문 상태';
COMMENT ON COLUMN order_view.broker_type IS '증권사 코드 (KIS, KIWOOM 등)';
COMMENT ON COLUMN order_view.broker_order_id IS '증권사 주문 번호';
COMMENT ON COLUMN order_view.filled_quantity IS '체결 수량';
COMMENT ON COLUMN order_view.filled_price IS '체결 가격';
COMMENT ON COLUMN order_view.total_amount IS '총 거래금액 (수수료 포함)';
COMMENT ON COLUMN order_view.fee IS '수수료';

-- PortfolioView 테이블 코멘트
COMMENT ON TABLE portfolio_view IS 'CQRS 포트폴리오 조회용 비정규화 테이블 - 읽기 최적화';
COMMENT ON COLUMN portfolio_view.portfolio_id IS '포트폴리오 고유 식별자';
COMMENT ON COLUMN portfolio_view.user_id IS '사용자 식별자 (고유)';
COMMENT ON COLUMN portfolio_view.cash_balance IS '현금 잔액 (원 단위)';
COMMENT ON COLUMN portfolio_view.total_invested IS '총 투자금액';
COMMENT ON COLUMN portfolio_view.total_market_value IS '총 평가금액';
COMMENT ON COLUMN portfolio_view.total_profit_loss IS '총 손익금액';
COMMENT ON COLUMN portfolio_view.profit_loss_percentage IS '수익률 (%)';
COMMENT ON COLUMN portfolio_view.position_count IS '보유 종목 수';

-- PositionView 테이블 코멘트
COMMENT ON TABLE position_view IS 'CQRS 포지션 조회용 비정규화 테이블 - 종목별 보유 현황';
COMMENT ON COLUMN position_view.symbol IS '종목 코드';
COMMENT ON COLUMN position_view.symbol_name IS '종목명 (한글)';
COMMENT ON COLUMN position_view.quantity IS '보유 수량 (주 단위)';
COMMENT ON COLUMN position_view.average_price IS '평균 단가 (원 단위)';
COMMENT ON COLUMN position_view.current_price IS '현재가 (원 단위)';
COMMENT ON COLUMN position_view.market_value IS '평가금액';
COMMENT ON COLUMN position_view.unrealized_pnl IS '미실현 손익';
COMMENT ON COLUMN position_view.unrealized_pnl_percentage IS '수익률 (%)';

-- ============================================================================
-- 제약조건 추가 (JPA 자동생성 보완)
-- ============================================================================

-- OrderView 제약조건
ALTER TABLE order_view ADD CONSTRAINT IF NOT EXISTS chk_order_view_price_positive 
    CHECK (price IS NULL OR price > 0);
    
ALTER TABLE order_view ADD CONSTRAINT IF NOT EXISTS chk_order_view_quantity_positive 
    CHECK (quantity > 0);
    
ALTER TABLE order_view ADD CONSTRAINT IF NOT EXISTS chk_order_view_filled_quantity_valid 
    CHECK (filled_quantity >= 0 AND (filled_quantity IS NULL OR filled_quantity <= quantity));

-- PortfolioView 제약조건
ALTER TABLE portfolio_view ADD CONSTRAINT IF NOT EXISTS chk_portfolio_view_cash_balance_non_negative 
    CHECK (cash_balance >= 0);
    
ALTER TABLE portfolio_view ADD CONSTRAINT IF NOT EXISTS chk_portfolio_view_position_count_non_negative 
    CHECK (position_count >= 0);

-- PositionView 제약조건
ALTER TABLE position_view ADD CONSTRAINT IF NOT EXISTS chk_position_view_quantity_positive 
    CHECK (quantity > 0);
    
ALTER TABLE position_view ADD CONSTRAINT IF NOT EXISTS chk_position_view_average_price_positive 
    CHECK (average_price > 0);

-- ============================================================================
-- 트리거 함수 정의 (자동 타임스탬프 업데이트)
-- ============================================================================

-- updated_at 자동 업데이트 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- OrderView updated_at 트리거
DROP TRIGGER IF EXISTS trigger_order_view_updated_at ON order_view;
CREATE TRIGGER trigger_order_view_updated_at
    BEFORE UPDATE ON order_view
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- PortfolioView updated_at 트리거
DROP TRIGGER IF EXISTS trigger_portfolio_view_updated_at ON portfolio_view;
CREATE TRIGGER trigger_portfolio_view_updated_at
    BEFORE UPDATE ON portfolio_view
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- PositionView last_updated 트리거
DROP TRIGGER IF EXISTS trigger_position_view_updated_at ON position_view;
CREATE TRIGGER trigger_position_view_updated_at
    BEFORE UPDATE ON position_view
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 뷰 정의 (복잡한 조회 쿼리 최적화)
-- ============================================================================

-- 사용자별 포트폴리오 요약 뷰
CREATE OR REPLACE VIEW user_portfolio_summary AS
SELECT 
    pv.user_id,
    pv.cash_balance,
    pv.total_invested,
    pv.total_market_value,
    pv.cash_balance + pv.total_market_value as total_portfolio_value,
    pv.total_profit_loss,
    pv.profit_loss_percentage,
    pv.position_count,
    COUNT(DISTINCT ov.order_id) FILTER (WHERE ov.status IN ('PENDING', 'SUBMITTED', 'PARTIALLY_FILLED')) as active_order_count,
    COUNT(DISTINCT ov.order_id) FILTER (WHERE ov.created_at >= CURRENT_DATE) as today_order_count
FROM portfolio_view pv
LEFT JOIN order_view ov ON pv.user_id = ov.user_id
GROUP BY pv.user_id, pv.cash_balance, pv.total_invested, pv.total_market_value, 
         pv.total_profit_loss, pv.profit_loss_percentage, pv.position_count;

-- 종목별 거래 요약 뷰
CREATE OR REPLACE VIEW symbol_trading_summary AS
SELECT 
    symbol,
    COUNT(*) as total_orders,
    COUNT(*) FILTER (WHERE side = 'BUY') as buy_orders,
    COUNT(*) FILTER (WHERE side = 'SELL') as sell_orders,
    COUNT(*) FILTER (WHERE status = 'FILLED') as filled_orders,
    AVG(price) FILTER (WHERE status = 'FILLED') as avg_filled_price,
    SUM(quantity) FILTER (WHERE status = 'FILLED' AND side = 'BUY') as total_buy_quantity,
    SUM(quantity) FILTER (WHERE status = 'FILLED' AND side = 'SELL') as total_sell_quantity,
    MAX(filled_at) as last_trade_time
FROM order_view 
WHERE symbol IS NOT NULL
GROUP BY symbol;

-- ============================================================================
-- 시퀀스 정의 (필요시 사용)
-- ============================================================================

-- 포지션 뷰 ID 시퀀스 (JPA GenerationType.IDENTITY 보완)
CREATE SEQUENCE IF NOT EXISTS position_view_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

-- ============================================================================
-- 권한 설정 (보안)
-- ============================================================================

-- 애플리케이션 사용자 권한 (실제 운영시 적절히 수정)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO quantum_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO quantum_user;

-- 스키마 초기화 완료 로그
SELECT 'Trading Query Schema Initialization Completed' AS status;