-- V1_6__Create_User_Kiwoom_Settings_Table.sql
-- 사용자별 키움증권 설정 테이블 생성

-- 사용자별 키움증권 설정 테이블
CREATE TABLE user_kiwoom_settings (
    user_id VARCHAR(100) PRIMARY KEY,
    default_real_mode BOOLEAN NOT NULL DEFAULT false,
    auto_refresh_enabled BOOLEAN NOT NULL DEFAULT true,
    token_expiry_notification BOOLEAN NOT NULL DEFAULT true,
    notification_threshold_minutes INTEGER NOT NULL DEFAULT 30,
    auto_reissue_on_mode_switch BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_mode_change_at TIMESTAMP WITH TIME ZONE,
    version BIGINT NOT NULL DEFAULT 1
);

-- 인덱스 생성
CREATE INDEX idx_user_kiwoom_settings_default_real_mode ON user_kiwoom_settings(default_real_mode);
CREATE INDEX idx_user_kiwoom_settings_updated_at ON user_kiwoom_settings(updated_at);
CREATE INDEX idx_user_kiwoom_settings_last_mode_change_at ON user_kiwoom_settings(last_mode_change_at);
CREATE INDEX idx_user_kiwoom_settings_auto_refresh ON user_kiwoom_settings(auto_refresh_enabled);
CREATE INDEX idx_user_kiwoom_settings_notification ON user_kiwoom_settings(token_expiry_notification);

-- 제약 조건 추가
ALTER TABLE user_kiwoom_settings 
ADD CONSTRAINT chk_notification_threshold 
CHECK (notification_threshold_minutes >= 5 AND notification_threshold_minutes <= 1440);

-- 트리거 함수: updated_at 자동 업데이트
CREATE OR REPLACE FUNCTION update_user_kiwoom_settings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    NEW.version = OLD.version + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 트리거 생성
CREATE TRIGGER trigger_user_kiwoom_settings_updated_at
    BEFORE UPDATE ON user_kiwoom_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_user_kiwoom_settings_updated_at();

-- 기본 설정 데이터 삽입 (기존 사용자들을 위한)
INSERT INTO user_kiwoom_settings (user_id, default_real_mode, auto_refresh_enabled, token_expiry_notification, notification_threshold_minutes, auto_reissue_on_mode_switch)
SELECT 
    u.username,
    false,  -- 기본값: 모의투자 모드
    true,   -- 자동 갱신 활성화
    true,   -- 만료 알림 활성화
    30,     -- 30분 전 알림
    true    -- 모드 전환 시 자동 재발급
FROM users u
WHERE u.username IS NOT NULL
ON CONFLICT (user_id) DO NOTHING;

-- 코멘트 추가
COMMENT ON TABLE user_kiwoom_settings IS '사용자별 키움증권 거래 설정';
COMMENT ON COLUMN user_kiwoom_settings.user_id IS '사용자 ID (users.username 참조)';
COMMENT ON COLUMN user_kiwoom_settings.default_real_mode IS '기본 거래 모드 (true: 실전투자, false: 모의투자)';
COMMENT ON COLUMN user_kiwoom_settings.auto_refresh_enabled IS '토큰 자동 갱신 활성화 여부';
COMMENT ON COLUMN user_kiwoom_settings.token_expiry_notification IS '토큰 만료 알림 활성화 여부';
COMMENT ON COLUMN user_kiwoom_settings.notification_threshold_minutes IS '토큰 만료 알림 임계시간 (분)';
COMMENT ON COLUMN user_kiwoom_settings.auto_reissue_on_mode_switch IS '모드 전환 시 자동 토큰 재발급 여부';
COMMENT ON COLUMN user_kiwoom_settings.last_mode_change_at IS '최근 모드 변경 시각';
COMMENT ON COLUMN user_kiwoom_settings.version IS '낙관적 잠금을 위한 버전';