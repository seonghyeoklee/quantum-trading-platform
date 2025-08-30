// 키움 실시간 데이터 파서
import { RealtimeQuoteData, RealtimeCandleData, RealtimeOrderBookData, RealtimeTradeData, RealtimeOrderExecutionData } from '@/lib/api/websocket-types';

// 키움 데이터 타입별 필드 매핑
export const KIWOOM_FIELD_MAP = {
  // 0B: 주식체결 데이터 필드
  '0B': {
    '10': 'current_price',      // 현재가
    '11': 'price_change',       // 전일대비
    '12': 'change_rate',        // 등락율
    '13': 'accumulated_volume', // 누적거래량
    '14': 'accumulated_amount', // 누적거래대금
    '15': 'volume',            // 거래량
    '16': 'open_price',        // 시가
    '17': 'high_price',        // 고가
    '18': 'low_price',         // 저가
    '19': 'prev_close',        // 전일종가
    '20': 'volume_ratio',      // 거래량비율
    '228': 'change_direction', // 대비기호 (1:상한, 2:상승, 3:보합, 4:하한, 5:하락)
  },
  
  // 0A: 주식호가 데이터 필드  
  '0A': {
    '21': 'ask_price_1',       // 매도호가1
    '22': 'ask_volume_1',      // 매도호가수량1
    '23': 'ask_price_2',       // 매도호가2
    '24': 'ask_volume_2',      // 매도호가수량2
    '25': 'ask_price_3',       // 매도호가3
    '26': 'ask_volume_3',      // 매도호가수량3
    '27': 'ask_price_4',       // 매도호가4
    '28': 'ask_volume_4',      // 매도호가수량4
    '29': 'ask_price_5',       // 매도호가5
    '30': 'ask_volume_5',      // 매도호가수량5
    '31': 'bid_price_1',       // 매수호가1
    '32': 'bid_volume_1',      // 매수호가수량1
    '33': 'bid_price_2',       // 매수호가2
    '34': 'bid_volume_2',      // 매수호가수량2
    '35': 'bid_price_3',       // 매수호가3
    '36': 'bid_volume_3',      // 매수호가수량3
    '37': 'bid_price_4',       // 매수호가4
    '38': 'bid_volume_4',      // 매수호가수량4
    '39': 'bid_price_5',       // 매수호가5
    '40': 'bid_volume_5',      // 매수호가수량5
    '41': 'total_ask_volume',  // 총매도호가잔량
    '42': 'total_bid_volume',  // 총매수호가잔량
  },
  
  // 00: 주문체결 데이터 필드
  '00': {
    '9201': 'account_number',  // 계좌번호
    '9203': 'order_number',    // 주문번호
    '9001': 'symbol',          // 종목코드
    '302': 'symbol_name',      // 종목명
    '913': 'order_status',     // 주문상태
    '905': 'order_type',       // 주문구분 (+매수, -매도)
    '906': 'order_method',     // 매매구분 (시장가, 지정가 등)
    '900': 'order_quantity',   // 주문수량
    '901': 'order_price',      // 주문가격
    '902': 'remaining_quantity', // 미체결수량
    '903': 'executed_amount',  // 체결누계금액
    '910': 'executed_price',   // 체결가
    '911': 'executed_quantity', // 체결량
    '10': 'current_price',     // 현재가
    '27': 'ask_price',         // 매도호가
    '28': 'bid_price',         // 매수호가
    '908': 'order_time',       // 주문/체결시간
    '919': 'reject_reason',    // 거부사유
    '938': 'commission',       // 수수료
    '939': 'tax',              // 세금
  }
} as const;

// 키움 종목 이름 매핑 (주요 종목만)
export const KIWOOM_STOCK_NAMES: Record<string, string> = {
  '005930': '삼성전자',
  '000660': 'SK하이닉스',
  '035420': 'NAVER',
  '207940': '삼성바이오로직스',
  '006400': '삼성SDI',
  '051910': 'LG화학',
  '068270': '셀트리온',
  '005380': '현대차',
  '035720': '카카오',
  '105560': 'KB금융',
};

// 문자열에서 숫자 추출 (천 단위 구분자 제거) - 키움 특화 처리
export function parseKiwoomNumber(value: string): number {
  if (!value) return 0;
  
  console.log('🔢 키움 숫자 파싱:', { 원본: value, 타입: typeof value });
  
  // 키움 데이터는 보통 문자열로 오고, 천단위 구분자나 특수문자가 포함될 수 있음
  // 1. 공백 제거
  let cleanValue = value.toString().trim();
  
  // 2. 천단위 구분자 (쉼표) 제거
  cleanValue = cleanValue.replace(/,/g, '');
  
  // 3. 더하기 기호 제거 (상승 표시)
  cleanValue = cleanValue.replace(/\+/g, '');
  
  // 4. 기타 통화 기호나 단위 제거 (원, $ 등)
  cleanValue = cleanValue.replace(/[원$%]/g, '');
  
  // 5. 최종적으로 숫자와 소수점, 마이너스만 남기기
  cleanValue = cleanValue.replace(/[^\d.-]/g, '');
  
  // 6. 빈 문자열이면 0 반환
  if (!cleanValue || cleanValue === '-') return 0;
  
  const result = parseFloat(cleanValue) || 0;
  
  // 7. 결과가 음수이고 주가/거래량 같은 항목이면 절댓값 사용 (키움 특성)
  // 키움에서는 때로 음수로 데이터가 와도 실제로는 양수 값
  const absoluteResult = Math.abs(result);
  
  console.log('✅ 키움 숫자 파싱 완료:', { 
    원본: value, 
    정제후: cleanValue, 
    파싱결과: result,
    절댓값: absoluteResult,
    최종사용: absoluteResult
  });
  
  return absoluteResult;
}

// 키움 대비기호를 방향으로 변환
export function parseChangeDirection(code: string): 'up' | 'down' | 'unchanged' {
  switch (code) {
    case '1': // 상한
    case '2': // 상승
      return 'up';
    case '4': // 하한  
    case '5': // 하락
      return 'down';
    case '3': // 보합
    default:
      return 'unchanged';
  }
}

// 숫자 파싱 (등락 정보용 - 음수 허용)
export function parseKiwoomNumberWithSign(value: string): number {
  if (!value) return 0;
  
  // 등락 정보는 음수가 정상이므로 절댓값을 취하지 않음
  let cleanValue = value.toString().trim();
  cleanValue = cleanValue.replace(/,/g, '');
  cleanValue = cleanValue.replace(/[원$%]/g, '');
  cleanValue = cleanValue.replace(/[^\d.-]/g, '');
  
  if (!cleanValue || cleanValue === '-') return 0;
  
  return parseFloat(cleanValue) || 0;
}

// 0B (주식체결) 데이터를 RealtimeQuoteData로 변환
export function parseKiwoomQuoteData(
  item: string, 
  values: { [key: string]: string },
  timestamp: string
): RealtimeQuoteData {
  // 키움 데이터의 특성을 고려한 파싱
  // 가격 데이터는 절댓값, 등락 데이터는 부호 유지
  const currentPrice = parseKiwoomNumber(values['10']);        // 현재가 (절댓값)
  const priceChange = parseKiwoomNumberWithSign(values['11']); // 전일대비 (부호 유지)
  const changeRate = parseKiwoomNumberWithSign(values['12']);  // 등락률 (부호 유지)
  const volume = parseKiwoomNumber(values['15']);              // 거래량 (절댓값)
  const openPrice = parseKiwoomNumber(values['16']);           // 시가 (절댓값)
  const highPrice = parseKiwoomNumber(values['17']);           // 고가 (절댓값)
  const lowPrice = parseKiwoomNumber(values['18']);            // 저가 (절댓값)
  
  // 전일종가는 현재가에서 등락을 빼서 계산
  const prevClose = currentPrice - priceChange;
  
  const changeDirection = parseChangeDirection(values['25']); // 전일대비기호 (field 25)

  console.log('🔄 키움 체결 데이터 파싱:', {
    종목: item,
    현재가: currentPrice,
    전일대비: priceChange,
    등락률: changeRate,
    거래량: volume,
    OHLC: { open: openPrice, high: highPrice, low: lowPrice, close: currentPrice },
    전일종가: prevClose,
    등락방향: changeDirection,
    원본값들: values
  });

  return {
    symbol: item,
    name: KIWOOM_STOCK_NAMES[item] || item,
    currentPrice,
    change: priceChange,
    changePercent: changeRate,
    changeDirection,
    volume,
    high: highPrice || currentPrice,
    low: lowPrice || currentPrice,
    open: openPrice || currentPrice,
    previousClose: prevClose,
    timestamp
  };
}

// 0B (주식체결) 데이터를 RealtimeCandleData로 변환  
export function parseKiwoomCandleData(
  item: string,
  values: { [key: string]: string },
  timestamp: string,
  isNew?: boolean
): RealtimeCandleData {
  // 캔들 데이터는 모두 가격이므로 절댓값으로 파싱
  const currentPrice = parseKiwoomNumber(values['10']);  // 현재가 (절댓값)
  const openPrice = parseKiwoomNumber(values['16']);     // 시가 (절댓값)
  const highPrice = parseKiwoomNumber(values['17']);     // 고가 (절댓값)
  const lowPrice = parseKiwoomNumber(values['18']);      // 저가 (절댓값)
  const volume = parseKiwoomNumber(values['15']);        // 거래량 (절댓값)

  console.log('📊 키움 실시간 캔들 데이터 파싱:', {
    종목: item,
    시간: { 원본timestamp: timestamp, 타입: typeof timestamp },
    OHLC: { 
      open: openPrice || currentPrice,
      high: highPrice || currentPrice, 
      low: lowPrice || currentPrice,
      close: currentPrice 
    },
    거래량: volume,
    isNew: isNew,
    원본values: { 
      '10': values['10'], // 현재가
      '15': values['15'], // 거래량 
      '16': values['16'], // 시가
      '17': values['17'], // 고가
      '18': values['18']  // 저가
    }
  });

  const result = {
    symbol: item,
    time: timestamp,
    open: openPrice || currentPrice,
    high: highPrice || currentPrice,
    low: lowPrice || currentPrice,
    close: currentPrice,
    volume,
    isNew: isNew ?? false  // 서버에서 제공하거나 클라이언트가 추론, 기본값 false
  };

  console.log('✅ 키움 실시간 캔들 데이터 파싱 완료:', result);

  return result;
}

// 0A (주식호가) 데이터를 RealtimeOrderBookData로 변환
export function parseKiwoomOrderBookData(
  item: string,
  values: { [key: string]: string },
  timestamp: string
): RealtimeOrderBookData {
  const asks = [];
  const bids = [];

  // 매도호가 5단계
  for (let i = 1; i <= 5; i++) {
    const priceKey = `${20 + i}`;  // 21, 22, 23, 24, 25
    const volumeKey = `${20 + i + 1}`;  // 22, 23, 24, 25, 26
    
    const price = parseKiwoomNumber(values[priceKey]);
    const volume = parseKiwoomNumber(values[volumeKey]);
    
    if (price > 0) {
      asks.push({ price, volume });
    }
  }

  // 매수호가 5단계  
  for (let i = 1; i <= 5; i++) {
    const priceKey = `${30 + i}`;  // 31, 32, 33, 34, 35
    const volumeKey = `${30 + i + 1}`;  // 32, 33, 34, 35, 36
    
    const price = parseKiwoomNumber(values[priceKey]);
    const volume = parseKiwoomNumber(values[volumeKey]);
    
    if (price > 0) {
      bids.push({ price, volume });
    }
  }

  const totalAskVolume = parseKiwoomNumber(values['41']);
  const totalBidVolume = parseKiwoomNumber(values['42']);

  console.log('📋 키움 호가 데이터 파싱:', {
    종목: item,
    매도호가: asks.length,
    매수호가: bids.length,
    총매도잔량: totalAskVolume,
    총매수잔량: totalBidVolume
  });

  return {
    symbol: item,
    timestamp,
    asks: asks.reverse(), // 높은 가격부터 정렬
    bids,                 // 높은 가격부터 정렬  
    totalAskVolume,
    totalBidVolume
  };
}

// 키움 실시간 데이터 통합 파서
export function parseKiwoomRealtimeData(
  originalData: {
    trnm?: string;
    data?: Array<{
      item: string;
      type: string;
      name: string;
      values: { [key: string]: string };
    }>;
  },
  timestamp: string
): {
  quotes: RealtimeQuoteData[];
  candles: RealtimeCandleData[];
  orderbooks: RealtimeOrderBookData[];
  trades: RealtimeTradeData[];
  orderExecutions: RealtimeOrderExecutionData[];
} {
  const quotes: RealtimeQuoteData[] = [];
  const candles: RealtimeCandleData[] = [];
  const orderbooks: RealtimeOrderBookData[] = [];
  const trades: RealtimeTradeData[] = [];
  const orderExecutions: RealtimeOrderExecutionData[] = [];

  if (!originalData.data) {
    return { quotes, candles, orderbooks, trades, orderExecutions };
  }

  originalData.data.forEach(itemData => {
    const { item, type, values } = itemData;

    console.log('🔍 키움 데이터 파싱:', {
      종목: item,
      타입: type,
      타입명: itemData.name,
      값개수: Object.keys(values).length
    });

    switch (type) {
      case '0B': // 주식체결
        const quote = parseKiwoomQuoteData(item, values, timestamp);
        quotes.push(quote);
        
        // 캔들 데이터도 함께 생성 (isNew는 클라이언트에서 판단)
        const candle = parseKiwoomCandleData(item, values, timestamp);
        candles.push(candle);
        
        // 체결 내역도 생성 (고유 ID 추가)
        const tradeId = `${item}-${timestamp}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const trade: RealtimeTradeData = {
          id: tradeId,
          symbol: item,
          timestamp,
          price: quote.currentPrice,
          volume: quote.volume,
          tradeType: 'unknown', // 키움에서 매수/매도 구분 정보가 없음
          changeFromPrevious: quote.change // 등락은 음수 가능 (이미 parseKiwoomNumberWithSign 사용)
        };
        trades.push(trade);
        
        console.log('💹 체결 내역 생성:', {
          id: tradeId,
          종목: item,
          가격: trade.price,
          거래량: trade.volume,
          등락: trade.changeFromPrevious
        });
        break;

      case '0A': // 주식호가
        const orderbook = parseKiwoomOrderBookData(item, values, timestamp);
        orderbooks.push(orderbook);
        break;

      case '00': // 주문체결
        const orderExecution = parseKiwoomOrderExecutionData(item, values, timestamp);
        orderExecutions.push(orderExecution);
        break;

      default:
        console.log('❓ 지원하지 않는 데이터 타입:', type, itemData.name);
    }
  });

  console.log('✅ 키움 데이터 파싱 완료:', {
    시세: quotes.length,
    캔들: candles.length, 
    호가: orderbooks.length,
    체결: trades.length,
    주문체결: orderExecutions.length
  });

  return { quotes, candles, orderbooks, trades, orderExecutions };
}

// 00 (주문체결) 데이터를 RealtimeOrderExecutionData로 변환
export function parseKiwoomOrderExecutionData(
  item: string,
  values: { [key: string]: string },
  timestamp: string
): RealtimeOrderExecutionData {
  const accountNumber = values['9201'] || '';
  const orderNumber = values['9203'] || '';
  const symbol = values['9001'] || item;
  const symbolName = values['302'] || KIWOOM_STOCK_NAMES[symbol] || symbol;
  const orderStatus = values['913'] || '';
  const orderTypeStr = values['905'] || '';
  const orderMethod = values['906'] || '';
  
  // 주문구분 파싱 (+매수, -매도 등)
  const orderType: 'buy' | 'sell' = orderTypeStr.includes('매수') || orderTypeStr.startsWith('+') ? 'buy' : 'sell';
  
  const orderQuantity = parseKiwoomNumber(values['900']);
  const orderPrice = parseKiwoomNumber(values['901']);
  const remainingQuantity = parseKiwoomNumber(values['902']);
  const executedAmount = parseKiwoomNumber(values['903']);
  const executedPrice = values['910'] ? parseKiwoomNumber(values['910']) : undefined;
  const executedQuantity = values['911'] ? parseKiwoomNumber(values['911']) : undefined;
  
  const currentPrice = parseKiwoomNumber(values['10']);
  const askPrice = parseKiwoomNumber(values['27']);
  const bidPrice = parseKiwoomNumber(values['28']);
  
  const orderTime = values['908'] || '';
  const rejectReason = values['919'] || undefined;
  const commission = parseKiwoomNumber(values['938']);
  const tax = parseKiwoomNumber(values['939']);

  console.log('📋 키움 주문체결 데이터 파싱:', {
    계좌번호: accountNumber,
    주문번호: orderNumber,
    종목: `${symbol}(${symbolName})`,
    주문상태: orderStatus,
    주문구분: orderType,
    매매구분: orderMethod,
    주문수량: orderQuantity,
    주문가격: orderPrice,
    미체결수량: remainingQuantity,
    체결가: executedPrice,
    체결량: executedQuantity,
    현재가: currentPrice,
    원본값들: values
  });

  return {
    id: `${orderNumber}-${timestamp}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    accountNumber,
    orderNumber,
    symbol,
    symbolName,
    orderStatus,
    orderType,
    orderMethod,
    orderQuantity,
    orderPrice,
    remainingQuantity,
    executedAmount,
    executedPrice,
    executedQuantity,
    currentPrice,
    askPrice,
    bidPrice,
    orderTime,
    timestamp,
    rejectReason,
    commission,
    tax
  };
}