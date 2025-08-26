"""
종합 분석 API 라우터

Google Sheets VLOOKUP 기반 주식 종합 분석 API를 제공합니다.
재무, 기술, 가격, 재료 4개 영역을 통합 분석하여 투자 판단 지표를 제공합니다.
"""

import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# 기본 BaseResponse 정의
class BaseResponse(BaseModel):
    """기본 응답 모델"""
    success: bool = Field(True, description="성공 여부")
    message: str = Field("", description="응답 메시지")
    data: Optional[Any] = Field(None, description="응답 데이터")

# Handle both relative and absolute imports for different execution contexts
try:
    from ..core.area_scorers import AreaScorer
    from ..indicators.financial_indicators import FinancialDataCollector
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from kiwoom_api.analysis.core.area_scorers import AreaScorer
    from kiwoom_api.analysis.indicators.financial_indicators import FinancialDataCollector


# 요청/응답 모델 정의
class StockAnalysisRequest(BaseModel):
    """주식 분석 요청 모델"""
    stock_code: str = Field(..., description="6자리 종목코드", example="005930")
    include_details: bool = Field(True, description="상세 분석 포함 여부")
    
    class Config:
        json_schema_extra = {
            "example": {
                "stock_code": "005930",
                "include_details": True
            }
        }


class CriteriaEvaluation(BaseModel):
    """평가 기준 적용 결과"""
    criterion: str = Field(..., description="평가 기준명")
    actual_value: str = Field(..., description="실제값")
    benchmark: str = Field(..., description="기준값")
    met: bool = Field(..., description="기준 충족 여부")
    points: int = Field(..., description="획득 점수")
    explanation: str = Field(..., description="설명")

# BaseDataInfo를 Dict[str, Any]로 단순화
BaseDataInfo = Dict[str, Any]

class CalculationProcess(BaseModel):
    """계산 과정 상세"""
    base_score: int = Field(..., description="기준 점수")
    earned_points: int = Field(..., description="획득 점수")
    formula: str = Field(..., description="계산 공식")
    step_by_step: List[str] = Field(..., description="단계별 계산 과정")
    final_score: int = Field(..., description="최종 점수")

class AreaScoreDetail(BaseModel):
    """영역별 상세 점수"""
    area: str = Field(..., description="영역명")
    individual_scores: Dict[str, int] = Field(..., description="개별 지표 점수들")
    individual_sum: int = Field(..., description="개별 점수 합계")
    base_score: int = Field(..., description="기준 점수")
    total_score: int = Field(..., description="최종 점수")
    max_score: int = Field(..., description="만점")
    percentage: float = Field(..., description="백분율")
    interpretation: str = Field(..., description="해석")
    formula: str = Field(..., description="계산 공식")
    
    # 확장된 필드들
    base_data: Dict[str, BaseDataInfo] = Field(..., description="기반 데이터")
    criteria_evaluation: List[CriteriaEvaluation] = Field(..., description="평가 기준 적용 결과")
    calculation: CalculationProcess = Field(..., description="계산 과정 상세")


class StockAnalysisResponse(BaseResponse):
    """주식 분석 응답 모델"""
    stock_code: str = Field(..., description="종목코드")
    stock_name: str = Field(..., description="종목명")
    calculation_time: datetime = Field(..., description="계산 시점")
    
    # 요약 정보
    summary: Dict[str, Any] = Field(..., description="요약 정보")
    
    # 영역별 상세 정보 (선택적)
    areas: Optional[Dict[str, AreaScoreDetail]] = Field(None, description="영역별 상세 점수")
    
    # 데이터 소스 정보
    data_sources: Dict[str, str] = Field(..., description="데이터 소스 정보")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "분석 완료",
                "data": None,
                "stock_code": "005930",
                "stock_name": "삼성전자",
                "calculation_time": "2025-08-25T15:30:00",
                "summary": {
                    "financial_score": 4,
                    "technical_score": 3,
                    "price_score": 5,
                    "material_score": 2,
                    "total_score": 14,
                    "max_score": 20,
                    "percentage": 70.0,
                    "grade": "B",
                    "interpretation": "관심 종목",
                    "recommendation": "관망"
                },
                "data_sources": {
                    "basic_info": "Kiwoom ka10001",
                    "historical": "Kiwoom ka10005",
                    "institutional": "Kiwoom ka10045",
                    "financial": "DART API",
                    "technical": "Calculated"
                }
            }
        }


class MultiStockAnalysisRequest(BaseModel):
    """다종목 분석 요청 모델"""
    stock_codes: List[str] = Field(..., description="종목코드 리스트", min_items=1, max_items=10)
    sort_by: str = Field("total_score", description="정렬 기준", pattern="^(total_score|financial_score|technical_score|price_score|material_score)$")
    sort_desc: bool = Field(True, description="내림차순 정렬 여부")
    
    class Config:
        json_schema_extra = {
            "example": {
                "stock_codes": ["005930", "000660", "373220"],
                "sort_by": "total_score",
                "sort_desc": True
            }
        }


class MultiStockAnalysisResponse(BaseResponse):
    """다종목 분석 응답 모델"""
    analysis_count: int = Field(..., description="분석된 종목 수")
    calculation_time: datetime = Field(..., description="계산 시점")
    results: List[StockAnalysisResponse] = Field(..., description="종목별 분석 결과")
    ranking_summary: Dict[str, Any] = Field(..., description="랭킹 요약")


# 라우터 생성
router = APIRouter(prefix="/api/analysis", tags=["종합 분석"])

# 전역 객체
area_scorer = AreaScorer()
data_collector = FinancialDataCollector()


@router.post("/comprehensive/{stock_code}", 
             response_model=StockAnalysisResponse,
             summary="종합 주식 분석",
             description="Google Sheets VLOOKUP 기반 4개 영역(재무, 기술, 가격, 재료) 종합 분석")
async def analyze_comprehensive(
    stock_code: str = Path(..., description="6자리 종목코드 (예: 005930=삼성전자)", pattern="^[0-9]{6}$", example="005930"),
    include_details: bool = Query(True, description="영역별 상세 점수 포함 여부")
):
    """
    종합 주식 분석 - Google Sheets VLOOKUP 완전 재현
    
    Google Sheets의 VLOOKUP 공식을 기반으로 한 완전한 주식 분석을 제공합니다.
    
    **예시: 삼성전자 (005930) 분석**
    ```
    POST /api/analysis/comprehensive/005930?include_details=true
    ```
    
    **분석 영역:**
    - **재무 영역**: 매출액, 영업이익, 영업이익률, 유보율, 부채비율 (0~5점)
      - 매출 증가율 10% 이상 → +1점 (A001)
      - 영업이익 흑자전환 → +1점 (A003)
      - 유보율 1,000% 이상 → +1점 (A004)
    - **기술 영역**: OBV, 투자심리도, RSI (0~5점)
      - RSI 30% 이하 (침체) → +1점 (B003)
      - OBV 조건 만족 → +1점 (B001)
    - **가격 영역**: 52주 대비 현재 위치 (0~5점)
      - 52주 최저가 대비 -40% 이상 → +3점 (C001)
    - **재료 영역**: 호재/악재, 배당, 이자보상배율 등 (0~5점)
      - 배당수익률 2% 이상 → +1점 (D004)
      - 어닝서프라이즈 → +1점 (D005)
    
    **점수 계산 공식**: MAX(0,MIN(5,2+SUM(개별점수들)))
    **총점**: 0~20점 (각 영역 최대 5점)
    
    **주요 종목코드:**
    - 005930: 삼성전자
    - 000660: SK하이닉스  
    - 005380: 현대차
    - 035420: NAVER
    - 051910: LG화학
    
    **데이터 소스:**
    - 키움증권 API (ka10001, ka10005, ka10045) - 기본 주식정보
    - DART API (재무제표 상세 정보) - 정확한 재무비율
    - 뉴스 크롤링 (호재/악재 판별) - 실시간 감성분석
    - 실시간 계산 (기술적 지표) - RSI, OBV, 투자심리도
    """
    try:
        # 1. 종합 데이터 수집
        stock_data = await data_collector.get_comprehensive_data(stock_code)
        
        if not stock_data.get('stock_name'):
            raise HTTPException(
                status_code=404,
                detail=f"종목코드 {stock_code}에 대한 정보를 찾을 수 없습니다."
            )
        
        # 2. 종합 점수 계산
        comprehensive_result = area_scorer.calculate_comprehensive_score(stock_data)
        
        # 3. 응답 데이터 구성
        response_data = StockAnalysisResponse(
            success=True,
            message="분석 완료",
            stock_code=stock_code,
            stock_name=stock_data['stock_name'],
            calculation_time=datetime.now(),
            summary=comprehensive_result['summary'],
            data_sources=stock_data.get('data_sources', {})
        )
        
        # 상세 정보 포함 시
        if include_details:
            areas_detail = {}
            for area_name, area_result in comprehensive_result['areas'].items():
                areas_detail[area_name] = AreaScoreDetail(**area_result)
            response_data.areas = areas_detail
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"분석 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/financial/{stock_code}",
             summary="재무 영역 분석",
             description="재무 영역만 단독 분석 (매출액, 영업이익, 영업이익률, 유보율, 부채비율)")
async def analyze_financial(stock_code: str = Path(..., description="6자리 종목코드 (예: 005930=삼성전자)", pattern="^[0-9]{6}$", example="005930")):
    """재무 영역 단독 분석"""
    try:
        stock_data = await data_collector.get_comprehensive_data(stock_code)
        comprehensive_result = area_scorer.calculate_comprehensive_score(stock_data)
        
        return {
            "success": True,
            "message": "재무 분석 완료",
            "stock_code": stock_code,
            "stock_name": stock_data.get('stock_name', ''),
            "calculation_time": datetime.now(),
            "financial_analysis": comprehensive_result['areas']['financial'],
            "data_sources": stock_data.get('data_sources', {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/technical/{stock_code}",
             summary="기술 영역 분석", 
             description="기술 영역만 단독 분석 (OBV, 투자심리도, RSI)")
async def analyze_technical(stock_code: str = Path(..., description="6자리 종목코드 (예: 005930=삼성전자)", pattern="^[0-9]{6}$", example="005930")):
    """기술 영역 단독 분석"""
    try:
        stock_data = await data_collector.get_comprehensive_data(stock_code)
        comprehensive_result = area_scorer.calculate_comprehensive_score(stock_data)
        
        return {
            "success": True,
            "message": "기술 분석 완료",
            "stock_code": stock_code,
            "stock_name": stock_data.get('stock_name', ''),
            "calculation_time": datetime.now(),
            "technical_analysis": comprehensive_result['areas']['technical'],
            "data_sources": stock_data.get('data_sources', {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/price/{stock_code}",
             summary="가격 영역 분석",
             description="가격 영역만 단독 분석 (52주 대비 현재 위치)")
async def analyze_price(stock_code: str = Path(..., description="6자리 종목코드 (예: 005930=삼성전자)", pattern="^[0-9]{6}$", example="005930")):
    """가격 영역 단독 분석"""
    try:
        stock_data = await data_collector.get_comprehensive_data(stock_code)
        comprehensive_result = area_scorer.calculate_comprehensive_score(stock_data)
        
        return {
            "success": True,
            "message": "가격 분석 완료",
            "stock_code": stock_code,
            "stock_name": stock_data.get('stock_name', ''),
            "calculation_time": datetime.now(),
            "price_analysis": comprehensive_result['areas']['price'],
            "data_sources": stock_data.get('data_sources', {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/material/{stock_code}",
             summary="재료 영역 분석",
             description="재료 영역만 단독 분석 (호재/악재, 배당, 이자보상배율 등)")
async def analyze_material(stock_code: str = Path(..., description="6자리 종목코드 (예: 005930=삼성전자)", pattern="^[0-9]{6}$", example="005930")):
    """재료 영역 단독 분석"""
    try:
        stock_data = await data_collector.get_comprehensive_data(stock_code)
        comprehensive_result = area_scorer.calculate_comprehensive_score(stock_data)
        
        return {
            "success": True,
            "message": "재료 분석 완료",
            "stock_code": stock_code,
            "stock_name": stock_data.get('stock_name', ''),
            "calculation_time": datetime.now(),
            "material_analysis": comprehensive_result['areas']['material'],
            "data_sources": stock_data.get('data_sources', {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multi-stock",
             response_model=MultiStockAnalysisResponse,
             summary="다종목 종합 분석",
             description="여러 종목의 종합 분석 및 랭킹 제공")
async def analyze_multi_stock(request: MultiStockAnalysisRequest):
    """
    다종목 종합 분석
    
    여러 종목을 동시에 분석하고 점수순으로 랭킹을 제공합니다.
    최대 10개 종목까지 동시 분석 가능합니다.
    """
    try:
        results = []
        
        # 각 종목별 분석 실행
        for stock_code in request.stock_codes:
            try:
                stock_data = await data_collector.get_comprehensive_data(stock_code)
                comprehensive_result = area_scorer.calculate_comprehensive_score(stock_data)
                
                analysis_result = StockAnalysisResponse(
                    success=True,
                    message="분석 완료",
                    stock_code=stock_code,
                    stock_name=stock_data.get('stock_name', ''),
                    calculation_time=datetime.now(),
                    summary=comprehensive_result['summary'],
                    data_sources=stock_data.get('data_sources', {})
                )
                
                results.append(analysis_result)
                
            except Exception as e:
                # 개별 종목 분석 실패 시 오류 정보 포함
                error_result = StockAnalysisResponse(
                    success=False,
                    message=f"분석 실패: {str(e)}",
                    stock_code=stock_code,
                    stock_name="분석 실패",
                    calculation_time=datetime.now(),
                    summary={
                        "total_score": 0,
                        "grade": "N/A",
                        "interpretation": "분석 실패",
                        "recommendation": "N/A"
                    },
                    data_sources={}
                )
                results.append(error_result)
        
        # 정렬
        results.sort(
            key=lambda x: x.summary.get(request.sort_by, 0),
            reverse=request.sort_desc
        )
        
        # 랭킹 요약 생성
        successful_results = [r for r in results if r.success]
        ranking_summary = {
            "total_requested": len(request.stock_codes),
            "successful_analysis": len(successful_results),
            "failed_analysis": len(results) - len(successful_results),
            "top_performer": {
                "stock_code": successful_results[0].stock_code,
                "stock_name": successful_results[0].stock_name,
                "total_score": successful_results[0].summary.get("total_score", 0)
            } if successful_results else None,
            "average_score": sum(r.summary.get("total_score", 0) for r in successful_results) / len(successful_results) if successful_results else 0
        }
        
        return MultiStockAnalysisResponse(
            success=True,
            message=f"{len(successful_results)}개 종목 분석 완료",
            analysis_count=len(successful_results),
            calculation_time=datetime.now(),
            results=results,
            ranking_summary=ranking_summary
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"다종목 분석 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/criteria",
            summary="평가 기준표 조회",
            description="Google Sheets '디노테스트_평가기준' 시트와 동일한 평가 기준표")
async def get_evaluation_criteria():
    """평가 기준표 조회"""
    from ..core.evaluation_criteria import EvaluationCriteria
    
    return {
        "success": True,
        "message": "평가 기준표 조회 완료",
        "criteria_table": EvaluationCriteria.CRITERIA_TABLE,
        "categories": {
            "재무": EvaluationCriteria.get_category_codes("재무"),
            "기술": EvaluationCriteria.get_category_codes("기술"), 
            "가격": EvaluationCriteria.get_category_codes("가격"),
            "재료": EvaluationCriteria.get_category_codes("재료")
        }
    }


@router.get("/health",
            summary="분석 시스템 상태 확인",
            description="분석 시스템 구성요소 상태 확인")
async def health_check():
    """분석 시스템 상태 확인"""
    try:
        # 간단한 데이터 수집 테스트
        test_result = await data_collector.get_stock_basic_info("005930")
        
        return {
            "success": True,
            "message": "분석 시스템 정상",
            "timestamp": datetime.now(),
            "components": {
                "area_scorer": "정상",
                "data_collector": "정상",
                "kiwoom_api": "정상" if test_result else "점검 필요",
                "dart_api": "설정됨" if data_collector.dart_api_key else "미설정"
            },
            "version": "1.0.0"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"분석 시스템 점검 필요: {str(e)}",
            "timestamp": datetime.now(),
            "components": {
                "area_scorer": "점검 필요",
                "data_collector": "점검 필요",
                "kiwoom_api": "점검 필요",
                "dart_api": "점검 필요"
            }
        }