-- ===================================================================
-- V1.5: 사용자별 트레이딩 설정 및 시스템 설정 테이블 생성
-- ===================================================================

-- 사용자별 트레이딩 설정 테이블
CREATE TABLE user_trading_settings (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    trading_mode VARCHAR(20) NOT NULL DEFAULT 'SANDBOX', -- SANDBOX, PRODUCTION
    kiwoom_account_id VARCHAR(50), -- 키움계좌번호
    max_daily_amount DECIMAL(15,2) DEFAULT 1000000.00, -- 일일 최대 투자금액 (기본 100만원)
    risk_level VARCHAR(10) NOT NULL DEFAULT 'MEDIUM', -- LOW, MEDIUM, HIGH
    auto_trading_enabled BOOLEAN NOT NULL DEFAULT false,
    notifications_enabled BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- 트레이딩 모드 제약조건
ALTER TABLE user_trading_settings 
    ADD CONSTRAINT check_trading_mode 
    CHECK (trading_mode IN ('SANDBOX', 'PRODUCTION'));

-- 리스크 레벨 제약조건
ALTER TABLE user_trading_settings 
    ADD CONSTRAINT check_risk_level 
    CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH'));

-- 시스템 전역 트레이딩 설정 테이블
CREATE TABLE system_trading_config (
    config_key VARCHAR(100) PRIMARY KEY,
    config_value TEXT NOT NULL,
    config_type VARCHAR(20) NOT NULL DEFAULT 'STRING', -- STRING, NUMBER, BOOLEAN, JSON
    description TEXT,
    is_encrypted BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255)
);

-- 설정 타입 제약조건
ALTER TABLE system_trading_config 
    ADD CONSTRAINT check_config_type 
    CHECK (config_type IN ('STRING', 'NUMBER', 'BOOLEAN', 'JSON'));

-- 트레이딩 모드 변경 이력 테이블 (감사 로그)
CREATE TABLE trading_mode_history (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    previous_mode VARCHAR(20),
    new_mode VARCHAR(20) NOT NULL,
    changed_by VARCHAR(255) NOT NULL, -- 변경한 사용자 (자기 자신 또는 관리자)
    change_reason TEXT,
    ip_address VARCHAR(45), -- IPv6 지원
    user_agent TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_user_trading_settings_user_id ON user_trading_settings(user_id);
CREATE INDEX idx_user_trading_settings_trading_mode ON user_trading_settings(trading_mode);
CREATE INDEX idx_user_trading_settings_updated_at ON user_trading_settings(updated_at);

CREATE INDEX idx_system_trading_config_updated_at ON system_trading_config(updated_at);

CREATE INDEX idx_trading_mode_history_user_id ON trading_mode_history(user_id);
CREATE INDEX idx_trading_mode_history_created_at ON trading_mode_history(created_at);

-- 업데이트 시간 자동 갱신 트리거
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language plpgsql;

CREATE TRIGGER update_user_trading_settings_updated_at 
    BEFORE UPDATE ON user_trading_settings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_trading_config_updated_at 
    BEFORE UPDATE ON system_trading_config 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 기본 시스템 설정값 삽입
INSERT INTO system_trading_config (config_key, config_value, config_type, description) VALUES
('default_trading_mode', 'SANDBOX', 'STRING', '신규 사용자 기본 트레이딩 모드'),
('allow_production_mode', 'false', 'BOOLEAN', '실전투자 모드 허용 여부'),
('max_daily_amount_limit', '10000000.00', 'NUMBER', '일일 최대 투자금액 한도 (원)'),
('require_2fa_for_production', 'true', 'BOOLEAN', '실전투자 모드 전환 시 2FA 필수 여부'),
('trading_hours_start', '09:00:00', 'STRING', '트레이딩 허용 시작 시간'),
('trading_hours_end', '15:30:00', 'STRING', '트레이딩 허용 종료 시간'),
('python_adapter_notification_url', 'http://quantum-kiwoom-adapter:10201/api/v1/admin/user-trading-mode', 'STRING', 'Python 어댑터 모드 변경 알림 URL'),
('mode_change_cooldown_minutes', '60', 'NUMBER', '모드 변경 후 재변경 대기시간 (분)');

-- 코멘트 추가
COMMENT ON TABLE user_trading_settings IS '사용자별 트레이딩 설정 저장 테이블';
COMMENT ON TABLE system_trading_config IS '시스템 전역 트레이딩 설정 저장 테이블';
COMMENT ON TABLE trading_mode_history IS '트레이딩 모드 변경 이력 감사 로그 테이블';

COMMENT ON COLUMN user_trading_settings.trading_mode IS 'SANDBOX: 모의투자, PRODUCTION: 실전투자';
COMMENT ON COLUMN user_trading_settings.risk_level IS 'LOW: 보수적, MEDIUM: 중간, HIGH: 공격적';
COMMENT ON COLUMN user_trading_settings.max_daily_amount IS '일일 최대 투자금액 (원 단위)';
COMMENT ON COLUMN system_trading_config.is_encrypted IS '설정값 암호화 여부 (민감한 정보용)';