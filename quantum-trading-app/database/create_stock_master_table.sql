-- 종목 마스터 테이블 생성
-- DINO 통합 분석 시스템의 종목 검색 기능을 위한 테이블
CREATE TABLE IF NOT EXISTS stock_master (
    stock_code VARCHAR(6) PRIMARY KEY COMMENT '6자리 종목코드 (예: 005930)',
    company_name VARCHAR(100) NOT NULL COMMENT '회사명 (예: 삼성전자)',
    company_name_en VARCHAR(100) COMMENT '영문 회사명',
    market_type VARCHAR(10) COMMENT '시장구분 (KOSPI/KOSDAQ)',
    sector VARCHAR(50) COMMENT '업종',
    is_active BOOLEAN DEFAULT TRUE COMMENT '상장여부',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시'
);

-- 회사명 검색을 위한 인덱스 (한글 검색 최적화)
CREATE INDEX IF NOT EXISTS idx_stock_master_company_name ON stock_master (company_name);

-- 시장구분별 검색을 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_stock_master_market_type ON stock_master (market_type);

-- 업종별 검색을 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_stock_master_sector ON stock_master (sector);

-- 활성 종목 검색을 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_stock_master_active ON stock_master (is_active);

-- 초기 주요 종목 데이터 삽입 (KOSPI 200 주요 종목)
INSERT INTO stock_master (stock_code, company_name, company_name_en, market_type, sector) VALUES
('005930', '삼성전자', 'Samsung Electronics Co., Ltd.', 'KOSPI', '전기전자'),
('000660', 'SK하이닉스', 'SK Hynix Inc.', 'KOSPI', '전기전자'),
('373220', 'LG에너지솔루션', 'LG Energy Solution, Ltd.', 'KOSPI', '전기전자'),
('207940', '삼성바이오로직스', 'Samsung Biologics Co., Ltd.', 'KOSPI', '의약품'),
('005935', '삼성전자우', 'Samsung Electronics Co., Ltd. Pref', 'KOSPI', '전기전자'),
('051910', 'LG화학', 'LG Chem, Ltd.', 'KOSPI', '화학'),
('006400', '삼성SDI', 'Samsung SDI Co., Ltd.', 'KOSPI', '전기전자'),
('035420', 'NAVER', 'NAVER Corporation', 'KOSPI', '서비스업'),
('005490', 'POSCO홀딩스', 'POSCO Holdings Inc.', 'KOSPI', '철강금속'),
('068270', '셀트리온', 'Celltrion, Inc.', 'KOSPI', '의약품'),
('105560', 'KB금융', 'KB Financial Group Inc.', 'KOSPI', '은행'),
('055550', '신한지주', 'Shinhan Financial Group Co., Ltd.', 'KOSPI', '은행'),
('035720', '카카오', 'Kakao Corp.', 'KOSPI', '서비스업'),
('003670', '포스코퓨처엠', 'POSCO Future M Co., Ltd.', 'KOSPI', '철강금속'),
('000270', '기아', 'Kia Corporation', 'KOSPI', '자동차부품'),
('012330', '현대모비스', 'Hyundai Mobis Co., Ltd.', 'KOSPI', '자동차부품'),
('017670', 'SK텔레콤', 'SK Telecom Co., Ltd.', 'KOSPI', '통신업'),
('096770', 'SK이노베이션', 'SK Innovation Co., Ltd.', 'KOSPI', '화학'),
('028260', '삼성물산', 'Samsung C&T Corporation', 'KOSPI', '건설업'),
('066570', 'LG전자', 'LG Electronics Inc.', 'KOSPI', '전기전자'),
('323410', '카카오뱅크', 'KakaoBank Corp.', 'KOSPI', '은행'),
('003550', 'LG', 'LG Corporation', 'KOSPI', '기타금융'),
('015760', '한국전력', 'Korea Electric Power Corporation', 'KOSPI', '전기가스업'),
('086790', '하나금융지주', 'Hana Financial Group Inc.', 'KOSPI', '은행'),
('018260', '삼성에스디에스', 'Samsung SDS Co., Ltd.', 'KOSPI', 'IT'),
('032830', '삼성생명', 'Samsung Life Insurance Co., Ltd.', 'KOSPI', '보험'),
('009150', '삼성전기', 'Samsung Electro-Mechanics Co., Ltd.', 'KOSPI', '전기전자'),
('010950', 'S-Oil', 'S-Oil Corporation', 'KOSPI', '화학'),
('161390', '한국타이어앤테크놀로지', 'Hankook Tire & Technology Co., Ltd.', 'KOSPI', '자동차부품'),
('047050', '포스코인터내셔널', 'POSCO International Corporation', 'KOSPI', '철강금속')
ON DUPLICATE KEY UPDATE
    company_name = VALUES(company_name),
    company_name_en = VALUES(company_name_en),
    market_type = VALUES(market_type),
    sector = VALUES(sector),
    updated_at = CURRENT_TIMESTAMP;

-- 테이블 생성 및 데이터 삽입 완료 확인
SELECT COUNT(*) as total_stocks FROM stock_master;