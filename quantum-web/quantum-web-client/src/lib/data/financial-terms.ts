// 금융 용어 사전 데이터베이스

export interface FinancialTerm {
  id: string;
  term: string;           // 용어명
  category: string;       // 카테고리
  definition: string;     // 정의
  description: string;    // 상세 설명
  formula?: string;       // 공식 (있는 경우)
  example?: string;       // 예시
  relatedTerms?: string[]; // 관련 용어 ID
  difficulty: 'beginner' | 'intermediate' | 'advanced'; // 난이도
  tags: string[];         // 태그
}

export const financialTerms: FinancialTerm[] = [
  // ===== 기본 용어 =====
  {
    id: 'stock_price',
    term: '주가',
    category: 'general',
    definition: '주식의 시장 가격',
    description: '주식시장에서 거래되는 한 주당 가격을 의미합니다. 수요와 공급에 따라 실시간으로 변동됩니다.',
    example: '삼성전자 주가가 71,400원이라면, 주식 1주를 사려면 71,400원이 필요합니다.',
    relatedTerms: ['market_cap', 'trading_volume'],
    difficulty: 'beginner',
    tags: ['가격', '기본', '시장']
  },
  {
    id: 'trading_volume',
    term: '거래량',
    category: 'trading',
    definition: '일정 기간 동안 거래된 주식의 수량',
    description: '보통 하루 동안 매매된 주식의 총 개수를 말합니다. 거래량이 많으면 관심이 높다는 의미입니다.',
    example: '거래량 1,000만주라면 하루에 1,000만주가 매매되었다는 뜻입니다.',
    relatedTerms: ['trading_value', 'liquidity'],
    difficulty: 'beginner',
    tags: ['거래', '수량', '활발성']
  },
  {
    id: 'trading_value',
    term: '거래대금',
    category: 'trading',
    definition: '일정 기간 동안 거래된 주식의 총 금액',
    description: '거래량에 주가를 곱한 값으로, 해당 종목에 실제로 투입된 자금의 규모를 나타냅니다.',
    formula: '거래대금 = 거래량 × 주가',
    example: '1,000만주가 평균 7만원에 거래되었다면 거래대금은 7,000억원입니다.',
    relatedTerms: ['trading_volume', 'market_cap'],
    difficulty: 'beginner',
    tags: ['거래', '금액', '규모']
  },
  {
    id: 'change_rate',
    term: '등락률',
    category: 'general',
    definition: '전일 대비 주가 변동률',
    description: '전일 종가와 현재가를 비교하여 백분율로 나타낸 변동률입니다. 양수면 상승, 음수면 하락을 의미합니다.',
    formula: '등락률 = ((현재가 - 전일종가) / 전일종가) × 100',
    example: '전일 7만원, 현재 7만1천원이면 등락률은 +1.43%입니다.',
    relatedTerms: ['change_amount', 'volatility'],
    difficulty: 'beginner',
    tags: ['변동', '비율', '등락']
  },

  // ===== 가격 정보 =====
  {
    id: 'open_price',
    term: '시가',
    category: 'market',
    definition: '장 시작 시 첫 거래 가격',
    description: '주식시장이 열리는 9시에 형성되는 첫 거래 가격입니다. 전일 종가와 다를 수 있습니다.',
    example: '9시에 삼성전자가 71,500원에 첫 거래되었다면 시가는 71,500원입니다.',
    relatedTerms: ['high_price', 'low_price', 'close_price'],
    difficulty: 'beginner',
    tags: ['가격', '시작', '개장']
  },
  {
    id: 'high_price',
    term: '고가',
    category: 'market',
    definition: '당일 거래된 최고 가격',
    description: '하루 중 가장 높았던 거래 가격입니다. 당일 매수 세력의 강도를 파악할 수 있습니다.',
    example: '하루 중 삼성전자가 최고 72,000원까지 올랐다면 고가는 72,000원입니다.',
    relatedTerms: ['open_price', 'low_price', 'close_price'],
    difficulty: 'beginner',
    tags: ['가격', '최고', '강세']
  },
  {
    id: 'low_price',
    term: '저가',
    category: 'market',
    definition: '당일 거래된 최저 가격',
    description: '하루 중 가장 낮았던 거래 가격입니다. 당일 매도 압력의 강도를 파악할 수 있습니다.',
    example: '하루 중 삼성전자가 최저 70,500원까지 떨어졌다면 저가는 70,500원입니다.',
    relatedTerms: ['open_price', 'high_price', 'close_price'],
    difficulty: 'beginner',
    tags: ['가격', '최저', '약세']
  },
  {
    id: 'close_price',
    term: '종가',
    category: 'market',
    definition: '장 마감 시 마지막 거래 가격',
    description: '주식시장이 마감되는 시점의 마지막 거래 가격입니다. 다음날 기준가가 됩니다.',
    example: '삼성전자가 71,200원에 장을 마감했다면 종가는 71,200원입니다.',
    relatedTerms: ['open_price', 'high_price', 'low_price'],
    difficulty: 'beginner',
    tags: ['가격', '마감', '기준']
  },
  {
    id: 'upper_limit',
    term: '상한가',
    category: 'trading',
    definition: '하루 중 오를 수 있는 최대 가격',
    description: '전일 종가 대비 30% 상승한 가격입니다. 상한가에 도달하면 더 이상 상승할 수 없습니다.',
    formula: '상한가 = 전일종가 × 1.3',
    example: '전일종가 7만원인 종목의 상한가는 91,000원입니다.',
    relatedTerms: ['lower_limit', 'circuit_breaker'],
    difficulty: 'beginner',
    tags: ['제한', '상승', '최대']
  },
  {
    id: 'lower_limit',
    term: '하한가',
    category: 'trading',
    definition: '하루 중 떨어질 수 있는 최저 가격',
    description: '전일 종가 대비 30% 하락한 가격입니다. 하한가에 도달하면 더 이상 하락할 수 없습니다.',
    formula: '하한가 = 전일종가 × 0.7',
    example: '전일종가 7만원인 종목의 하한가는 49,000원입니다.',
    relatedTerms: ['upper_limit', 'circuit_breaker'],
    difficulty: 'beginner',
    tags: ['제한', '하락', '최저']
  },
  {
    id: 'week52_high',
    term: '52주 최고가',
    category: 'market',
    definition: '지난 1년간 기록한 최고 주가',
    description: '최근 52주(약 1년) 동안 거래된 가격 중 가장 높은 가격입니다. 장기 추세를 파악하는 지표입니다.',
    example: '1년간 삼성전자 최고가가 85,000원이었다면 52주 최고가는 85,000원입니다.',
    relatedTerms: ['week52_low', 'resistance_level'],
    difficulty: 'intermediate',
    tags: ['장기', '최고', '추세']
  },
  {
    id: 'week52_low',
    term: '52주 최저가',
    category: 'market',
    definition: '지난 1년간 기록한 최저 주가',
    description: '최근 52주(약 1년) 동안 거래된 가격 중 가장 낮은 가격입니다. 장기 지지선 역할을 합니다.',
    example: '1년간 삼성전자 최저가가 55,000원이었다면 52주 최저가는 55,000원입니다.',
    relatedTerms: ['week52_high', 'support_level'],
    difficulty: 'intermediate',
    tags: ['장기', '최저', '지지']
  },

  // ===== 가치평가 지표 =====
  {
    id: 'per',
    term: 'PER (주가수익비율)',
    category: 'valuation',
    definition: '주가를 주당순이익으로 나눈 비율',
    description: 'Price Earnings Ratio의 줄임말로, 주가가 주당순이익의 몇 배인지를 나타내는 지표입니다. 기업의 수익성 대비 주가의 적정성을 판단하는 데 사용됩니다.',
    formula: 'PER = 주가 ÷ 주당순이익(EPS)',
    example: '주가가 50,000원이고 주당순이익이 2,500원이면, PER = 50,000 ÷ 2,500 = 20배입니다.',
    relatedTerms: ['eps', 'pbr', 'roe'],
    difficulty: 'beginner',
    tags: ['가치평가', 'PER', '수익성', '투자지표']
  },
  {
    id: 'pbr',
    term: 'PBR (주가순자산비율)',
    category: 'valuation',
    definition: '주가를 주당순자산으로 나눈 비율',
    description: 'Price Book-value Ratio의 줄임말로, 주가가 주당순자산의 몇 배인지를 나타내는 지표입니다. 기업의 자산가치 대비 주가의 적정성을 판단하는 데 사용됩니다.',
    formula: 'PBR = 주가 ÷ 주당순자산(BPS)',
    example: '주가가 50,000원이고 주당순자산이 25,000원이면, PBR = 50,000 ÷ 25,000 = 2배입니다.',
    relatedTerms: ['bps', 'per', 'book_value'],
    difficulty: 'beginner',
    tags: ['가치평가', 'PBR', '순자산', '투자지표']
  },
  {
    id: 'ev_ebitda',
    term: 'EV/EBITDA',
    category: 'valuation',
    definition: '기업가치를 세전영업이익으로 나눈 비율',
    description: 'Enterprise Value to EBITDA의 줄임말로, 기업의 전체 가치가 영업현금흐름의 몇 배인지를 나타내는 지표입니다. 부채를 고려한 기업가치 평가에 사용되며, 업종 간 비교에 유용합니다.',
    formula: 'EV/EBITDA = 기업가치(EV) ÷ EBITDA',
    example: '기업가치가 10조원이고 EBITDA가 1조원이라면, EV/EBITDA = 10 ÷ 1 = 10배입니다.',
    relatedTerms: ['per', 'pbr', 'enterprise_value', 'ebitda'],
    difficulty: 'advanced',
    tags: ['가치평가', 'EV/EBITDA', '기업가치', '투자지표', 'EBITDA']
  },
  {
    id: 'enterprise_value',
    term: 'EV (기업가치)',
    category: 'valuation',
    definition: '시가총액에 순부채를 더한 기업의 전체 가치',
    description: 'Enterprise Value의 줄임말로, 기업을 인수할 때 필요한 총 비용을 나타냅니다. 시가총액 + 총부채 - 현금으로 계산되며, 부채가 많은 기업의 진정한 가치를 평가할 때 유용합니다.',
    formula: 'EV = 시가총액 + 총부채 - 현금 및 현금성자산',
    example: '시가총액 100조원, 부채 20조원, 현금 5조원이라면, EV = 100 + 20 - 5 = 115조원입니다.',
    relatedTerms: ['market_cap', 'ev_ebitda', 'debt_ratio'],
    difficulty: 'intermediate',
    tags: ['가치평가', 'EV', '기업가치', '인수가치']
  },

  // ===== 수익성 지표 =====
  {
    id: 'eps',
    term: 'EPS (주당순이익)',
    category: 'profitability',
    definition: '기업의 순이익을 발행주식수로 나눈 값',
    description: 'Earnings Per Share의 줄임말로, 주식 1주당 얼마의 순이익을 벌어들이는지를 나타내는 지표입니다. 기업의 수익성을 평가하는 핵심 지표입니다.',
    formula: 'EPS = 순이익 ÷ 발행주식수',
    example: '순이익이 1,000억원이고 발행주식수가 4,000만주라면, EPS = 1,000억 ÷ 4,000만 = 2,500원입니다.',
    relatedTerms: ['per', 'roe', 'net_income'],
    difficulty: 'beginner',
    tags: ['수익성', 'EPS', '주당순이익', '투자지표']
  },
  {
    id: 'roe',
    term: 'ROE (자기자본이익률)',
    category: 'profitability',
    definition: '순이익을 자기자본으로 나눈 비율',
    description: 'Return On Equity의 줄임말로, 기업이 자기자본을 얼마나 효율적으로 활용하여 이익을 창출하는지를 나타내는 지표입니다.',
    formula: 'ROE = 순이익 ÷ 자기자본 × 100',
    example: '순이익이 1,000억원이고 자기자본이 5,000억원이라면, ROE = 1,000 ÷ 5,000 × 100 = 20%입니다.',
    relatedTerms: ['eps', 'per', 'roa'],
    difficulty: 'intermediate',
    tags: ['수익성', 'ROE', '자기자본이익률', '투자지표']
  },
  {
    id: 'ebitda',
    term: 'EBITDA',
    category: 'profitability',
    definition: '이자, 세금, 감가상각비 차감 전 영업이익',
    description: 'Earnings Before Interest, Taxes, Depreciation and Amortization의 줄임말로, 기업의 순수한 영업 성과를 나타내는 지표입니다. 회계 처리 방법이나 자본구조의 영향을 배제하고 기업의 본업 수익성을 평가할 수 있습니다.',
    formula: 'EBITDA = 영업이익 + 감가상각비 + 무형자산상각비',
    example: '영업이익 8,000억원, 감가상각비 1,500억원, 무형자산상각비 500억원이라면, EBITDA = 8,000 + 1,500 + 500 = 10,000억원입니다.',
    relatedTerms: ['ev_ebitda', 'operating_income', 'depreciation'],
    difficulty: 'advanced',
    tags: ['수익성', 'EBITDA', '영업이익', '현금흐름']
  },
  {
    id: 'roa',
    term: 'ROA (총자산이익률)',
    category: 'profitability',
    definition: '순이익을 총자산으로 나눈 비율',
    description: 'Return On Assets의 줄임말로, 기업이 보유한 자산을 얼마나 효율적으로 활용하여 이익을 창출하는지를 나타내는 지표입니다.',
    formula: 'ROA = 순이익 ÷ 총자산 × 100',
    example: '순이익이 1,000억원이고 총자산이 10,000억원이라면, ROA = 1,000 ÷ 10,000 × 100 = 10%입니다.',
    relatedTerms: ['roe', 'eps', 'asset_turnover'],
    difficulty: 'intermediate',
    tags: ['수익성', 'ROA', '총자산이익률', '효율성']
  },
  {
    id: 'operating_margin',
    term: '영업이익률',
    category: 'profitability',
    definition: '영업이익을 매출액으로 나눈 비율',
    description: '기업이 본업에서 얼마나 효율적으로 이익을 창출하는지를 나타내는 지표입니다. 높을수록 본업의 수익성이 좋다는 의미입니다.',
    formula: '영업이익률 = 영업이익 ÷ 매출액 × 100',
    example: '영업이익 2,000억원, 매출액 10,000억원이라면 영업이익률은 20%입니다.',
    relatedTerms: ['net_margin', 'gross_margin'],
    difficulty: 'intermediate',
    tags: ['수익성', '영업이익률', '마진']
  },

  // ===== 재무건전성 지표 =====
  {
    id: 'bps',
    term: 'BPS (주당순자산)',
    category: 'financial_health',
    definition: '기업의 순자산을 발행주식수로 나눈 값',
    description: 'Book-value Per Share의 줄임말로, 주식 1주당 순자산의 가치를 나타내는 지표입니다. 기업이 청산될 때 주주가 받을 수 있는 이론적 가치입니다.',
    formula: 'BPS = 순자산(자본총계) ÷ 발행주식수',
    example: '순자산이 10조원이고 발행주식수가 4억주라면, BPS = 10조 ÷ 4억 = 25,000원입니다.',
    relatedTerms: ['pbr', 'book_value', 'equity'],
    difficulty: 'beginner',
    tags: ['재무건전성', 'BPS', '주당순자산', '투자지표']
  },
  {
    id: 'debt_ratio',
    term: '부채비율',
    category: 'financial_health',
    definition: '부채를 자기자본으로 나눈 비율',
    description: '기업의 재무 안정성을 나타내는 지표로, 낮을수록 재무구조가 건전하다고 평가됩니다.',
    formula: '부채비율 = 부채총계 ÷ 자기자본 × 100',
    example: '부채 5,000억원, 자기자본 10,000억원이라면 부채비율은 50%입니다.',
    relatedTerms: ['equity_ratio', 'current_ratio'],
    difficulty: 'intermediate',
    tags: ['재무건전성', '부채비율', '안정성']
  },
  {
    id: 'current_ratio',
    term: '유동비율',
    category: 'financial_health',
    definition: '유동자산을 유동부채로 나눈 비율',
    description: '단기적인 채무 상환 능력을 나타내는 지표입니다. 일반적으로 200% 이상이면 안전하다고 평가됩니다.',
    formula: '유동비율 = 유동자산 ÷ 유동부채 × 100',
    example: '유동자산 3,000억원, 유동부채 1,500억원이라면 유동비율은 200%입니다.',
    relatedTerms: ['quick_ratio', 'debt_ratio'],
    difficulty: 'intermediate',
    tags: ['재무건전성', '유동비율', '단기안정성']
  },

  // ===== 시장 지표 =====
  {
    id: 'market_cap',
    term: '시가총액',
    category: 'market',
    definition: '기업의 총 주식 가치',
    description: '기업이 발행한 모든 주식의 시장가격 총합으로, 기업의 시장에서의 총 가치를 나타냅니다.',
    formula: '시가총액 = 주가 × 발행주식수',
    example: '주가가 70,000원이고 발행주식수가 6억주라면, 시가총액 = 70,000 × 6억 = 420조원입니다.',
    relatedTerms: ['stock_price', 'trading_volume'],
    difficulty: 'beginner',
    tags: ['시장지표', '시가총액', '기업가치']
  },
  {
    id: 'foreign_ownership',
    term: '외국인지분율',
    category: 'market',
    definition: '전체 주식 중 외국인이 보유한 비율',
    description: '외국인 투자자들이 해당 기업 주식을 얼마나 보유하고 있는지를 나타내는 지표입니다. 외국인 관심도와 글로벌 투자매력도를 가늠할 수 있습니다.',
    example: '전체 주식의 52%를 외국인이 보유하고 있다면 외국인지분율은 52%입니다.',
    relatedTerms: ['market_cap', 'institutional_ownership'],
    difficulty: 'beginner',
    tags: ['시장지표', '외국인', '지분율']
  },
  {
    id: 'beta',
    term: '베타 (β)',
    category: 'market',
    definition: '시장 대비 주가 민감도',
    description: '개별 주식의 가격 변동이 시장 전체의 변동에 얼마나 민감하게 반응하는지를 나타내는 지표입니다. 1보다 크면 시장보다 변동이 크고, 작으면 변동이 작습니다.',
    formula: 'β = 개별 주식과 시장의 공분산 ÷ 시장의 분산',
    example: '베타가 1.2라면 시장이 10% 오를 때 해당 주식은 12% 오른다는 의미입니다.',
    relatedTerms: ['volatility', 'correlation'],
    difficulty: 'advanced',
    tags: ['시장지표', '베타', '민감도', '위험']
  },

  // ===== 차트 분석 용어 =====
  {
    id: 'support_level',
    term: '지지선',
    category: 'general',
    definition: '주가 하락을 막아주는 가격대',
    description: '주가가 하락하다가 매수세가 나타나면서 더 이상 떨어지지 않는 가격 수준입니다.',
    example: '7만원 근처에서 계속 반등한다면 7만원이 지지선 역할을 한다고 봅니다.',
    relatedTerms: ['resistance_level', 'breakout'],
    difficulty: 'intermediate',
    tags: ['차트', '지지', '기술분석']
  },
  {
    id: 'resistance_level',
    term: '저항선',
    category: 'general',
    definition: '주가 상승을 막는 가격대',
    description: '주가가 상승하다가 매도세가 나타나면서 더 이상 오르지 못하는 가격 수준입니다.',
    example: '8만원 근처에서 계속 하락한다면 8만원이 저항선 역할을 한다고 봅니다.',
    relatedTerms: ['support_level', 'breakout'],
    difficulty: 'intermediate',
    tags: ['차트', '저항', '기술분석']
  },
  {
    id: 'moving_average',
    term: '이동평균선',
    category: 'general',
    definition: '일정 기간의 평균 주가를 연결한 선',
    description: '과거 일정 기간의 주가를 평균 내어 연결한 선으로, 추세를 파악하는 데 사용됩니다.',
    example: '20일 이동평균선은 최근 20일간의 평균 주가를 매일 계산해서 연결한 선입니다.',
    relatedTerms: ['golden_cross', 'dead_cross'],
    difficulty: 'intermediate',
    tags: ['차트', '평균', '추세']
  },
  {
    id: 'breakout',
    term: '돌파',
    category: 'general',
    definition: '지지선이나 저항선을 뚫고 나가는 현상',
    description: '주가가 기존의 지지선이나 저항선을 뚫고 새로운 방향으로 움직이는 것을 말합니다. 추세 전환의 신호로 해석됩니다.',
    example: '8만원 저항선을 뚫고 8만1천원으로 올라가면 상승 돌파라고 합니다.',
    relatedTerms: ['support_level', 'resistance_level', 'trend_change'],
    difficulty: 'intermediate',
    tags: ['차트', '돌파', '추세전환']
  },

  // ===== 거래 용어 =====
  {
    id: 'bid_ask_spread',
    term: '호가스프레드',
    category: 'trading',
    definition: '매도 호가와 매수 호가의 차이',
    description: '가장 낮은 매도 호가와 가장 높은 매수 호가의 차이로, 거래 비용과 유동성을 나타냅니다.',
    example: '매도호가 71,000원, 매수호가 70,900원이면 호가스프레드는 100원입니다.',
    relatedTerms: ['liquidity', 'market_order'],
    difficulty: 'intermediate',
    tags: ['호가', '유동성', '거래비용']
  },
  {
    id: 'market_order',
    term: '시장가 주문',
    category: 'trading',
    definition: '현재 시장 가격으로 즉시 거래하는 주문',
    description: '가격을 지정하지 않고 시장에서 형성되는 가격으로 즉시 매매하는 주문 방식입니다.',
    example: '삼성전자를 시장가로 100주 매수하면 현재 매도호가로 즉시 체결됩니다.',
    relatedTerms: ['limit_order', 'bid_ask_spread'],
    difficulty: 'beginner',
    tags: ['주문', '거래', '즉시체결']
  },
  {
    id: 'limit_order',
    term: '지정가 주문',
    category: 'trading',
    definition: '특정 가격을 지정하여 거래하는 주문',
    description: '원하는 가격을 지정하여 해당 가격에서만 거래가 이루어지도록 하는 주문 방식입니다.',
    example: '삼성전자를 70,000원 지정가로 매수 주문하면 70,000원 이하에서만 체결됩니다.',
    relatedTerms: ['market_order', 'pending_order'],
    difficulty: 'beginner',
    tags: ['주문', '거래', '가격지정']
  },
  {
    id: 'volume_weighted_average_price',
    term: 'VWAP (거래량가중평균가)',
    category: 'trading',
    definition: '거래량을 가중치로 한 평균 거래가격',
    description: 'Volume Weighted Average Price의 줄임말로, 일정 기간 동안 거래량을 가중치로 계산한 평균 가격입니다. 기관투자자들이 매매 기준으로 많이 사용합니다.',
    formula: 'VWAP = (가격 × 거래량의 합) ÷ 총 거래량',
    example: '오전에 7만원에 100주, 오후에 7만1천원에 200주 거래되었다면 VWAP는 70,667원입니다.',
    relatedTerms: ['trading_volume', 'average_price'],
    difficulty: 'advanced',
    tags: ['거래', '평균가격', '가중평균']
  }
];

// 카테고리별 용어 분류
export const termsByCategory = {
  'valuation': financialTerms.filter(term => term.category === 'valuation'),
  'profitability': financialTerms.filter(term => term.category === 'profitability'),
  'financial_health': financialTerms.filter(term => term.category === 'financial_health'),
  'market': financialTerms.filter(term => term.category === 'market'),
  'trading': financialTerms.filter(term => term.category === 'trading'),
  'general': financialTerms.filter(term => term.category === 'general'),
};

// 난이도별 용어 분류
export const termsByDifficulty = {
  'beginner': financialTerms.filter(term => term.difficulty === 'beginner'),
  'intermediate': financialTerms.filter(term => term.difficulty === 'intermediate'),
  'advanced': financialTerms.filter(term => term.difficulty === 'advanced'),
};

// 용어 검색 함수
export function searchTerms(query: string): FinancialTerm[] {
  if (!query.trim()) return [];
  
  const lowercaseQuery = query.toLowerCase();
  return financialTerms.filter(term => 
    term.term.toLowerCase().includes(lowercaseQuery) ||
    term.definition.toLowerCase().includes(lowercaseQuery) ||
    term.description.toLowerCase().includes(lowercaseQuery) ||
    term.tags.some(tag => tag.toLowerCase().includes(lowercaseQuery))
  );
}

// ID로 용어 찾기
export function findTermById(id: string): FinancialTerm | undefined {
  return financialTerms.find(term => term.id === id);
}

// 관련 용어 찾기
export function getRelatedTerms(termId: string): FinancialTerm[] {
  const term = findTermById(termId);
  if (!term || !term.relatedTerms) return [];
  
  return term.relatedTerms
    .map(id => findTermById(id))
    .filter((term): term is FinancialTerm => term !== undefined);
}

// 모든 용어 가져오기
export function getAllTerms(): FinancialTerm[] {
  return [...financialTerms];
}

// 카테고리 목록 가져오기
export function getTermCategories(): string[] {
  const categories = new Set(financialTerms.map(term => term.category));
  return Array.from(categories).sort();
}

// 난이도 옵션 가져오기
export function getDifficultyOptions(): string[] {
  const difficulties = new Set(financialTerms.map(term => term.difficulty));
  return Array.from(difficulties).sort((a, b) => {
    const order = { 'beginner': 1, 'intermediate': 2, 'advanced': 3 };
    return (order[a as keyof typeof order] || 999) - (order[b as keyof typeof order] || 999);
  });
}