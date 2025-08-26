"""
종목분석 API 라우터

Google Sheets 분석 로직을 API로 제공합니다.
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path as PathLib
from typing import Dict, List

from fastapi import APIRouter, HTTPException, Path, Query

# Handle both relative and absolute imports for different execution contexts
try:
    from ...models.kiwoom_request import KiwoomStockChartApiRequest
    from ...functions.chart import fn_ka10081
    from ...functions.stock import fn_ka10099
    from ..indicators.technical import calculate_rsi, calculate_obv, calculate_sma, calculate_ema
    from ..core.scorer import AnalysisScorer
    from ..core.models import (
        RSIAnalysisRequest, RSIAnalysisResponse, 
        TechnicalAnalysisResponse, AnalysisError, create_analysis_error
    )
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = PathLib(__file__).parent.parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    from kiwoom_api.models.kiwoom_request import KiwoomStockChartApiRequest
    from kiwoom_api.functions.chart import fn_ka10081
    from kiwoom_api.functions.stock import fn_ka10099
    from kiwoom_api.analysis.indicators.technical import calculate_rsi, calculate_obv, calculate_sma, calculate_ema
    from kiwoom_api.analysis.core.scorer import AnalysisScorer
    from kiwoom_api.analysis.core.models import (
        RSIAnalysisRequest, RSIAnalysisResponse,
        TechnicalAnalysisResponse, AnalysisError, create_analysis_error
    )

logger = logging.getLogger(__name__)

router = APIRouter(tags=["종목분석"], prefix="/api/analysis")


# 종목명 매핑 (간단한 버전)
STOCK_NAMES = {
    "005930": "삼성전자",
    "000660": "SK하이닉스", 
    "373220": "LG에너지솔루션",
    "207940": "삼성바이오로직스",
    "005380": "현대차",
    "006400": "삼성SDI",
    "051910": "LG화학",
    "035420": "NAVER",
    "068270": "셀트리온",
    "035720": "카카오"
}


async def get_stock_chart_data(stock_code: str, days: int = 30) -> List[Dict]:
    """
    키움에서 일봉 차트 데이터를 가져옵니다.
    
    Args:
        stock_code: 종목코드
        days: 가져올 일수 (기본 30일)
    
    Returns:
        일봉 데이터 리스트
    """
    try:
        # 기준일자 설정 (오늘 기준)
        base_date = datetime.now().strftime("%Y%m%d")
        
        # 키움 API 요청 데이터
        chart_request = KiwoomStockChartApiRequest(
            data={
                "stk_cd": stock_code,
                "base_dt": base_date,
                "upd_stkpc_tp": "1"  # 수정주가 사용
            },
            cont_yn="N",
            next_key=""
        )
        
        # 키움 일봉 차트 API 호출
        result = await fn_ka10081(
            data=chart_request.data.model_dump(),
            cont_yn=chart_request.cont_yn,
            next_key=chart_request.next_key
        )
        
        # 응답 데이터 파싱
        if result.get("Code") != 200:
            raise Exception(f"키움 API 오류: {result.get('Header', {}).get('api-id', 'Unknown')}")
        
        body = result.get("Body", {})
        # Kiwoom API ka10081의 실제 데이터 필드
        chart_data_raw = body.get("stk_dt_pole_chart_qry", [])
        
        # 필요한 일수만큼 자르기
        chart_data = chart_data_raw[:days] if len(chart_data_raw) > days else chart_data_raw
        
        return chart_data
        
    except Exception as e:
        logger.error(f"차트 데이터 조회 실패 ({stock_code}): {e}")
        raise HTTPException(
            status_code=500,
            detail=f"차트 데이터 조회 실패: {str(e)}"
        )


def get_stock_name(stock_code: str) -> str:
    """종목코드에서 종목명 조회"""
    return STOCK_NAMES.get(stock_code, f"종목{stock_code}")


async def _calculate_rsi_internal(stock_code: str, period: int = 14) -> RSIAnalysisResponse:
    """
    내부용 RSI 계산 함수 (FastAPI dependency 없이 사용)
    """
    logger.info(f"RSI 분석 시작: {stock_code}, 기간: {period}일")
    
    # 차트 데이터 조회 (RSI 계산에 필요한 충분한 데이터)
    required_days = period + 10  # 여유 데이터
    chart_data = await get_stock_chart_data(stock_code, required_days)
    
    if len(chart_data) < period + 1:
        raise HTTPException(
            status_code=400,
            detail=f"RSI 계산을 위한 충분한 데이터가 없습니다. 필요: {period+1}일, 보유: {len(chart_data)}일"
        )
    
    # 종가 데이터 추출 (최신 데이터가 먼저 오므로 역순 정렬)
    prices = []
    for data in reversed(chart_data):  # 시간순으로 정렬
        close_price = float(data.get("cur_prc", "0"))  # 종가 (현재가)
        if close_price > 0:
            prices.append(close_price)
    
    if len(prices) < period + 1:
        raise HTTPException(
            status_code=400,
            detail="유효한 가격 데이터가 부족합니다."
        )
    
    # RSI 계산
    rsi = calculate_rsi(prices, period)
    
    # RSI 점수화
    scorer = AnalysisScorer()
    score = scorer.score_rsi(rsi)
    interpretation = scorer.get_interpretation(score)
    
    # 분석 기간 계산
    start_date = chart_data[-1].get("dt", "")  # 가장 오래된 데이터 날짜
    end_date = chart_data[0].get("dt", "")    # 가장 최근 데이터 날짜
    data_period = f"{period}일 ({start_date} ~ {end_date})"
    
    logger.info(f"RSI 분석 완료: {stock_code}, RSI={rsi}, 점수={score}")
    
    return RSIAnalysisResponse(
        stock_code=stock_code,
        stock_name=get_stock_name(stock_code),
        rsi=rsi,
        score=score,
        interpretation=interpretation,
        calculation_time=datetime.now(),
        data_period=data_period
    )


@router.get(
    "/rsi/{stock_code}",
    response_model=RSIAnalysisResponse,
    summary="RSI 분석",
    description="키움 API 데이터를 사용하여 RSI를 계산하고 점수화합니다."
)
async def analyze_rsi(
    stock_code: str = Path(..., description="6자리 종목코드", example="005930"),
    period: int = Query(default=14, description="RSI 계산 기간", ge=5, le=50, example=14)
) -> RSIAnalysisResponse:
    """
    RSI 분석 API
    
    Args:
        stock_code: 6자리 종목코드 (예: 005930)
        period: RSI 계산 기간 (기본 14일)
    
    Returns:
        RSI 분석 결과
    """
    try:
        return await _calculate_rsi_internal(stock_code, period)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RSI 분석 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"RSI 분석 중 오류가 발생했습니다: {str(e)}"
        )


@router.get(
    "/technical/{stock_code}",
    response_model=TechnicalAnalysisResponse,
    summary="기술적 분석",
    description="RSI를 포함한 기술적 지표들을 종합 분석합니다."
)
async def analyze_technical(
    stock_code: str = Path(..., description="6자리 종목코드", example="005930")
) -> TechnicalAnalysisResponse:
    """
    기술적 분석 API
    
    현재는 RSI만 구현되어 있으며, 향후 OBV, 이동평균선 등이 추가될 예정입니다.
    
    Args:
        stock_code: 6자리 종목코드
    
    Returns:
        기술적 분석 종합 결과
    """
    try:
        logger.info(f"기술적 분석 시작: {stock_code}")
        
        # 차트 데이터 조회 (기술적 분석에 필요한 충분한 데이터)
        required_days = 60  # 60일 이동평균 계산을 위해
        chart_data = await get_stock_chart_data(stock_code, required_days)
        
        if len(chart_data) < 20:
            raise HTTPException(
                status_code=400,
                detail=f"기술적 분석을 위한 충분한 데이터가 없습니다. 필요: 20일, 보유: {len(chart_data)}일"
            )
        
        # 데이터 추출 (최신 데이터가 먼저 오므로 역순 정렬)
        prices = []
        volumes = []
        for data in reversed(chart_data):  # 시간순으로 정렬
            close_price = float(data.get("cur_prc", "0"))  # 종가 (현재가)
            volume = int(data.get("trde_qty", "0"))  # 거래량
            if close_price > 0:
                prices.append(close_price)
                volumes.append(volume)
        
        if len(prices) < 20:
            raise HTTPException(
                status_code=400,
                detail="유효한 가격 데이터가 부족합니다."
            )
        
        # RSI 분석
        rsi_result = await _calculate_rsi_internal(stock_code, 14)
        
        # OBV 계산
        obv_value = calculate_obv(prices, volumes) if len(prices) >= 2 else 0.0
        
        # 이동평균 계산
        sma_20 = calculate_sma(prices, 20) if len(prices) >= 20 else 0.0
        sma_60 = calculate_sma(prices, 60) if len(prices) >= 60 else 0.0
        
        # 가격 추세 판단 (최근 5일 기준)
        recent_prices = prices[-5:]
        price_trend = "neutral"
        if len(recent_prices) >= 2:
            if recent_prices[-1] > recent_prices[0]:
                price_trend = "up"
            elif recent_prices[-1] < recent_prices[0]:
                price_trend = "down"
        
        # 점수 계산
        scorer = AnalysisScorer()
        obv_score = scorer.score_obv(obv_value, price_trend)
        sma_score = scorer.score_sma_trend(prices[-1], sma_20, sma_60) if len(prices) >= 60 else 0.0
        
        indicators = {
            "rsi": rsi_result.rsi,
            "obv": obv_value,
            "sma_20": sma_20,
            "sma_60": sma_60,
            "sentiment": 0.0  # TODO: 투자심리도 추가
        }
        
        scores = {
            "rsi": rsi_result.score,
            "obv": obv_score,
            "sma": sma_score,
            "sentiment": 0.0
        }
        
        # 기술적 분석 종합 점수
        tech_result = scorer.calculate_technical_score(
            rsi_score=rsi_result.score,
            obv_score=obv_score,
            sma_score=sma_score
        )
        
        logger.info(f"기술적 분석 완료: {stock_code}, 종합점수={tech_result['total_score']}")
        
        return TechnicalAnalysisResponse(
            stock_code=stock_code,
            stock_name=get_stock_name(stock_code),
            indicators=indicators,
            scores=scores,
            total_score=tech_result["total_score"],
            max_score=tech_result["max_score"],
            percentage=tech_result["percentage"],
            interpretation=tech_result["interpretation"],
            calculation_time=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"기술적 분석 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"기술적 분석 중 오류가 발생했습니다: {str(e)}"
        )


@router.get(
    "/health",
    summary="분석 시스템 헬스체크",
    description="분석 시스템의 상태를 확인합니다."
)
async def health_check():
    """분석 시스템 헬스체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": "0.1.0",
        "available_analyses": [
            "RSI 분석 (14일 기간)",
            "기술적 분석 (RSI + OBV + 이동평균선)"
        ],
        "indicators": {
            "rsi": "상대강도지수 (과매수/과매도 판단)",
            "obv": "거래량 기반 모멘텀 지표",
            "sma": "이동평균선 추세 분석 (20일/60일)",
            "ema": "지수이동평균 (구현 완료)"
        },
        "planned_features": [
            "PER/PBR 재무 분석",
            "뉴스/공시 재료 분석",
            "투자심리도 분석",
            "종합 분석 시스템"
        ]
    }