'use client';

import { useState, useMemo, useEffect, useCallback, useRef, forwardRef, useImperativeHandle } from 'react';
import TradingChart from './TradingChart';
import ChartControls from './ChartControls';
import RealtimePrice from '../realtime/RealtimePrice';
import OrderBook from '../realtime/OrderBook';
import TradeHistory from '../realtime/TradeHistory';
import StockSearch from './StockSearch';
import { ChartTimeframe, ChartType, StockInfo, ChartState } from './ChartTypes';
import { kiwoomApiService } from '@/lib/api/kiwoom-service';
import { KiwoomStockInfo } from '@/lib/api/kiwoom-types';
import useWebSocket from '@/hooks/useWebSocket';
import { 
  RealtimeQuoteData, 
  RealtimeCandleData, 
  RealtimeOrderBookData, 
  RealtimeTradeData,
  WebSocketMessage 
} from '@/lib/api/websocket-types';
import { parseKiwoomRealtimeData } from '@/lib/utils/kiwoom-parser';

interface ChartContainerProps {
  className?: string;
  onStockSelect?: (stock: KiwoomStockInfo) => void;
}

export interface ChartContainerRef {
  selectStock: (stockCode: string, stockName: string) => void;
}

// 종목 정보 (6자리 종목코드 사용, 실제 API 응답 기준)
const stocksInfo: Record<string, StockInfo> = {
  // 대형주 (Large Cap)
  '005930': { symbol: '005930', name: '삼성전자', price: 70500, change: 0, changePercent: 0, market: 'KOSPI' },
  '000660': { symbol: '000660', name: 'SK하이닉스', price: 128000, change: 0, changePercent: 0, market: 'KOSPI' },
  '207940': { symbol: '207940', name: '삼성바이오로직스', price: 710000, change: 0, changePercent: 0, market: 'KOSPI' },
  '005380': { symbol: '005380', name: '현대차', price: 248000, change: 0, changePercent: 0, market: 'KOSPI' },
  '051910': { symbol: '051910', name: 'LG화학', price: 400000, change: 0, changePercent: 0, market: 'KOSPI' },
  
  // IT/테크 (IT/Tech)
  '035420': { symbol: '035420', name: 'NAVER', price: 221500, change: 0, changePercent: 0, market: 'KOSPI' },
  '035720': { symbol: '035720', name: '카카오', price: 65300, change: 0, changePercent: 0, market: 'KOSPI' },
  '036570': { symbol: '036570', name: 'NCsoft', price: 285000, change: 0, changePercent: 0, market: 'KOSPI' },
  '018260': { symbol: '018260', name: '삼성에스디에스', price: 142000, change: 0, changePercent: 0, market: 'KOSPI' },
  
  // 금융 (Financial)
  '055550': { symbol: '055550', name: '신한지주', price: 49200, change: 0, changePercent: 0, market: 'KOSPI' },
  '105560': { symbol: '105560', name: 'KB금융', price: 74600, change: 0, changePercent: 0, market: 'KOSPI' },
  '086790': { symbol: '086790', name: '하나금융지주', price: 64100, change: 0, changePercent: 0, market: 'KOSPI' },
  
  // 코스닥 (KOSDAQ)
  '091990': { symbol: '091990', name: '셀트리온헬스케어', price: 89500, change: 0, changePercent: 0, market: 'KOSDAQ' },
  '068270': { symbol: '068270', name: '셀트리온', price: 210000, change: 0, changePercent: 0, market: 'KOSPI' },
  '326030': { symbol: '326030', name: 'SK바이오팜', price: 112000, change: 0, changePercent: 0, market: 'KOSPI' },
  '028300': { symbol: '028300', name: 'HLB', price: 42750, change: 0, changePercent: 0, market: 'KOSDAQ' },
  '196170': { symbol: '196170', name: '알테오젠', price: 98600, change: 0, changePercent: 0, market: 'KOSDAQ' },
  
  // 엔터테인먼트 (Entertainment)
  '352820': { symbol: '352820', name: '하이브', price: 199000, change: 0, changePercent: 0, market: 'KOSPI' },
  '041510': { symbol: '041510', name: 'SM', price: 82900, change: 0, changePercent: 0, market: 'KOSDAQ' },
  '122870': { symbol: '122870', name: 'YG엔터테인먼트', price: 44700, change: 0, changePercent: 0, market: 'KOSDAQ' },
};

const ChartContainer = forwardRef<ChartContainerRef, ChartContainerProps>(({ className, onStockSelect }, ref) => {
  const [currentTimeframe, setCurrentTimeframe] = useState<ChartTimeframe>('1M');
  const [currentChartType, setCurrentChartType] = useState<ChartType>('daily');
  const [currentSymbol, setCurrentSymbol] = useState<string>('005930');
  const [selectedStock, setSelectedStock] = useState<KiwoomStockInfo | null>(null);
  const [chartState, setChartState] = useState<ChartState>({
    data: [],
    loading: false,
    error: null,
  });
  
  // 실시간 데이터 상태
  const [realtimeQuote, setRealtimeQuote] = useState<RealtimeQuoteData | null>(null);
  const [realtimeCandle, setRealtimeCandle] = useState<RealtimeCandleData | null>(null);
  const [realtimeOrderBook, setRealtimeOrderBook] = useState<RealtimeOrderBookData | null>(null);
  const [realtimeTrades, setRealtimeTrades] = useState<RealtimeTradeData[]>([]);

  // 실시간 데이터 업데이트 쓰로틀링을 위한 ref
  const lastQuoteUpdateRef = useRef<number>(0);
  const lastCandleUpdateRef = useRef<number>(0);
  const lastOrderBookUpdateRef = useRef<number>(0);
  
  // 업데이트 간격 설정 (밀리초) - 성능 최적화
  const QUOTE_UPDATE_INTERVAL = 1000; // 시세: 1초 (덜 자주 업데이트)
  const CANDLE_UPDATE_INTERVAL = 2000; // 캔들: 2초 (더 안정적)
  const ORDERBOOK_UPDATE_INTERVAL = 800; // 호가: 800ms (조금 더 여유있게)
  const [showRealtimePanel, setShowRealtimePanel] = useState<boolean>(true);
  
  // API 호출 중복 방지를 위한 ref
  const loadingRef = useRef<boolean>(false);

  // WebSocket 연결 설정
  const webSocket = useWebSocket({
    url: process.env.NEXT_PUBLIC_WS_URL || 'ws://adapter.quantum-trading.com:8000/ws/realtime',
    reconnectInterval: 3000,
    maxReconnectAttempts: 5,
    heartbeatInterval: 30000,
    onConnect: () => {
      console.log('✅ WebSocket 연결 성공');
      
      // 약간의 지연 후 구독 (서버가 완전히 준비된 후)
      setTimeout(() => {
        if (currentSymbol) {
          console.log('🔔 초기 종목 구독 시작:', currentSymbol);
          webSocket.subscribe([currentSymbol], ['quote', 'candle', 'orderbook', 'trade']);
        } else {
          console.log('⚠️ 현재 종목이 없어서 구독하지 않음');
        }
      }, 1000);
    },
    onDisconnect: () => {
      console.log('❌ WebSocket 연결 해제');
    },
    onError: (error) => {
      console.error('🚨 WebSocket 오류:', error);
    },
    onReconnecting: (attempt) => {
      console.log(`🔄 WebSocket 재연결 시도 중... (${attempt}회차)`);
    }
  });

  // 현재 종목 정보
  const currentStockInfo = useMemo(() => {
    // 검색으로 선택된 종목이 있으면 우선 사용
    if (selectedStock) {
      const basePrice = parseInt(selectedStock.lastPrice) || 0;
      
      // 차트 데이터가 있으면 최신 가격 정보 업데이트
      if (chartState.data.length > 0) {
        const latestData = chartState.data[chartState.data.length - 1];
        const previousData = chartState.data[chartState.data.length - 2];
        
        const price = latestData.close;
        const change = previousData ? latestData.close - previousData.close : latestData.close - basePrice;
        const changePercent = previousData 
          ? (change / previousData.close) * 100 
          : basePrice > 0 ? ((latestData.close - basePrice) / basePrice) * 100 : 0;
        
        return {
          symbol: selectedStock.code,
          name: selectedStock.name,
          price,
          change,
          changePercent,
          market: (selectedStock.marketName === 'KOSDAQ' ? 'KOSDAQ' : 'KOSPI') as 'KOSPI' | 'KOSDAQ',
        };
      }
      
      return {
        symbol: selectedStock.code,
        name: selectedStock.name,
        price: basePrice,
        change: 0,
        changePercent: 0,
        market: (selectedStock.marketName === 'KOSDAQ' ? 'KOSDAQ' : 'KOSPI') as 'KOSPI' | 'KOSDAQ',
      };
    }
    
    // 기본 하드코딩된 종목 정보 사용
    const baseInfo = stocksInfo[currentSymbol] || stocksInfo['005930'];
    
    // 차트 데이터가 있으면 최신 가격 정보 업데이트
    if (chartState.data.length > 0) {
      const latestData = chartState.data[chartState.data.length - 1];
      const previousData = chartState.data[chartState.data.length - 2];
      
      const price = latestData.close;
      const change = previousData ? latestData.close - previousData.close : 0;
      const changePercent = previousData ? (change / previousData.close) * 100 : 0;
      
      return {
        ...baseInfo,
        price,
        change,
        changePercent,
      };
    }
    
    return baseInfo;
  }, [currentSymbol, chartState.data, selectedStock]);

  // WebSocket 메시지 처리
  useEffect(() => {
    const message = webSocket.lastMessage;
    if (!message) {
      console.log('📭 WebSocket 메시지가 없음');
      return;
    }

    console.log('📨 WebSocket 메시지 처리 시작:', {
      type: message.type,
      symbol: message.symbol,
      currentSymbol: currentSymbol,
      dataType: typeof message.data,
      dataKeys: message.data ? Object.keys(message.data) : []
    });

    try {
      // 새로운 키움 API 실시간 데이터 처리
      if (message.type === 'kiwoom_realtime' && message.original_data) {
        console.log('🔥 새로운 키움 실시간 데이터 처리:', message.original_data);
        
        const { quotes, candles, orderbooks, trades } = parseKiwoomRealtimeData(
          message.original_data,
          message.timestamp || new Date().toISOString()
        );

        // 현재 선택된 종목의 데이터만 UI에 반영 (쓰로틀링 적용)
        const now = Date.now();
        
        quotes.forEach(quote => {
          if (quote.symbol === currentSymbol) {
            // 시세 업데이트 쓰로틀링
            if (now - lastQuoteUpdateRef.current >= QUOTE_UPDATE_INTERVAL) {
              setRealtimeQuote(quote);
              lastQuoteUpdateRef.current = now;
              console.log('💰 키움 실시간 시세 업데이트:', quote.currentPrice, '원');
            }
          }
        });

        candles.forEach(candle => {
          if (candle.symbol === currentSymbol) {
            // 캔들 업데이트 쓰로틀링
            if (now - lastCandleUpdateRef.current >= CANDLE_UPDATE_INTERVAL) {
              console.log('🔥 실시간 캔들 데이터 수신:', {
                symbol: candle.symbol,
                time: candle.time,
                시간타입: typeof candle.time,
                OHLCV: {
                  open: candle.open,
                  high: candle.high,
                  low: candle.low,
                  close: candle.close,
                  volume: candle.volume
                },
                isNew: candle.isNew,
                현재차트타입: currentChartType
              });
              setRealtimeCandle(candle);
              lastCandleUpdateRef.current = now;
            }
          }
        });

        orderbooks.forEach(orderbook => {
          if (orderbook.symbol === currentSymbol) {
            // 호가 업데이트 쓰로틀링
            if (now - lastOrderBookUpdateRef.current >= ORDERBOOK_UPDATE_INTERVAL) {
              setRealtimeOrderBook(orderbook);
              lastOrderBookUpdateRef.current = now;
              console.log('📋 키움 실시간 호가 업데이트:', orderbook.asks.length, '단계');
            }
          }
        });

        trades.forEach(trade => {
          if (trade.symbol === currentSymbol) {
            setRealtimeTrades(prev => {
              // 최신 체결 내역을 앞에 추가하고 100개까지만 유지
              const newTrades = [trade, ...prev].slice(0, 100);
              return newTrades;
            });
            console.log('🤝 키움 실시간 체결 업데이트:', trade.price, '원');
          }
        });
      }

      // 키움 서버 연결/구독 응답 처리
      if (message.event) {
        switch (message.event) {
          case 'connected':
            console.log('✅ 키움 서버 연결 완료 (레거시):', message.message);
            console.log('📊 서버 정보:', message.info);
            break;

          default:
            console.log('❓ 알 수 없는 키움 이벤트 (레거시):', message.event, message);
        }
      }

      // 레거시 실시간 데이터 처리 (이전 형식 호환성)
      if (message.type === 'realtime_data' && message.data) {
        const realtimeData = message.data;
        console.log('🔥 레거시 실시간 데이터 처리:', realtimeData);
        
        if (realtimeData.stock_code === currentSymbol) {
          // 레거시 형식을 새로운 형식으로 변환
          const quoteData: RealtimeQuoteData = {
            symbol: realtimeData.stock_code,
            name: realtimeData.stock_name,
            currentPrice: parseFloat(realtimeData.current_price.replace(/[^\d]/g, '')),
            change: parseFloat(realtimeData.price_change.replace(/[^\d-]/g, '')),
            changePercent: parseFloat(realtimeData.change_rate.replace(/[^\d.-]/g, '')),
            changeDirection: realtimeData.trend === 'up' ? 'up' : realtimeData.trend === 'down' ? 'down' : 'unchanged',
            volume: parseFloat(realtimeData.volume.replace(/[^\d]/g, '')),
            high: parseFloat(realtimeData.current_price.replace(/[^\d]/g, '')),
            low: parseFloat(realtimeData.current_price.replace(/[^\d]/g, '')),
            open: parseFloat(realtimeData.current_price.replace(/[^\d]/g, '')),
            previousClose: parseFloat(realtimeData.current_price.replace(/[^\d]/g, '')) - parseFloat(realtimeData.price_change.replace(/[^\d-]/g, '')),
            timestamp: realtimeData.timestamp
          };
          
          setRealtimeQuote(quoteData);
          console.log('💰 레거시 실시간 시세 업데이트:', quoteData.currentPrice, '원');
          
          const candleData: RealtimeCandleData = {
            symbol: realtimeData.stock_code,
            time: realtimeData.timestamp,
            open: quoteData.previousClose,
            high: quoteData.currentPrice,
            low: quoteData.currentPrice,
            close: quoteData.currentPrice,
            volume: quoteData.volume,
            isNew: realtimeData.isNew ?? undefined
          };
          
          setRealtimeCandle(candleData);
          console.log('📊 레거시 실시간 캔들 업데이트:', candleData.close, '원');
        }
      }

      // 표준 형식 처리 (향후 서버 업데이트 시)
      if (message.type) {
        switch (message.type) {
          case 'quote':
            const quoteData = message.data as RealtimeQuoteData;
            if (quoteData.symbol === currentSymbol) {
              setRealtimeQuote(quoteData);
              console.log('💰 실시간 시세 업데이트:', quoteData.currentPrice);
            }
            break;

          case 'candle':
            const candleData = message.data as RealtimeCandleData;
            if (candleData.symbol === currentSymbol) {
              setRealtimeCandle(candleData);
              console.log('📊 실시간 캔들 업데이트:', candleData.close);
            }
            break;

          case 'orderbook':
            const orderbookData = message.data as RealtimeOrderBookData;
            if (orderbookData.symbol === currentSymbol) {
              setRealtimeOrderBook(orderbookData);
              console.log('📋 실시간 호가 업데이트:', orderbookData.asks.length, '단계');
            }
            break;

          case 'trade':
            const tradeData = message.data as RealtimeTradeData;
            if (tradeData.symbol === currentSymbol) {
              setRealtimeTrades(prev => [...prev, tradeData].slice(-100)); // 최근 100개만 유지
              console.log('🤝 실시간 체결 업데이트:', tradeData.price, tradeData.volume);
            }
            break;

          case 'error':
            console.error('🚨 WebSocket 에러 메시지:', message.data);
            break;

          default:
            console.log('❓ 알 수 없는 메시지 타입:', message.type);
        }
      }
    } catch (error) {
      console.error('📨 WebSocket 메시지 처리 오류:', error);
    }
  }, [webSocket.lastMessage, currentSymbol]);

  // 종목 변경 시 WebSocket 구독 업데이트 (새로운 키움 API)
  useEffect(() => {
    if (webSocket.isConnected && currentSymbol) {
      console.log('🔄 종목 변경으로 키움 WebSocket 구독 업데이트:', {
        종목: currentSymbol,
        이름: stocksInfo[currentSymbol]?.name || '알 수 없음'
      });
      
      // 새로운 키움 REG 방식으로 구독 (refresh: false = 기존 해지하고 새로 구독)
      webSocket.subscribe([currentSymbol], ['quote', 'candle', 'orderbook', 'trade'], false);
      
      // 실시간 데이터 초기화
      setRealtimeQuote(null);
      setRealtimeCandle(null);
      setRealtimeOrderBook(null);
      setRealtimeTrades([]);
      
      console.log(`✅ ${currentSymbol} 키움 REG 구독 완료`);
    } else {
      console.log('⚠️ 종목 구독 불가:', {
        연결상태: webSocket.isConnected,
        종목: currentSymbol,
        WebSocket상태: webSocket.status
      });
    }
  }, [currentSymbol, webSocket.isConnected, webSocket.subscribe, webSocket.unsubscribe]);

  // WebSocket 연결 시작
  useEffect(() => {
    console.log('🚀 WebSocket 연결 시작:', {
      url: process.env.NEXT_PUBLIC_WS_URL || 'ws://adapter.quantum-trading.com:8000/ws/realtime',
      currentSymbol: currentSymbol,
      status: webSocket.status
    });
    webSocket.connect();
    
    return () => {
      console.log('🛑 WebSocket 연결 해제');
      webSocket.disconnect();
    };
  }, [webSocket.connect, webSocket.disconnect]);

  // WebSocket 상태 및 실시간 데이터 모니터링
  useEffect(() => {
    console.log('🔍 WebSocket 상태 변경:', {
      상태: webSocket.status,
      연결됨: webSocket.isConnected,
      재연결시도: webSocket.reconnectAttempts,
      에러: webSocket.error?.message,
      마지막메시지시간: webSocket.lastMessage?.timestamp
    });
  }, [webSocket.status, webSocket.isConnected, webSocket.reconnectAttempts, webSocket.error]);

  useEffect(() => {
    if (realtimeQuote) {
      console.log('💰 실시간 시세 업데이트:', {
        종목: `${realtimeQuote.symbol} (${realtimeQuote.name})`,
        현재가: `${realtimeQuote.currentPrice.toLocaleString()}원`,
        등락: `${realtimeQuote.change >= 0 ? '+' : ''}${realtimeQuote.change.toLocaleString()}원`,
        등락률: `${realtimeQuote.changePercent >= 0 ? '+' : ''}${realtimeQuote.changePercent.toFixed(2)}%`,
        방향: realtimeQuote.changeDirection,
        거래량: realtimeQuote.volume.toLocaleString(),
        시간: realtimeQuote.timestamp
      });
    }
  }, [realtimeQuote]);

  useEffect(() => {
    if (realtimeCandle) {
      console.log('📊 실시간 캔들 업데이트:', {
        종목: realtimeCandle.symbol,
        시간: realtimeCandle.time,
        OHLCV: {
          시가: realtimeCandle.open.toLocaleString(),
          고가: realtimeCandle.high.toLocaleString(),
          저가: realtimeCandle.low.toLocaleString(),
          종가: realtimeCandle.close.toLocaleString(),
          거래량: realtimeCandle.volume.toLocaleString()
        },
        새캔들여부: realtimeCandle.isNew
      });
    }
  }, [realtimeCandle]);

  useEffect(() => {
    if (realtimeOrderBook && realtimeOrderBook.asks.length > 0) {
      console.log('📋 실시간 호가 업데이트:', {
        종목: realtimeOrderBook.symbol,
        매도호가: realtimeOrderBook.asks.slice(0, 3).map(ask => `${ask.price.toLocaleString()}원(${ask.volume})`),
        매수호가: realtimeOrderBook.bids.slice(0, 3).map(bid => `${bid.price.toLocaleString()}원(${bid.volume})`),
        총매도잔량: realtimeOrderBook.totalAskVolume.toLocaleString(),
        총매수잔량: realtimeOrderBook.totalBidVolume.toLocaleString(),
        스프레드: realtimeOrderBook.asks[0] && realtimeOrderBook.bids[0] ? 
          (realtimeOrderBook.asks[0].price - realtimeOrderBook.bids[0].price) : 0
      });
    }
  }, [realtimeOrderBook]);

  useEffect(() => {
    if (realtimeTrades && realtimeTrades.length > 0) {
      const latestTrade = realtimeTrades[0];
      console.log('🤝 실시간 체결 업데이트:', {
        종목: latestTrade.symbol,
        체결가: `${latestTrade.price.toLocaleString()}원`,
        체결량: latestTrade.volume.toLocaleString(),
        매매구분: latestTrade.tradeType,
        직전대비: `${latestTrade.changeFromPrevious >= 0 ? '+' : ''}${latestTrade.changeFromPrevious}원`,
        총체결수: realtimeTrades.length
      });
    }
  }, [realtimeTrades]);

  // 컴포넌트 마운트 및 종목/시간대/차트타입 변경 시 데이터 로드
  useEffect(() => {
    let isCancelled = false;
    const requestKey = `${currentSymbol}-${currentTimeframe}-${currentChartType}`;

    const loadChartData = async () => {
      // 이미 로딩 중이거나 동일한 요청이면 중복 호출 방지
      if (loadingRef.current) {
        console.log('이미 API 호출 중입니다. 중복 호출 방지');
        return;
      }

      console.log(`차트 데이터 로드 시작: ${requestKey}`);
      
      loadingRef.current = true;
      setChartState(prev => ({ ...prev, loading: true, error: null }));

      // 300ms 디바운싱 - 빠른 연속 호출 방지
      await new Promise(resolve => setTimeout(resolve, 300));
      
      if (isCancelled) return;

      try {
        // 차트 타입이 사용자에 의해 선택된 경우 직접 타입으로 조회
        const data = await kiwoomApiService.getChartDataByType(currentSymbol, currentChartType, currentTimeframe);
        
        if (!isCancelled) {
          console.log(`차트 데이터 로드 완료: ${data.length}개`);
          
          setChartState(prev => ({
            ...prev,
            data,
            loading: false,
            error: null,
            lastUpdated: new Date(),
          }));
        }

      } catch (error) {
        if (!isCancelled) {
          console.error('차트 데이터 로드 실패:', error);
          
          setChartState(prev => ({
            ...prev,
            data: [],
            loading: false,
            error: error instanceof Error ? error.message : '데이터 로드에 실패했습니다.',
          }));
        }
      } finally {
        if (!isCancelled) {
          loadingRef.current = false;
        }
      }
    };

    loadChartData();

    return () => {
      isCancelled = true;
      loadingRef.current = false;
    };
  }, [currentSymbol, currentTimeframe, currentChartType]);

  // 수동 새로고침용 함수
  const loadChartData = useCallback(async () => {
    setChartState(prev => ({ ...prev, loading: true, error: null }));

    try {
      console.log(`수동 차트 데이터 로드: ${currentSymbol}, ${currentChartType}, ${currentTimeframe}`);
      
      const data = await kiwoomApiService.getChartDataByType(currentSymbol, currentChartType, currentTimeframe);
      
      console.log(`수동 차트 데이터 로드 완료: ${data.length}개`);
      
      setChartState(prev => ({
        ...prev,
        data,
        loading: false,
        error: null,
        lastUpdated: new Date(),
      }));

    } catch (error) {
      console.error('수동 차트 데이터 로드 실패:', error);
      
      setChartState(prev => ({
        ...prev,
        data: [],
        loading: false,
        error: error instanceof Error ? error.message : '데이터 로드에 실패했습니다.',
      }));
    }
  }, [currentSymbol, currentChartType, currentTimeframe]);

  const handleTimeframeChange = useCallback((timeframe: ChartTimeframe) => {
    setCurrentTimeframe(timeframe);
  }, []);

  const handleChartTypeChange = useCallback((chartType: ChartType) => {
    setCurrentChartType(chartType);
  }, []);

  const handleStockChange = useCallback((symbol: string) => {
    setCurrentSymbol(symbol);
  }, []);

  const handleStockSelect = useCallback((stock: KiwoomStockInfo) => {
    console.log('선택된 종목:', stock);
    setCurrentSymbol(stock.code);
    setSelectedStock(stock);
    
    // 부모 컴포넌트로 종목 선택 이벤트 전달
    if (onStockSelect) {
      onStockSelect(stock);
    }
  }, [onStockSelect]);

  // 외부에서 종목 선택을 위한 함수
  const selectStockByCode = useCallback((stockCode: string, stockName: string) => {
    console.log('외부에서 종목 선택:', stockCode, stockName);
    
    // stocksInfo에서 해당 종목 찾기
    const stockInfo = stocksInfo[stockCode];
    
    // Create minimal stock info structure with only available real data
    const stockInfoData: KiwoomStockInfo = {
      code: stockCode,
      name: stockName,
      listCount: '',
      auditInfo: '',
      regDay: '',
      lastPrice: String(stockInfo?.price || ''),
      state: '',
      marketCode: '',
      marketName: stockInfo?.market || '',
      upName: '',
      upSizeName: '',
      orderWarning: '',
      nxtEnable: ''
    };
    
    handleStockSelect(stockInfoData);
  }, [handleStockSelect]);

  // ref로 외부에 노출할 메서드들
  useImperativeHandle(ref, () => ({
    selectStock: selectStockByCode
  }), [selectStockByCode]);


  // 수동 구독 테스트 함수
  const handleManualSubscribe = useCallback(() => {
    console.log('🔄 수동 구독 테스트 시작:', currentSymbol);
    console.log('WebSocket 상태:', webSocket.status, 'isConnected:', webSocket.isConnected);
    
    if (webSocket.isConnected && currentSymbol) {
      webSocket.subscribe([currentSymbol], ['quote', 'candle', 'orderbook', 'trade']);
    } else {
      console.log('❌ WebSocket 연결되지 않음 또는 종목 없음');
    }
  }, [webSocket, currentSymbol]);

  // 하단 시장 데이터 계산
  const marketData = useMemo(() => {
    if (chartState.data.length === 0) {
      return {
        openPrice: 0,
        highPrice: 0,
        lowPrice: 0,
        volume: 0,
      };
    }

    const data = chartState.data;
    const openPrice = data[0]?.open || 0;
    const highPrice = Math.max(...data.map(d => d.high));
    const lowPrice = Math.min(...data.map(d => d.low));
    const volume = data.reduce((sum, d) => sum + (d.volume || 0), 0);

    return { openPrice, highPrice, lowPrice, volume };
  }, [chartState.data]);

  return (
    <div className={`flex flex-col h-full ${className || ''}`}>
      {/* 종목 검색 */}
      <div className="p-2 sm:p-4 border-b border-border bg-card">
        <StockSearch
          onStockSelect={handleStockSelect}
          className="w-full"
        />
      </div>

      {/* 차트 컨트롤 */}
      <ChartControls
        currentTimeframe={currentTimeframe}
        currentChartType={currentChartType}
        currentStock={currentStockInfo}
        isStockSelected={selectedStock !== null}
        onTimeframeChange={handleTimeframeChange}
        onChartTypeChange={handleChartTypeChange}
        onStockChange={handleStockChange}
      />
      
      {/* 메인 차트 영역 */}
      <div className="flex-1 p-2 sm:p-4 lg:p-6 bg-background relative">
        {chartState.loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/80 z-10">
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
              <span className="text-sm text-muted-foreground">차트 데이터 로딩 중...</span>
            </div>
          </div>
        )}

        {chartState.error && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/80 z-10">
            <div className="text-center">
              <div className="text-red-500 text-sm mb-2">❌ 데이터 로드 실패</div>
              <div className="text-xs text-muted-foreground mb-4">{chartState.error}</div>
              <button 
                onClick={loadChartData}
                className="px-3 py-1 text-xs bg-primary text-primary-foreground rounded hover:bg-primary/90"
              >
                다시 시도
              </button>
            </div>
          </div>
        )}

        <div className="w-full h-full">
          <TradingChart
            symbol={currentSymbol}
            market="domestic"
            stockInfo={currentStockInfo}
            realtimeData={{
              price: realtimeQuote?.currentPrice,
              volume: realtimeQuote?.volume,
              timestamp: realtimeQuote?.timestamp
            }}
            onRealtimeUpdate={(data) => {
              console.log('📊 TradingChart 실시간 업데이트 콜백:', data);
            }}
          />
        </div>
      </div>

      {/* 실시간 데이터 패널 - 모바일 최적화 */}
      {showRealtimePanel && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-4 p-2 sm:p-4 border-t border-border bg-background">
          {/* 실시간 가격 - 모바일에서 전체 너비 */}
          <div className="col-span-1 md:col-span-2 lg:col-span-1">
            <RealtimePrice data={realtimeQuote} />
          </div>
          
          {/* 호가창 - 모바일에서 전체 너비 */}
          <div className="col-span-1 md:col-span-1 lg:col-span-1">
            <OrderBook data={realtimeOrderBook} maxLevels={5} />
          </div>
          
          {/* 체결 내역 - 모바일에서 전체 너비 */}
          <div className="col-span-1 md:col-span-1 lg:col-span-1">
            <TradeHistory trades={realtimeTrades} maxItems={15} />
          </div>
        </div>
      )}
      
      {/* 하단 시장 데이터 - 모바일 최적화 */}
      <div className="p-3 sm:p-4 lg:p-6 border-t border-border bg-muted">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 lg:gap-6">
          <div className="space-y-2">
            <div className="text-xs text-muted-foreground">시가</div>
            <div className="text-sm font-medium">
              {marketData.openPrice > 0 ? marketData.openPrice.toLocaleString('ko-KR') : '-'}
            </div>
          </div>
          <div className="space-y-2">
            <div className="text-xs text-muted-foreground">고가</div>
            <div className="text-sm font-medium text-bull">
              {marketData.highPrice > 0 ? marketData.highPrice.toLocaleString('ko-KR') : '-'}
            </div>
          </div>
          <div className="space-y-2">
            <div className="text-xs text-muted-foreground">저가</div>
            <div className="text-sm font-medium text-bear">
              {marketData.lowPrice > 0 ? marketData.lowPrice.toLocaleString('ko-KR') : '-'}
            </div>
          </div>
          <div className="space-y-2">
            <div className="text-xs text-muted-foreground">거래량</div>
            <div className="text-sm font-medium">
              {marketData.volume > 0 ? marketData.volume.toLocaleString('ko-KR') : '-'}
            </div>
          </div>
        </div>

        {/* 데이터 상태 정보 - 모바일 최적화 */}
        <div className="mt-4 flex flex-col sm:flex-row sm:items-center sm:justify-between text-xs text-muted-foreground space-y-2 sm:space-y-0">
          <div className="flex flex-wrap items-center gap-2 sm:gap-4">
            <span>키움증권 API 연동</span>
            {chartState.lastUpdated && (
              <span className="hidden sm:inline">마지막 업데이트: {chartState.lastUpdated.toLocaleTimeString('ko-KR')}</span>
            )}
            <span className="hidden sm:inline">•</span>
            <span className="hidden sm:inline">WebSocket 실시간 연결</span>
            {webSocket.status === 'reconnecting' && (
              <span>재연결 시도 중... ({webSocket.reconnectAttempts}회차)</span>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-2 sm:gap-4 justify-end">
            {/* REST API 상태 */}
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${chartState.error ? 'bg-red-500' : chartState.loading ? 'bg-yellow-500' : 'bg-green-500'}`} />
              <span>API {chartState.error ? '실패' : chartState.loading ? '로딩' : '연결'}</span>
            </div>
            
            {/* WebSocket 상태 */}
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${
                webSocket.status === 'connected' ? 'bg-green-500' : 
                webSocket.status === 'connecting' || webSocket.status === 'reconnecting' ? 'bg-yellow-500' : 
                'bg-red-500'
              } ${webSocket.status === 'connected' ? 'animate-pulse' : ''}`} />
              <span>실시간 {
                webSocket.status === 'connected' ? '연결됨' :
                webSocket.status === 'connecting' ? '연결 중' :
                webSocket.status === 'reconnecting' ? '재연결 중' :
                webSocket.status === 'error' ? '오류' :
                '연결 해제'
              }</span>
            </div>

            {/* 실시간 패널 토글 - 모바일에서 간단한 텍스트 */}
            <button
              onClick={() => setShowRealtimePanel(!showRealtimePanel)}
              className="text-primary hover:text-primary/80 transition-colors text-xs sm:text-xs"
            >
              <span className="hidden sm:inline">
                {showRealtimePanel ? '실시간 패널 숨기기' : '실시간 패널 표시'}
              </span>
              <span className="sm:hidden">
                {showRealtimePanel ? '실시간 숨김' : '실시간 보기'}
              </span>
            </button>

            {/* TradingView 가이드: Go to Realtime 버튼 - 모바일 숨김 */}
            <button
              onClick={() => {
                // TradingView 차트의 실시간 스크롤 기능 활성화
                const chartElement = document.querySelector('.trading-chart-container');
                if (chartElement) {
                  const event = new CustomEvent('goToRealtime');
                  chartElement.dispatchEvent(event);
                }
              }}
              className="hidden sm:block px-2 py-1 text-xs bg-green-500 text-white rounded hover:bg-green-600 transition-colors"
            >
              📈 실시간
            </button>

            {/* 수동 구독 테스트 버튼 - 개발 환경에서만 표시 */}
            {process.env.NODE_ENV === 'development' && (
              <button
                onClick={handleManualSubscribe}
                className="hidden lg:block px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
              >
                구독 테스트
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
});

ChartContainer.displayName = 'ChartContainer';

export default ChartContainer;
