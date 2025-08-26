"""
4개 영역별 점수 계산 로직 구현

Google Sheets의 영역별 점수 계산 공식을 구현합니다:
- 재무: =MAX(0,MIN(5,2+SUM(G23,G25,G27,G28,G29)))
- 기술: =MAX(0,MIN(5,2+SUM(G31,G33,G34)))  
- 가격: =MAX(0,MIN(5,2+G36))
- 재료: =MAX(0,MIN(5,2+SUM(G39:G46)))

각 영역은 0~5점 범위로 제한되며, 기본 점수 2점에서 시작합니다.
"""

import sys
from pathlib import Path

# Handle both relative and absolute imports for different execution contexts
try:
    from .vlookup_calculator import VLOOKUPCalculator
    from .evaluation_criteria import EvaluationCriteria
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from kiwoom_api.analysis.core.vlookup_calculator import VLOOKUPCalculator
    from kiwoom_api.analysis.core.evaluation_criteria import EvaluationCriteria

from typing import Dict, Any, List
from datetime import datetime


class AreaScorer:
    """4개 영역별 점수 계산 클래스"""
    
    def __init__(self):
        self.vlookup_calc = VLOOKUPCalculator()
        self.criteria = EvaluationCriteria()
    
    def calculate_financial_score(self, 
                                sales_score: int,
                                operating_profit_score: int,
                                operating_margin_score: int,
                                retention_ratio_score: int,
                                debt_ratio_score: int) -> Dict[str, Any]:
        """
        재무 영역 점수 계산
        
        공식: =MAX(0,MIN(5,2+SUM(G23,G25,G27,G28,G29)))
        
        Args:
            sales_score: 매출액 점수 (G23)
            operating_profit_score: 영업이익 점수 (G25)  
            operating_margin_score: 영업이익률 점수 (G27)
            retention_ratio_score: 유보율 점수 (G28)
            debt_ratio_score: 부채비율 점수 (G29)
            
        Returns:
            재무 영역 분석 결과
        """
        individual_scores = [
            sales_score,
            operating_profit_score, 
            operating_margin_score,
            retention_ratio_score,
            debt_ratio_score
        ]
        
        # 구글 시트 공식과 정확히 동일: MAX(0,MIN(5,2+SUM(...)))
        individual_sum = sum(individual_scores)
        total_score = max(0, min(5, 2 + individual_sum))
        
        return {
            "area": "재무",
            "individual_scores": {
                "sales": sales_score,
                "operating_profit": operating_profit_score,
                "operating_margin": operating_margin_score, 
                "retention_ratio": retention_ratio_score,
                "debt_ratio": debt_ratio_score
            },
            "individual_sum": individual_sum,
            "base_score": 2,
            "total_score": total_score,
            "max_score": 5,
            "percentage": (total_score / 5) * 100,
            "interpretation": self._get_interpretation(total_score, 5),
            "formula": f"MAX(0,MIN(5,2+SUM({individual_scores}))) = MAX(0,MIN(5,2+{individual_sum})) = {total_score}"
        }
    
    def calculate_technical_score(self,
                                obv_score: int,
                                sentiment_score: int, 
                                rsi_score: int) -> Dict[str, Any]:
        """
        기술 영역 점수 계산
        
        공식: =MAX(0,MIN(5,2+SUM(G31,G33,G34)))
        
        Args:
            obv_score: OBV 점수 (G31)
            sentiment_score: 투자심리도 점수 (G33)
            rsi_score: RSI 점수 (G34)
            
        Returns:
            기술 영역 분석 결과
        """
        individual_scores = [obv_score, sentiment_score, rsi_score]
        
        # 구글 시트 공식과 정확히 동일: MAX(0,MIN(5,2+SUM(...)))
        individual_sum = sum(individual_scores)
        total_score = max(0, min(5, 2 + individual_sum))
        
        return {
            "area": "기술",
            "individual_scores": {
                "obv": obv_score,
                "sentiment": sentiment_score,
                "rsi": rsi_score
            },
            "individual_sum": individual_sum,
            "base_score": 2,
            "total_score": total_score,
            "max_score": 5,
            "percentage": (total_score / 5) * 100,
            "interpretation": self._get_interpretation(total_score, 5),
            "formula": f"MAX(0,MIN(5,2+SUM({individual_scores}))) = MAX(0,MIN(5,2+{individual_sum})) = {total_score}"
        }
    
    def calculate_price_score(self, position_52w_score: int) -> Dict[str, Any]:
        """
        가격 영역 점수 계산
        
        공식: =MAX(0,MIN(5,2+G36))
        
        Args:
            position_52w_score: 52주 대비 위치 점수 (G36)
            
        Returns:
            가격 영역 분석 결과
        """
        # 구글 시트 공식과 정확히 동일: MAX(0,MIN(5,2+G36))
        total_score = max(0, min(5, 2 + position_52w_score))
        
        return {
            "area": "가격",
            "individual_scores": {
                "52week_position": position_52w_score
            },
            "individual_sum": position_52w_score,
            "base_score": 2,
            "total_score": total_score,
            "max_score": 5,
            "percentage": (total_score / 5) * 100,
            "interpretation": self._get_interpretation(total_score, 5),
            "formula": f"MAX(0,MIN(5,2+{position_52w_score})) = {total_score}"
        }
    
    def calculate_material_score(self,
                               imminent_event_score: int,
                               leading_theme_score: int,
                               institutional_supply_score: int, 
                               high_dividend_score: int,
                               earnings_surprise_score: int,
                               unfaithful_disclosure_score: int,
                               negative_news_score: int,
                               interest_coverage_score: int) -> Dict[str, Any]:
        """
        재료 영역 점수 계산
        
        공식: =MAX(0,MIN(5,2+SUM(G39:G46)))
        
        Args:
            imminent_event_score: 호재임박 점수 (G39)
            leading_theme_score: 주도테마 점수 (G40)
            institutional_supply_score: 기관수급 점수 (G41)
            high_dividend_score: 고배당 점수 (G42)
            earnings_surprise_score: 어닝서프라이즈 점수 (G43)
            unfaithful_disclosure_score: 불성실공시 점수 (G44)
            negative_news_score: 악재뉴스 점수 (G45)
            interest_coverage_score: 이자보상배율 점수 (G46)
            
        Returns:
            재료 영역 분석 결과
        """
        individual_scores = [
            imminent_event_score,
            leading_theme_score,
            institutional_supply_score,
            high_dividend_score,
            earnings_surprise_score,
            unfaithful_disclosure_score,
            negative_news_score,
            interest_coverage_score
        ]
        
        # 구글 시트 공식과 정확히 동일: MAX(0,MIN(5,2+SUM(...)))
        individual_sum = sum(individual_scores)
        total_score = max(0, min(5, 2 + individual_sum))
        
        return {
            "area": "재료",
            "individual_scores": {
                "imminent_event": imminent_event_score,
                "leading_theme": leading_theme_score,
                "institutional_supply": institutional_supply_score,
                "high_dividend": high_dividend_score,
                "earnings_surprise": earnings_surprise_score,
                "unfaithful_disclosure": unfaithful_disclosure_score,
                "negative_news": negative_news_score,
                "interest_coverage": interest_coverage_score
            },
            "individual_sum": individual_sum,
            "base_score": 2,
            "total_score": total_score,
            "max_score": 5,
            "percentage": (total_score / 5) * 100,
            "interpretation": self._get_interpretation(total_score, 5),
            "formula": f"MAX(0,MIN(5,2+SUM({individual_scores}))) = MAX(0,MIN(5,2+{individual_sum})) = {total_score}"
        }
    
    def calculate_comprehensive_score(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        종합 점수 계산 (4개 영역 통합)
        
        Args:
            stock_data: 종목 데이터
            
        Returns:
            종합 분석 결과
        """
        # 1. 모든 개별 VLOOKUP 점수 계산
        all_vlookup_scores = self.vlookup_calc.calculate_all_scores(stock_data)
        
        # 2. 각 영역별 점수 계산
        financial_result = self.calculate_financial_score(
            all_vlookup_scores['financial']['sales'],
            all_vlookup_scores['financial']['operating_profit'],
            all_vlookup_scores['financial']['operating_margin'],
            all_vlookup_scores['financial']['retention_ratio'],
            all_vlookup_scores['financial']['debt_ratio']
        )
        
        technical_result = self.calculate_technical_score(
            all_vlookup_scores['technical']['obv'],
            all_vlookup_scores['technical']['sentiment'],
            all_vlookup_scores['technical']['rsi']
        )
        
        price_result = self.calculate_price_score(
            all_vlookup_scores['price']['52week_position']
        )
        
        material_result = self.calculate_material_score(
            all_vlookup_scores['material']['imminent_event'],
            all_vlookup_scores['material']['leading_theme'],
            all_vlookup_scores['material']['institutional_supply'],
            all_vlookup_scores['material']['high_dividend'],
            all_vlookup_scores['material']['earnings_surprise'],
            all_vlookup_scores['material']['unfaithful_disclosure'],
            all_vlookup_scores['material']['negative_news'],
            all_vlookup_scores['material']['interest_coverage']
        )
        
        # 3. 총점 계산
        total_score = (
            financial_result['total_score'] +
            technical_result['total_score'] +
            price_result['total_score'] +
            material_result['total_score']
        )
        
        max_total_score = 20  # 5 + 5 + 5 + 5
        
        return {
            "stock_code": stock_data.get('stock_code', ''),
            "stock_name": stock_data.get('stock_name', ''),
            "calculation_time": datetime.now(),
            
            # 영역별 상세 결과
            "areas": {
                "financial": financial_result,
                "technical": technical_result,
                "price": price_result,
                "material": material_result
            },
            
            # 종합 결과
            "summary": {
                "financial_score": financial_result['total_score'],
                "technical_score": technical_result['total_score'],
                "price_score": price_result['total_score'],
                "material_score": material_result['total_score'],
                "total_score": total_score,
                "max_score": max_total_score,
                "percentage": (total_score / max_total_score) * 100,
                "grade": self._calculate_grade(total_score, max_total_score),
                "interpretation": self._get_comprehensive_interpretation(total_score),
                "recommendation": self._get_investment_recommendation(total_score)
            },
            
            # 개별 VLOOKUP 점수들 (디버깅용)
            "vlookup_details": all_vlookup_scores
        }
    
    def _get_interpretation(self, score: int, max_score: int) -> str:
        """점수를 해석으로 변환"""
        percentage = (score / max_score) * 100
        
        if percentage >= 80:
            return "매우 우수"
        elif percentage >= 60:
            return "우수"
        elif percentage >= 40:
            return "보통"
        elif percentage >= 20:
            return "미흡"
        else:
            return "매우 미흡"
    
    def _calculate_grade(self, total_score: int, max_score: int) -> str:
        """총점을 등급으로 변환"""
        percentage = (total_score / max_score) * 100
        
        if percentage >= 90:
            return "A+"
        elif percentage >= 85:
            return "A"
        elif percentage >= 80:
            return "B+"
        elif percentage >= 75:
            return "B"
        elif percentage >= 70:
            return "C+"
        elif percentage >= 60:
            return "C"
        elif percentage >= 50:
            return "D+"
        else:
            return "D"
    
    def _get_comprehensive_interpretation(self, total_score: int) -> str:
        """종합 점수 해석"""
        if total_score >= 18:
            return "최우선 매수 종목"
        elif total_score >= 15:
            return "적극 매수 종목"
        elif total_score >= 12:
            return "관심 종목"
        elif total_score >= 8:
            return "관망 종목"
        elif total_score >= 5:
            return "주의 종목"
        else:
            return "매도 검토 종목"
    
    def _get_investment_recommendation(self, total_score: int) -> str:
        """투자 추천"""
        if total_score >= 16:
            return "적극 매수"
        elif total_score >= 12:
            return "매수"
        elif total_score >= 8:
            return "관망"
        elif total_score >= 4:
            return "주의"
        else:
            return "매도"


# 테스트 함수
def test_area_scorer():
    """영역별 점수 계산기 테스트"""
    scorer = AreaScorer()
    
    print("=== 영역별 점수 계산기 테스트 ===")
    
    # 1. 재무 영역 테스트 (예: 모두 +1점일 때)
    print("\n1. 재무 영역 테스트:")
    financial_result = scorer.calculate_financial_score(1, 1, 1, 1, 1)
    print(f"개별 점수들: {list(financial_result['individual_scores'].values())}")
    print(f"개별 합계: {financial_result['individual_sum']}")
    print(f"공식: {financial_result['formula']}")
    print(f"최종 점수: {financial_result['total_score']}/5")
    
    # 2. 기술 영역 테스트 (예: 혼재 점수일 때)
    print("\n2. 기술 영역 테스트:")
    technical_result = scorer.calculate_technical_score(1, -1, 1)
    print(f"개별 점수들: {list(technical_result['individual_scores'].values())}")
    print(f"개별 합계: {technical_result['individual_sum']}")
    print(f"공식: {technical_result['formula']}")
    print(f"최종 점수: {technical_result['total_score']}/5")
    
    # 3. 가격 영역 테스트
    print("\n3. 가격 영역 테스트:")
    price_result = scorer.calculate_price_score(3)  # C001: -40% 이상
    print(f"개별 점수: {price_result['individual_scores']}")
    print(f"공식: {price_result['formula']}")
    print(f"최종 점수: {price_result['total_score']}/5")
    
    # 4. 재료 영역 테스트
    print("\n4. 재료 영역 테스트:")
    material_result = scorer.calculate_material_score(1, 0, 1, 1, 0, 0, 0, -1)
    print(f"개별 점수들: {list(material_result['individual_scores'].values())}")
    print(f"개별 합계: {material_result['individual_sum']}")
    print(f"공식: {material_result['formula']}")
    print(f"최종 점수: {material_result['total_score']}/5")
    
    # 5. 종합 테스트
    print("\n5. 종합 테스트:")
    test_data = {
        'stock_code': '005930',
        'stock_name': '삼성전자',
        'current_sales': 1100,
        'previous_sales': 1000,
        'current_profit': 100,
        'previous_profit': -50,
        'operating_margin': 12,
        'retention_ratio': 1200,
        'debt_ratio': 30,
        'obv_satisfied': True,
        'sentiment_percentage': 20,
        'rsi_value': 25,
        'position_52w': -45,
        'dividend_yield': 3,
        'interest_coverage_ratio': 0.8
    }
    
    comprehensive_result = scorer.calculate_comprehensive_score(test_data)
    summary = comprehensive_result['summary']
    
    print(f"재무 점수: {summary['financial_score']}/5")
    print(f"기술 점수: {summary['technical_score']}/5")
    print(f"가격 점수: {summary['price_score']}/5")
    print(f"재료 점수: {summary['material_score']}/5")
    print(f"총점: {summary['total_score']}/20 ({summary['percentage']:.1f}%)")
    print(f"등급: {summary['grade']}")
    print(f"해석: {summary['interpretation']}")
    print(f"추천: {summary['recommendation']}")
    
    print("\n✅ 모든 테스트 완료!")


if __name__ == "__main__":
    test_area_scorer()