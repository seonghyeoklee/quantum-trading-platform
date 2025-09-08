import { useState, useEffect } from 'react';
import { PopularStock, PopularStocksApiResponse, MarketCode } from '@/types/popular-stocks';

interface UsePopularStocksOptions {
  marketCode?: MarketCode;
  refreshInterval?: number; // in milliseconds
  autoRefresh?: boolean;
}

interface UsePopularStocksReturn {
  stocks: PopularStock[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  lastUpdated: Date | null;
}

// Transform KIS API response to frontend format
const transformApiResponse = (apiData: PopularStocksApiResponse): PopularStock[] => {
  if (!apiData.output || !Array.isArray(apiData.output)) {
    return [];
  }

  return apiData.output.map((item, index) => ({
    symbol: item.mksc_shrn_iscd,
    name: item.hts_kor_isnm,
    market: item.mrkt_div_cls_name === '코스피' ? 'KOSPI' : 'KOSDAQ',
    price: parseInt(item.stck_prpr) || 0,
    change: parseInt(item.prdy_vrss) || 0,
    changePercent: parseFloat(item.prdy_ctrt) || 0,
    volume: parseInt(item.acml_vol) || 0,
    rank: parseInt(item.data_rank) || (index + 1),
    registrationCount: parseInt(item.inter_issu_reg_csnu) || 0,
  }));
};

export const usePopularStocks = (options: UsePopularStocksOptions = {}): UsePopularStocksReturn => {
  const {
    marketCode = '0000', // Default to all markets
    refreshInterval = 300000, // 5 minutes
    autoRefresh = true,
  } = options;

  const [stocks, setStocks] = useState<PopularStock[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchPopularStocks = async (): Promise<void> => {
    try {
      setError(null);
      
      // Build API URL with market filter
      const params = new URLSearchParams();
      if (marketCode !== '0000') {
        params.append('market', marketCode);
      }
      
      const url = `http://adapter.quantum-trading.com:8000/domestic/ranking/top-interest-stock${params.toString() ? `?${params.toString()}` : ''}`;
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      const data: PopularStocksApiResponse = await response.json();
      
      // Check for API error response
      if (data.rt_cd !== '0') {
        throw new Error(data.msg1 || 'KIS API returned error');
      }

      const transformedStocks = transformApiResponse(data);
      setStocks(transformedStocks);
      setLastUpdated(new Date());
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch popular stocks';
      setError(errorMessage);
      console.error('Popular stocks fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const refresh = async (): Promise<void> => {
    setLoading(true);
    await fetchPopularStocks();
  };

  // Initial fetch
  useEffect(() => {
    fetchPopularStocks();
  }, [marketCode]);

  // Auto refresh interval
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchPopularStocks();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, marketCode]);

  return {
    stocks,
    loading,
    error,
    refresh,
    lastUpdated,
  };
};