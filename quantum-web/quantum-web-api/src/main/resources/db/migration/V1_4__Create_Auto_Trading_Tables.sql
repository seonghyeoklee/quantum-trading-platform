-- 자동매매 설정 테이블 생성
CREATE TABLE auto_trading_configs (
    id VARCHAR(20) PRIMARY KEY,
    strategy_name VARCHAR(50) NOT NULL,
    symbol VARCHAR(6) NOT NULL,
    capital DECIMAL(15,2) NOT NULL,
    max_position_size INTEGER NOT NULL,
    stop_loss_percent DECIMAL(5,2) NOT NULL,
    take_profit_percent DECIMAL(5,2) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 자동매매 상태 테이블 생성
CREATE TABLE auto_trading_status (
    id VARCHAR(20) PRIMARY KEY,
    config_id VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    total_trades INTEGER NOT NULL DEFAULT 0,
    winning_trades INTEGER NOT NULL DEFAULT 0,
    total_profit DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    total_return DECIMAL(8,4) NOT NULL DEFAULT 0.0000,
    max_drawdown DECIMAL(8,4) NOT NULL DEFAULT 0.0000,
    started_at TIMESTAMP NULL,
    stopped_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 자동매매 설정 테이블 인덱스
CREATE INDEX idx_auto_trading_configs_strategy_symbol_active 
ON auto_trading_configs(strategy_name, symbol, is_active);

CREATE INDEX idx_auto_trading_configs_symbol_active 
ON auto_trading_configs(symbol, is_active);

CREATE INDEX idx_auto_trading_configs_created_at 
ON auto_trading_configs(created_at);

CREATE INDEX idx_auto_trading_configs_is_active 
ON auto_trading_configs(is_active);

-- 자동매매 상태 테이블 인덱스
CREATE INDEX idx_auto_trading_status_config_id 
ON auto_trading_status(config_id);

CREATE INDEX idx_auto_trading_status_status 
ON auto_trading_status(status);

CREATE INDEX idx_auto_trading_status_updated_at 
ON auto_trading_status(updated_at);

CREATE INDEX idx_auto_trading_status_total_return 
ON auto_trading_status(total_return);

CREATE INDEX idx_auto_trading_status_started_at 
ON auto_trading_status(started_at);

-- 외래키 제약 조건
ALTER TABLE auto_trading_status 
ADD CONSTRAINT fk_auto_trading_status_config_id 
FOREIGN KEY (config_id) REFERENCES auto_trading_configs(id) 
ON DELETE CASCADE;

-- 비즈니스 제약 조건
ALTER TABLE auto_trading_configs 
ADD CONSTRAINT chk_auto_trading_configs_symbol_format 
CHECK (symbol REGEXP '^[A-Z0-9]{6}$');

ALTER TABLE auto_trading_configs 
ADD CONSTRAINT chk_auto_trading_configs_capital_positive 
CHECK (capital > 0);

ALTER TABLE auto_trading_configs 
ADD CONSTRAINT chk_auto_trading_configs_position_size_range 
CHECK (max_position_size > 0 AND max_position_size <= 100);

ALTER TABLE auto_trading_configs 
ADD CONSTRAINT chk_auto_trading_configs_stop_loss_range 
CHECK (stop_loss_percent > 0 AND stop_loss_percent < 50);

ALTER TABLE auto_trading_configs 
ADD CONSTRAINT chk_auto_trading_configs_take_profit_range 
CHECK (take_profit_percent > 0 AND take_profit_percent < 100);

ALTER TABLE auto_trading_configs 
ADD CONSTRAINT chk_auto_trading_configs_profit_loss_relation 
CHECK (take_profit_percent > stop_loss_percent);

ALTER TABLE auto_trading_status 
ADD CONSTRAINT chk_auto_trading_status_status_values 
CHECK (status IN ('created', 'running', 'paused', 'stopped', 'error'));

ALTER TABLE auto_trading_status 
ADD CONSTRAINT chk_auto_trading_status_trades_positive 
CHECK (total_trades >= 0 AND winning_trades >= 0 AND winning_trades <= total_trades);

ALTER TABLE auto_trading_status 
ADD CONSTRAINT chk_auto_trading_status_drawdown_range 
CHECK (max_drawdown >= 0 AND max_drawdown <= 100);

-- 유니크 제약 조건 (동일 전략+종목에서 활성화된 설정은 하나만 허용)
CREATE UNIQUE INDEX idx_auto_trading_configs_unique_active 
ON auto_trading_configs(strategy_name, symbol) 
WHERE is_active = true;

-- 자동매매 설정별 상태는 하나만 허용
ALTER TABLE auto_trading_status 
ADD CONSTRAINT uk_auto_trading_status_config_id 
UNIQUE (config_id);

-- 테이블 코멘트
ALTER TABLE auto_trading_configs 
COMMENT = '자동매매 설정 정보를 저장하는 테이블';

ALTER TABLE auto_trading_status 
COMMENT = '자동매매 실행 상태 및 성과를 추적하는 테이블';

-- 컬럼 코멘트 (MySQL 5.7+ 지원)
ALTER TABLE auto_trading_configs 
MODIFY COLUMN id VARCHAR(20) COMMENT '자동매매 설정 고유 ID',
MODIFY COLUMN strategy_name VARCHAR(50) COMMENT '자동매매 전략명',
MODIFY COLUMN symbol VARCHAR(6) COMMENT '거래 종목 코드 (6자리)',
MODIFY COLUMN capital DECIMAL(15,2) COMMENT '투자 자본금',
MODIFY COLUMN max_position_size INTEGER COMMENT '최대 포지션 크기 (백분율)',
MODIFY COLUMN stop_loss_percent DECIMAL(5,2) COMMENT '손절 비율 (백분율)',
MODIFY COLUMN take_profit_percent DECIMAL(5,2) COMMENT '익절 비율 (백분율)',
MODIFY COLUMN is_active BOOLEAN COMMENT '활성화 여부',
MODIFY COLUMN created_at TIMESTAMP COMMENT '생성 일시',
MODIFY COLUMN updated_at TIMESTAMP COMMENT '수정 일시';

ALTER TABLE auto_trading_status 
MODIFY COLUMN id VARCHAR(20) COMMENT '자동매매 상태 고유 ID',
MODIFY COLUMN config_id VARCHAR(20) COMMENT '자동매매 설정 ID (외래키)',
MODIFY COLUMN status VARCHAR(20) COMMENT '현재 상태 (created/running/paused/stopped/error)',
MODIFY COLUMN total_trades INTEGER COMMENT '총 거래 횟수',
MODIFY COLUMN winning_trades INTEGER COMMENT '수익 거래 횟수',
MODIFY COLUMN total_profit DECIMAL(15,2) COMMENT '총 수익/손실 금액',
MODIFY COLUMN total_return DECIMAL(8,4) COMMENT '총 수익률 (백분율)',
MODIFY COLUMN max_drawdown DECIMAL(8,4) COMMENT '최대 낙폭 (백분율)',
MODIFY COLUMN started_at TIMESTAMP COMMENT '자동매매 시작 시각',
MODIFY COLUMN stopped_at TIMESTAMP COMMENT '자동매매 정지 시각',
MODIFY COLUMN created_at TIMESTAMP COMMENT '생성 일시',
MODIFY COLUMN updated_at TIMESTAMP COMMENT '수정 일시';