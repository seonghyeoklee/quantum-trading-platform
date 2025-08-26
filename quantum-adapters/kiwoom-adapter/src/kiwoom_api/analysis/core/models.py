"""
분석 시스템 데이터 모델

Pydantic 모델을 사용하여 API 요청/응답 형식을 정의합니다.
"""

from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field


class RSIAnalysisRequest(BaseModel):
    """RSI 분석 요청 모델"""
    stock_code: str = Field(..., description="6자리 종목코드", example="005930")
    period: Optional[int] = Field(14, description="RSI 계산 기간", ge=5, le=50)


class RSIAnalysisResponse(BaseModel):
    """RSI 분석 응답 모델"""
    stock_code: str = Field(..., description="종목코드")
    stock_name: str = Field(..., description="종목명")
    rsi: float = Field(..., description="RSI 값", ge=0, le=100)
    score: float = Field(..., description="RSI 점수", ge=-1, le=1)
    interpretation: str = Field(..., description="해석")
    calculation_time: datetime = Field(..., description="계산 시점")
    data_period: str = Field(..., description="사용된 데이터 기간")
    
    class Config:
        json_schema_extra = {
            "example": {
                "stock_code": "005930",
                "stock_name": "삼성전자",
                "rsi": 65.24,
                "score": -0.76,
                "interpretation": "부정",
                "calculation_time": "2025-08-25T11:30:00",
                "data_period": "14일"
            }
        }


class TechnicalAnalysisResponse(BaseModel):
    """기술적 분석 응답 모델"""
    stock_code: str = Field(..., description="종목코드")
    stock_name: str = Field(..., description="종목명")
    indicators: Dict[str, float] = Field(..., description="기술적 지표들")
    scores: Dict[str, float] = Field(..., description="각 지표별 점수")
    total_score: float = Field(..., description="기술 영역 총점", ge=-4, le=4)
    max_score: float = Field(4.0, description="기술 영역 만점")
    percentage: float = Field(..., description="점수 백분율", ge=0, le=100)
    interpretation: str = Field(..., description="종합 해석")
    calculation_time: datetime = Field(..., description="계산 시점")
    
    class Config:
        json_schema_extra = {
            "example": {
                "stock_code": "005930",
                "stock_name": "삼성전자",
                "indicators": {
                    "rsi": 65.24,
                    "obv": 1250000,
                    "sma_20": 75200,
                    "sentiment": 45.5
                },
                "scores": {
                    "rsi": -0.76,
                    "obv": 0.3,
                    "sma": 0.2,
                    "sentiment": -0.1
                },
                "total_score": -0.36,
                "max_score": 4.0,
                "percentage": 45.5,
                "interpretation": "부정",
                "calculation_time": "2025-08-25T11:30:00"
            }
        }


class FinancialAnalysisResponse(BaseModel):
    """재무 분석 응답 모델"""
    stock_code: str = Field(..., description="종목코드")
    stock_name: str = Field(..., description="종목명")
    indicators: Dict[str, float] = Field(..., description="재무 지표들")
    scores: Dict[str, float] = Field(..., description="각 지표별 점수")
    total_score: float = Field(..., description="재무 영역 총점", ge=-3, le=3)
    max_score: float = Field(3.0, description="재무 영역 만점")
    percentage: float = Field(..., description="점수 백분율", ge=0, le=100)
    interpretation: str = Field(..., description="종합 해석")
    calculation_time: datetime = Field(..., description="계산 시점")


class ComprehensiveAnalysisResponse(BaseModel):
    """종합 분석 응답 모델"""
    stock_code: str = Field(..., description="종목코드")
    stock_name: str = Field(..., description="종목명")
    
    # 4개 영역별 점수
    financial_score: float = Field(..., description="재무 점수", ge=-3, le=3)
    technical_score: float = Field(..., description="기술 점수", ge=-4, le=4)
    price_score: float = Field(..., description="가격 점수", ge=-2, le=2)
    material_score: float = Field(..., description="재료 점수", ge=-5, le=5)
    
    # 총점 및 해석
    total_score: float = Field(..., description="총점", ge=-14, le=14)
    max_score: float = Field(14.0, description="만점")
    percentage: float = Field(..., description="점수 백분율", ge=0, le=100)
    grade: str = Field(..., description="등급 (A+, A, B+, B, C+, C, D)")
    interpretation: str = Field(..., description="종합 해석")
    recommendation: str = Field(..., description="투자 추천")
    
    calculation_time: datetime = Field(..., description="계산 시점")
    
    class Config:
        json_schema_extra = {
            "example": {
                "stock_code": "005930",
                "stock_name": "삼성전자",
                "financial_score": 1.2,
                "technical_score": -0.36,
                "price_score": 0.8,
                "material_score": 2.1,
                "total_score": 3.74,
                "max_score": 14.0,
                "percentage": 63.4,
                "grade": "B+",
                "interpretation": "관심 종목",
                "recommendation": "관망",
                "calculation_time": "2025-08-25T11:30:00"
            }
        }


class AnalysisError(BaseModel):
    """분석 에러 응답 모델"""
    error_code: str = Field(..., description="에러 코드")
    error_message: str = Field(..., description="에러 메시지")
    stock_code: Optional[str] = Field(None, description="종목코드")
    timestamp: datetime = Field(..., description="에러 발생 시점")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "INSUFFICIENT_DATA",
                "error_message": "RSI 계산을 위한 충분한 가격 데이터가 없습니다",
                "stock_code": "005930",
                "timestamp": "2025-08-25T11:30:00"
            }
        }


class MultiStockAnalysisRequest(BaseModel):
    """다종목 분석 요청 모델"""
    stock_codes: List[str] = Field(..., description="종목코드 리스트", min_items=1, max_items=20)
    analysis_type: str = Field("comprehensive", description="분석 유형")
    
    class Config:
        json_schema_extra = {
            "example": {
                "stock_codes": ["005930", "000660", "373220"],
                "analysis_type": "comprehensive"
            }
        }


class MultiStockAnalysisResponse(BaseModel):
    """다종목 분석 응답 모델"""
    analysis_type: str = Field(..., description="분석 유형")
    results: List[ComprehensiveAnalysisResponse] = Field(..., description="종목별 분석 결과")
    ranking: List[Dict[str, Any]] = Field(..., description="점수별 랭킹")
    summary: Dict[str, Any] = Field(..., description="요약 통계")
    calculation_time: datetime = Field(..., description="계산 시점")


# 편의 함수들
def create_analysis_error(error_code: str, error_message: str, 
                         stock_code: Optional[str] = None) -> AnalysisError:
    """분석 에러 응답 생성"""
    return AnalysisError(
        error_code=error_code,
        error_message=error_message,
        stock_code=stock_code,
        timestamp=datetime.now()
    )


def calculate_grade(total_score: float, max_score: float = 14.0) -> str:
    """점수를 등급으로 변환"""
    percentage = (total_score + max_score) / (2 * max_score) * 100
    
    if percentage >= 85:
        return "A+"
    elif percentage >= 80:
        return "A"
    elif percentage >= 75:
        return "B+"
    elif percentage >= 70:
        return "B"
    elif percentage >= 60:
        return "C+"
    elif percentage >= 50:
        return "C"
    else:
        return "D"


def get_investment_recommendation(total_score: float) -> str:
    """점수를 투자 추천으로 변환"""
    if total_score >= 10:
        return "적극 매수"
    elif total_score >= 7:
        return "매수"
    elif total_score >= 3:
        return "관심 종목"
    elif total_score >= 0:
        return "관망"
    elif total_score >= -3:
        return "주의"
    else:
        return "매도 검토"