// Quantum 백엔드 API 클라이언트 (JWT 인증, 백엔드 프록시 사용)
import { apiClient } from '@/lib/api';

export class QuantumApiClient {
  constructor() {
    // 표준 API 클라이언트 사용, baseUrl 불필요
  }

  // 현재가 조회 (JWT 인증, 백엔드 프록시)
  async getCurrentPrice(symbol: string): Promise<StockPriceResponse> {
    try {
      // 백엔드 프록시 API 호출 (JWT 토큰 자동 포함)
      const response = await apiClient.get<StockPriceResponse>(
        `/api/v1/kis/domestic/price/${symbol}`
      );

      return response.data;
    } catch (error) {
      console.error('현재가 조회 실패:', error);
      throw error;
    }
  }

  // 일봉 차트 데이터 조회 (JWT 인증, 백엔드 프록시)
  async getDailyChart(
    symbol: string, 
    startDate?: string, 
    endDate?: string
  ): Promise<ChartDataResponse> {
    try {
      const today = new Date();
      const defaultEndDate = endDate || today.toISOString().slice(0, 10).replace(/-/g, '');
      
      // 기본 1개월 전 데이터
      const defaultStartDate = startDate || (() => {
        const date = new Date();
        date.setDate(date.getDate() - 30);
        return date.toISOString().slice(0, 10).replace(/-/g, '');
      })();

      // 백엔드 프록시 API 호출 (JWT 토큰 자동 포함)
      const response = await apiClient.get<ChartDataResponse>(
        `/api/v1/kis/domestic/chart/daily/${symbol}?fid_input_date_1=${defaultStartDate}&fid_input_date_2=${defaultEndDate}`
      );

      return response.data;
    } catch (error) {
      console.error('차트 데이터 조회 실패:', error);
      throw error;
    }
  }

  // 주간 차트 데이터 조회 (JWT 인증, 백엔드 프록시)
  async getWeeklyChart(
    symbol: string, 
    startDate?: string, 
    endDate?: string
  ): Promise<ChartDataResponse> {
    try {
      const today = new Date();
      const defaultEndDate = endDate || today.toISOString().slice(0, 10).replace(/-/g, '');
      
      // 기본 1년 전 데이터
      const defaultStartDate = startDate || (() => {
        const date = new Date();
        date.setFullYear(date.getFullYear() - 1);
        return date.toISOString().slice(0, 10).replace(/-/g, '');
      })();

      // 백엔드 프록시 API 호출 (JWT 토큰 자동 포함)
      const response = await apiClient.get<ChartDataResponse>(
        `/api/v1/kis/domestic/chart/weekly/${symbol}?fid_input_date_1=${defaultStartDate}&fid_input_date_2=${defaultEndDate}`
      );

      return response.data;
    } catch (error) {
      console.error('주간 차트 데이터 조회 실패:', error);
      throw error;
    }
  }

  // 월간 차트 데이터 조회 (JWT 인증, 백엔드 프록시)
  async getMonthlyChart(
    symbol: string, 
    startDate?: string, 
    endDate?: string
  ): Promise<ChartDataResponse> {
    try {
      const today = new Date();
      const defaultEndDate = endDate || today.toISOString().slice(0, 10).replace(/-/g, '');
      
      // 기본 3년 전 데이터
      const defaultStartDate = startDate || (() => {
        const date = new Date();
        date.setFullYear(date.getFullYear() - 3);
        return date.toISOString().slice(0, 10).replace(/-/g, '');
      })();

      // 백엔드 프록시 API 호출 (JWT 토큰 자동 포함)
      const response = await apiClient.get<ChartDataResponse>(
        `/api/v1/kis/domestic/chart/monthly/${symbol}?fid_input_date_1=${defaultStartDate}&fid_input_date_2=${defaultEndDate}`
      );

      return response.data;
    } catch (error) {
      console.error('월간 차트 데이터 조회 실패:', error);
      throw error;
    }
  }

  // 🚀 새로운 통합 차트 데이터 조회 API
  async getChart(
    symbol: string,
    period: 'D' | 'W' | 'M' | 'Y' = 'D',
    startDate?: string,
    endDate?: string
  ): Promise<ChartDataResponse> {
    try {
      const today = new Date();
      const defaultEndDate = endDate || today.toISOString().slice(0, 10).replace(/-/g, '');
      
      // 기간별 기본 시작 날짜 설정
      const defaultStartDate = startDate || (() => {
        const date = new Date();
        switch (period) {
          case 'D': // 일봉: 1년
            date.setFullYear(date.getFullYear() - 1);
            break;
          case 'W': // 주봉: 1년
            date.setFullYear(date.getFullYear() - 1);
            break;
          case 'M': // 월봉: 3년
            date.setFullYear(date.getFullYear() - 3);
            break;
          case 'Y': // 년봉: 10년
            date.setFullYear(date.getFullYear() - 10);
            break;
          default:
            date.setFullYear(date.getFullYear() - 1);
        }
        return date.toISOString().slice(0, 10).replace(/-/g, '');
      })();

      console.log(`📊 새로운 차트 API 호출 (JWT 인증): ${period}보 ${symbol}`);
      
      // 백엔드 프록시 API 호출 (JWT 토큰 자동 포함)
      const response = await apiClient.get<ChartDataResponse>(
        `/api/v1/kis/domestic/chart/${symbol}?period=${period}&start_date=${defaultStartDate}&end_date=${defaultEndDate}`
      );

      const data = response.data;
      console.log(`✅ 차트 데이터 조회 성공: ${period}봉 ${data.output2?.length || 0}건`);
      return data;
    } catch (error) {
      console.error(`❌ ${period}봉 차트 데이터 조회 실패:`, error);
      throw error;
    }
  }

  // 년봉 차트 데이터 조회 (새 API 사용)
  async getYearlyChart(symbol: string, startDate?: string, endDate?: string): Promise<ChartDataResponse> {
    return this.getChart(symbol, 'Y', startDate, endDate);
  }

  // 국내 지수 조회 (JWT 인증, 백엔드 프록시)
  async getDomesticIndex(indexCode: string): Promise<IndexResponse> {
    try {
      // 백엔드 프록시 API 호출 (JWT 토큰 자동 포함)
      const response = await apiClient.get<IndexResponse>(
        `/api/v1/kis/domestic/index/${indexCode}`
      );

      return response.data;
    } catch (error) {
      console.error('지수 조회 실패:', error);
      throw error;
    }
  }

  // 주요 지수들 한번에 조회
  async getMajorIndices(): Promise<{
    kospi: IndexData;
    kosdaq: IndexData;
    kospi200?: IndexData;
  }> {
    try {
      const [kospiResponse, kosdaqResponse] = await Promise.all([
        this.getDomesticIndex('0001'), // KOSPI
        this.getDomesticIndex('1001'), // KOSDAQ
      ]);

      const kospiData = kospiResponse.output[0];
      const kosdaqData = kosdaqResponse.output[0];

      return {
        kospi: {
          name: 'KOSPI',
          value: parseFloat(kospiData.bstp_nmix_prpr),
          change: parseFloat(kospiData.bstp_nmix_prdy_vrss),
          changePercent: parseFloat(kospiData.bstp_nmix_prdy_ctrt),
          sign: kospiData.prdy_vrss_sign
        },
        kosdaq: {
          name: 'KOSDAQ',
          value: parseFloat(kosdaqData.bstp_nmix_prpr),
          change: parseFloat(kosdaqData.bstp_nmix_prdy_vrss),
          changePercent: parseFloat(kosdaqData.bstp_nmix_prdy_ctrt),
          sign: kosdaqData.prdy_vrss_sign
        }
      };
    } catch (error) {
      console.error('주요 지수 조회 실패:', error);
      throw error;
    }
  }
}

// API 응답 타입 정의
export interface StockPriceResponse {
  rt_cd: string;        // 응답 코드
  msg_cd: string;       // 메시지 코드  
  msg1: string;         // 메시지
  output: {
    iscd_stat_cls_code: string;    // 종목 상태 구분 코드
    marg_rate: string;             // 증거금 비율
    rprs_mrkt_kor_name: string;    // 대표 시장 한글 명
    new_hgpr_lwpr_cls_code: string; // 신 고가 저가 구분 코드
    bstp_kor_isnm: string;         // 업종 한글 종목명
    temp_stop_yn: string;          // 임시 정지 여부
    oprc_rang_cont_yn: string;     // 시가 범위 연장 여부
    clpr_rang_cont_yn: string;     // 종가 범위 연장 여부
    crdt_able: string;             // 신용 가능 여부
    grmn_rate_cls_code: string;    // 보증금 비율 구분 코드
    elw_pblc_yn: string;           // ELW 발행 여부
    stck_prpr: string;             // 주식 현재가
    prdy_vrss: string;             // 전일 대비
    prdy_vrss_sign: string;        // 전일 대비 부호
    prdy_ctrt: string;             // 전일 대비율
    acml_vol: string;              // 누적 거래량
    acml_tr_pbmn: string;          // 누적 거래 대금
    ssts_yn: string;               // 증권 거래세 여부
    stck_fcam: string;             // 주식 액면가
    stck_sspr: string;             // 주식 대용가
    hts_kor_isnm: string;          // HTS 한글 종목명
    stck_max: string;              // 주식 상한가
    stck_min: string;              // 주식 하한가
    stck_oprc: string;             // 주식 시가
    stck_hgpr: string;             // 주식 최고가
    stck_lwpr: string;             // 주식 최저가
    stck_prdy_clpr: string;        // 주식 전일 종가
    askp: string;                  // 매도호가
    bidp: string;                  // 매수호가
    prdy_vol: string;              // 전일 거래량
    vol_tnrt: string;              // 거래량 회전율
    stck_fcam_cnnm: string;        // 주식 액면가 통화명
    stck_sspr_cnnm: string;        // 주식 대용가 통화명
    per: string;                   // PER
    pbr: string;                   // PBR
    eps: string;                   // EPS
    bps: string;                   // BPS
    d250_hgpr: string;             // 250일 최고가
    d250_hgpr_date: string;        // 250일 최고가 일자
    d250_hgpr_vrss_prpr_rate: string; // 250일 최고가 대비 현재가 비율
    d250_lwpr: string;             // 250일 최저가
    d250_lwpr_date: string;        // 250일 최저가 일자
    d250_lwpr_vrss_prpr_rate: string; // 250일 최저가 대비 현재가 비율
    stck_dryy_hgpr: string;        // 주식 연중 최고가
    dryy_hgpr_vrss_prpr_rate: string; // 연중 최고가 대비 현재가 비율
    dryy_hgpr_date: string;        // 연중 최고가 일자
    stck_dryy_lwpr: string;        // 주식 연중 최저가
    dryy_lwpr_vrss_prpr_rate: string; // 연중 최저가 대비 현재가 비율
    dryy_lwpr_date: string;        // 연중 최저가 일자
    w52_hgpr: string;              // 52주 최고가
    w52_hgpr_vrss_prpr_ctrt: string; // 52주 최고가 대비 현재가 대비
    w52_hgpr_date: string;         // 52주 최고가 일자
    w52_lwpr: string;              // 52주 최저가
    w52_lwpr_vrss_prpr_ctrt: string; // 52주 최저가 대비 현재가 대비
    w52_lwpr_date: string;         // 52주 최저가 일자
    whol_loan_rmnd_rate: string;   // 전체 융자 잔고 비율
    ssts_hot_yn: string;           // 증권 거래세 과열 여부
    stck_shrn_iscd: string;        // 주식 단축 종목코드
    fcam_cnnm: string;             // 액면가 통화명
    cpfn: string;                  // 자본금
    stck_hgpr_date: string;        // 주식 최고가 일자
    stck_lwpr_date: string;        // 주식 최저가 일자
    trht_yn: string;               // 거래정지 여부
    mrkt_trtm_cls_code: string;    // 시장 거래시간 구분코드
    vi_cls_code: string;           // VI 구분 코드
  };
}

export interface ChartDataResponse {
  rt_cd: string;        // 응답 코드
  msg_cd: string;       // 메시지 코드
  msg1: string;         // 메시지
  output1: {
    prdy_vrss: string;        // 전일대비
    prdy_vrss_sign: string;   // 전일대비부호  
    prdy_ctrt: string;        // 전일대비율
    stck_prdy_clpr: string;   // 주식전일종가
    acml_vol: string;         // 누적거래량
    acml_tr_pbmn: string;     // 누적거래대금
    hts_kor_isnm: string;     // HTS한글종목명
    stck_prpr: string;        // 주식현재가
  };
  output2: Array<{
    stck_bsop_date: string;   // 주식영업일자
    stck_oprc: string;        // 주식시가
    stck_hgpr: string;        // 주식최고가  
    stck_lwpr: string;        // 주식최저가
    stck_clpr: string;        // 주식종가
    acml_vol: string;         // 누적거래량
    acml_tr_pbmn: string;     // 누적거래대금
    flng_cls_code: string;    // 락구분코드
    prtt_rate: string;        // 분할비율
    mod_yn: string;           // 분할변경여부
    prdy_vrss_sign: string;   // 전일대비부호
    prdy_vrss: string;        // 전일대비
    revl_issu_reas: string;   // 재평가사유
  }>;
}

// 지수 관련 타입 정의
export interface IndexResponse {
  rt_cd: string;
  msg_cd: string;
  msg1: string;
  output: Array<{
    bstp_nmix_prpr: string;        // 지수 현재가
    bstp_nmix_prdy_vrss: string;   // 전일 대비
    prdy_vrss_sign: string;        // 전일 대비 부호
    bstp_nmix_prdy_ctrt: string;   // 전일 대비율
    acml_vol: string;              // 누적 거래량
    prdy_vol: string;              // 전일 거래량
    acml_tr_pbmn: string;          // 누적 거래대금
    prdy_tr_pbmn: string;          // 전일 거래대금
    bstp_nmix_oprc: string;        // 지수 시가
    bstp_nmix_hgpr: string;        // 지수 최고가
    bstp_nmix_lwpr: string;        // 지수 최저가
    ascn_issu_cnt: string;         // 상승 종목수
    down_issu_cnt: string;         // 하락 종목수
    stnr_issu_cnt: string;         // 보합 종목수
    dryy_bstp_nmix_hgpr: string;   // 연중 최고가
    dryy_bstp_nmix_lwpr: string;   // 연중 최저가
  }>;
}

export interface IndexData {
  name: string;
  value: number;
  change: number;
  changePercent: number;
  sign: string; // 2: 상승, 4: 하락, 3: 보합
}

// 전역 API 클라이언트 인스턴스
export const quantumApiClient = new QuantumApiClient();
