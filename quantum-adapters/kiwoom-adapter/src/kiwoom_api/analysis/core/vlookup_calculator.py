"""
Google Sheets VLOOKUP 계산 함수 구현

구글 시트에서 사용되는 18개의 VLOOKUP 공식을 Python 함수로 완전 구현합니다.
각 함수는 구글 시트의 IF-VLOOKUP 패턴과 동일한 로직을 따릅니다.
"""

import sys
from pathlib import Path

# Handle both relative and absolute imports for different execution contexts
try:
    from .evaluation_criteria import EvaluationCriteria
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from kiwoom_api.analysis.core.evaluation_criteria import EvaluationCriteria

from typing import Optional, Dict, Any


class VLOOKUPCalculator:
    """Google Sheets VLOOKUP 계산 함수 모음"""
    
    def __init__(self):
        self.criteria = EvaluationCriteria()
    
    # ==============================================
    # 재무 영역 (5개 함수)
    # ==============================================
    
    def calculate_sales_score(self, current_sales: float, previous_sales: float) -> int:
        """
        매출액 (전년 대비 증감률) 점수 계산
        
        공식: =VLOOKUP(IF(($D24-$D23)/$D23*100>=10,"A001",IF(($D23>$D24),"A006","Z999")),'디노테스트_평가기준'!B:D,3,FALSE)
        
        Args:
            current_sales: 당년도 매출액
            previous_sales: 전년도 매출액
            
        Returns:
            점수 (A001=+1, A006=-1, Z999=0)
        """
        if previous_sales <= 0:
            return self.criteria.vlookup("Z999")  # 0
        
        growth_rate = (current_sales - previous_sales) / previous_sales * 100
        
        if growth_rate >= 10:
            return self.criteria.vlookup("A001")  # +1
        elif current_sales < previous_sales:
            return self.criteria.vlookup("A006")  # -1
        else:
            return self.criteria.vlookup("Z999")  # 0
    
    def calculate_operating_profit_score(self, current_profit: float, previous_profit: float) -> int:
        """
        영업이익 (전년 대비 흑자/적자 전환) 점수 계산
        
        공식: =VLOOKUP(IF(AND($D25>0,$D24>0),"Z999",IF(AND($D25>0,$D24<0),"A003",IF(AND($D25<0,$D24>0),"A007",IF(AND($D25<0,$D24<0),"A008","Z999")))),'디노테스트_평가기준'!B:D,3,FALSE)
        
        Args:
            current_profit: 당년도 영업이익
            previous_profit: 전년도 영업이익
            
        Returns:
            점수 (A003=+1, A007=-1, A008=-2, Z999=0)
        """
        if current_profit > 0 and previous_profit > 0:
            return self.criteria.vlookup("Z999")  # 0 (흑자 지속)
        elif current_profit > 0 and previous_profit < 0:
            return self.criteria.vlookup("A003")  # +1 (적자→흑자)
        elif current_profit < 0 and previous_profit > 0:
            return self.criteria.vlookup("A007")  # -1 (흑자→적자)
        elif current_profit < 0 and previous_profit < 0:
            return self.criteria.vlookup("A008")  # -2 (적자→적자)
        else:
            return self.criteria.vlookup("Z999")  # 0
    
    def calculate_operating_margin_score(self, operating_margin: float) -> int:
        """
        영업이익률 점수 계산
        
        공식: =VLOOKUP(IF(D26>=10,"A002","Z999"),'디노테스트_평가기준'!B:D,3,FALSE)
        
        Args:
            operating_margin: 영업이익률 (%)
            
        Returns:
            점수 (A002=+1, Z999=0)
        """
        if operating_margin >= 10:
            return self.criteria.vlookup("A002")  # +1
        else:
            return self.criteria.vlookup("Z999")  # 0
    
    def calculate_retention_ratio_score(self, retention_ratio: float) -> int:
        """
        유보율 점수 계산
        
        공식: =VLOOKUP(IF(D27>=1000,"A004",IF(D27<=300,"A009","Z999")),'디노테스트_평가기준'!B:D,3,FALSE)
        
        Args:
            retention_ratio: 유보율 (%)
            
        Returns:
            점수 (A004=+1, A009=-1, Z999=0)
        """
        if retention_ratio >= 1000:
            return self.criteria.vlookup("A004")  # +1
        elif retention_ratio <= 300:
            return self.criteria.vlookup("A009")  # -1
        else:
            return self.criteria.vlookup("Z999")  # 0
    
    def calculate_debt_ratio_score(self, debt_ratio: float) -> int:
        """
        부채비율 점수 계산
        
        공식: =VLOOKUP(IF(D28<=50,"A005",IF(D28>=200,"A010","Z999")),'디노테스트_평가기준'!B:D,3,FALSE)
        
        Args:
            debt_ratio: 부채비율 (%)
            
        Returns:
            점수 (A005=+1, A010=-1, Z999=0)
        """
        if debt_ratio <= 50:
            return self.criteria.vlookup("A005")  # +1
        elif debt_ratio >= 200:
            return self.criteria.vlookup("A010")  # -1
        else:
            return self.criteria.vlookup("Z999")  # 0
    
    # ==============================================
    # 기술 영역 (3개 함수)
    # ==============================================
    
    def calculate_obv_score(self, obv_condition_met: bool) -> int:
        """
        OBV 점수 계산
        
        공식: =VLOOKUP(IF(D30="만족","B001","B004"),'디노테스트_평가기준'!B:D,3,FALSE)
        
        Args:
            obv_condition_met: OBV 조건 만족 여부
            
        Returns:
            점수 (B001=+1, B004=-1)
        """
        if obv_condition_met:
            return self.criteria.vlookup("B001")  # +1
        else:
            return self.criteria.vlookup("B004")  # -1
    
    def calculate_sentiment_score(self, sentiment_percentage: float) -> int:
        """
        투자심리도 점수 계산
        
        공식: =VLOOKUP(IF(D32<=25,"B002",IF(D32>=75,"B005","Z999")),'디노테스트_평가기준'!B:D,3,FALSE)
        
        Args:
            sentiment_percentage: 투자심리도 (%)
            
        Returns:
            점수 (B002=+1, B005=-1, Z999=0)
        """
        if sentiment_percentage <= 25:
            return self.criteria.vlookup("B002")  # +1 (침체)
        elif sentiment_percentage >= 75:
            return self.criteria.vlookup("B005")  # -1 (과열)
        else:
            return self.criteria.vlookup("Z999")  # 0
    
    def calculate_rsi_score(self, rsi_value: float) -> int:
        """
        RSI 점수 계산
        
        공식: =VLOOKUP(IF(D33<=30,"B003",IF(D33>=70,"B006","Z999")),'디노테스트_평가기준'!B:D,3,FALSE)
        
        Args:
            rsi_value: RSI 값
            
        Returns:
            점수 (B003=+1, B006=-1, Z999=0)
        """
        if rsi_value <= 30:
            return self.criteria.vlookup("B003")  # +1 (침체)
        elif rsi_value >= 70:
            return self.criteria.vlookup("B006")  # -1 (과열)
        else:
            return self.criteria.vlookup("Z999")  # 0
    
    # ==============================================
    # 가격 영역 (1개 함수)
    # ==============================================
    
    def calculate_52week_position_score(self, position_percentage: float) -> int:
        """
        52주 대비 현재 위치 점수 계산
        
        공식: =VLOOKUP(IF(D35<=-40,"C001",IF(D35<=-30,"C002",IF(D35<=-20,"C003",IF(D35>=300,"C004",IF(D35>=200,"C005",IF(D35>=100,"C006","Z999")))))),'디노테스트_평가기준'!B:D,3,FALSE)
        
        Args:
            position_percentage: 52주 대비 현재 위치 (%)
            
        Returns:
            점수 (C001=+3, C002=+2, C003=+1, C004=-3, C005=-2, C006=-1, Z999=0)
        """
        if position_percentage <= -40:
            return self.criteria.vlookup("C001")  # +3
        elif position_percentage <= -30:
            return self.criteria.vlookup("C002")  # +2
        elif position_percentage <= -20:
            return self.criteria.vlookup("C003")  # +1
        elif position_percentage >= 300:
            return self.criteria.vlookup("C004")  # -3
        elif position_percentage >= 200:
            return self.criteria.vlookup("C005")  # -2
        elif position_percentage >= 100:
            return self.criteria.vlookup("C006")  # -1
        else:
            return self.criteria.vlookup("Z999")  # 0
    
    # ==============================================
    # 재료 영역 (8개 함수)
    # ==============================================
    
    def calculate_imminent_event_score(self, has_imminent_event: bool) -> int:
        """
        구체화된 이벤트/호재 임박 점수 계산
        
        공식: =VLOOKUP(IF(UPPER($F38)="Y","D001","Z999"),'디노테스트_평가기준'!B:D,3,FALSE)
        
        Args:
            has_imminent_event: 호재 임박 여부
            
        Returns:
            점수 (D001=+1, Z999=0)
        """
        if has_imminent_event:
            return self.criteria.vlookup("D001")  # +1
        else:
            return self.criteria.vlookup("Z999")  # 0
    
    def calculate_leading_theme_score(self, is_leading_theme: bool) -> int:
        """
        확실한 주도 테마 점수 계산
        
        공식: =VLOOKUP(IF(UPPER($F39)="Y","D002","Z999"),'디노테스트_평가기준'!B:D,3,FALSE)
        
        Args:
            is_leading_theme: 주도 테마 여부
            
        Returns:
            점수 (D002=+1, Z999=0)
        """
        if is_leading_theme:
            return self.criteria.vlookup("D002")  # +1
        else:
            return self.criteria.vlookup("Z999")  # 0
    
    def calculate_institutional_supply_score(self, supply_percentage: float) -> int:
        """
        기관/외국인 수급 점수 계산
        
        공식: =VLOOKUP(IF(E40>=1,"D003","Z999"),'디노테스트_평가기준'!B:D,3,FALSE)
        
        Args:
            supply_percentage: 기관/외국인 순매수 비율 (상장주식수 대비 %)
            
        Returns:
            점수 (D003=+1, Z999=0)
        """
        if supply_percentage >= 1:
            return self.criteria.vlookup("D003")  # +1
        else:
            return self.criteria.vlookup("Z999")  # 0
    
    def calculate_high_dividend_score(self, dividend_yield: float) -> int:
        """
        고배당 점수 계산
        
        공식: =VLOOKUP(IF(E41>=2,"D004","Z999"),'디노테스트_평가기준'!B:D,3,FALSE)
        
        Args:
            dividend_yield: 배당수익률 (%)
            
        Returns:
            점수 (D004=+1, Z999=0)
        """
        if dividend_yield >= 2:
            return self.criteria.vlookup("D004")  # +1
        else:
            return self.criteria.vlookup("Z999")  # 0
    
    def calculate_earnings_surprise_score(self, has_earnings_surprise: bool) -> int:
        """
        어닝서프라이즈 점수 계산
        
        공식: =VLOOKUP(IF(UPPER($F42)="Y","D005","Z999"),'디노테스트_평가기준'!B:D,3,FALSE)
        
        Args:
            has_earnings_surprise: 실적 서프라이즈 여부
            
        Returns:
            점수 (D005=+1, Z999=0)
        """
        if has_earnings_surprise:
            return self.criteria.vlookup("D005")  # +1
        else:
            return self.criteria.vlookup("Z999")  # 0
    
    def calculate_unfaithful_disclosure_score(self, has_unfaithful_disclosure: bool) -> int:
        """
        불성실 공시 점수 계산
        
        공식: =VLOOKUP(IF(UPPER($F43)="Y","D006","Z999"),'디노테스트_평가기준'!B:D,3,FALSE)
        
        Args:
            has_unfaithful_disclosure: 불성실 공시 여부
            
        Returns:
            점수 (D006=-1, Z999=0)
        """
        if has_unfaithful_disclosure:
            return self.criteria.vlookup("D006")  # -1
        else:
            return self.criteria.vlookup("Z999")  # 0
    
    def calculate_negative_news_score(self, has_negative_news: bool) -> int:
        """
        악재뉴스 점수 계산
        
        공식: =VLOOKUP(IF(UPPER($F44)="Y","D007","Z999"),'디노테스트_평가기준'!B:D,3,FALSE)
        
        Args:
            has_negative_news: 악재뉴스 여부
            
        Returns:
            점수 (D007=-1, Z999=0)
        """
        if has_negative_news:
            return self.criteria.vlookup("D007")  # -1
        else:
            return self.criteria.vlookup("Z999")  # 0
    
    def calculate_interest_coverage_score(self, interest_coverage_ratio: Optional[float]) -> int:
        """
        이자보상배율 점수 계산
        
        공식 (3개 공식 조합):
        1. =INDEX(IMPORTHTML($J$3&G19,"table"),18,5)  # 데이터 수집
        2. =IF(E48<1,"Y","N")                         # 판정
        3. =VLOOKUP(IF(UPPER($F48)="Y","D009","Z999"),'디노테스트_평가기준'!B:D,3,FALSE)  # 점수
        
        Args:
            interest_coverage_ratio: 이자보상배율 (None이면 데이터 없음)
            
        Returns:
            점수 (D009=-1, Z999=0)
        """
        if interest_coverage_ratio is None:
            return self.criteria.vlookup("Z999")  # 0
        
        if interest_coverage_ratio < 1:
            return self.criteria.vlookup("D009")  # -1 (위험)
        else:
            return self.criteria.vlookup("Z999")  # 0
    
    # ==============================================
    # 종합 계산 함수들
    # ==============================================
    
    def calculate_all_scores(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        모든 18개 VLOOKUP 점수 일괄 계산
        
        Args:
            data: 종목 데이터 딕셔너리
            
        Returns:
            각 영역별 점수와 개별 점수들
        """
        # 재무 영역 (5개)
        financial_scores = {
            'sales': self.calculate_sales_score(
                data.get('current_sales', 0), 
                data.get('previous_sales', 1)
            ),
            'operating_profit': self.calculate_operating_profit_score(
                data.get('current_profit', 0), 
                data.get('previous_profit', 0)
            ),
            'operating_margin': self.calculate_operating_margin_score(
                data.get('operating_margin', 0)
            ),
            'retention_ratio': self.calculate_retention_ratio_score(
                data.get('retention_ratio', 0)
            ),
            'debt_ratio': self.calculate_debt_ratio_score(
                data.get('debt_ratio', 0)
            )
        }
        
        # 기술 영역 (3개)
        technical_scores = {
            'obv': self.calculate_obv_score(
                data.get('obv_satisfied', False)
            ),
            'sentiment': self.calculate_sentiment_score(
                data.get('sentiment_percentage', 50)
            ),
            'rsi': self.calculate_rsi_score(
                data.get('rsi_value', 50)
            )
        }
        
        # 가격 영역 (1개)
        price_scores = {
            '52week_position': self.calculate_52week_position_score(
                data.get('position_52w', 0)
            )
        }
        
        # 재료 영역 (8개)
        material_scores = {
            'imminent_event': self.calculate_imminent_event_score(
                data.get('has_imminent_event', False)
            ),
            'leading_theme': self.calculate_leading_theme_score(
                data.get('is_leading_theme', False)
            ),
            'institutional_supply': self.calculate_institutional_supply_score(
                data.get('institutional_supply', 0)
            ),
            'high_dividend': self.calculate_high_dividend_score(
                data.get('dividend_yield', 0)
            ),
            'earnings_surprise': self.calculate_earnings_surprise_score(
                data.get('has_earnings_surprise', False)
            ),
            'unfaithful_disclosure': self.calculate_unfaithful_disclosure_score(
                data.get('has_unfaithful_disclosure', False)
            ),
            'negative_news': self.calculate_negative_news_score(
                data.get('has_negative_news', False)
            ),
            'interest_coverage': self.calculate_interest_coverage_score(
                data.get('interest_coverage_ratio')
            )
        }
        
        return {
            'financial': financial_scores,
            'technical': technical_scores,
            'price': price_scores,
            'material': material_scores,
            'totals': {
                'financial_sum': sum(financial_scores.values()),
                'technical_sum': sum(technical_scores.values()),
                'price_sum': sum(price_scores.values()),
                'material_sum': sum(material_scores.values())
            }
        }


# 테스트 함수
def test_vlookup_calculator():
    """VLOOKUP 계산기 테스트"""
    calculator = VLOOKUPCalculator()
    
    print("=== VLOOKUP 계산기 테스트 ===")
    
    # 재무 영역 테스트
    print("\n1. 재무 영역 테스트:")
    print(f"매출액 (증가 15%): {calculator.calculate_sales_score(1150, 1000)}")  # 예상: +1
    print(f"매출액 (감소 10%): {calculator.calculate_sales_score(900, 1000)}")   # 예상: -1
    print(f"영업이익 (적자→흑자): {calculator.calculate_operating_profit_score(100, -50)}")  # 예상: +1
    print(f"영업이익률 12%: {calculator.calculate_operating_margin_score(12)}")  # 예상: +1
    print(f"유보율 1200%: {calculator.calculate_retention_ratio_score(1200)}")   # 예상: +1
    print(f"부채비율 30%: {calculator.calculate_debt_ratio_score(30)}")          # 예상: +1
    
    # 기술 영역 테스트
    print("\n2. 기술 영역 테스트:")
    print(f"OBV 만족: {calculator.calculate_obv_score(True)}")        # 예상: +1
    print(f"투자심리도 20%: {calculator.calculate_sentiment_score(20)}")  # 예상: +1
    print(f"RSI 25: {calculator.calculate_rsi_score(25)}")           # 예상: +1
    
    # 가격 영역 테스트
    print("\n3. 가격 영역 테스트:")
    print(f"52주 대비 -45%: {calculator.calculate_52week_position_score(-45)}")  # 예상: +3
    
    # 재료 영역 테스트
    print("\n4. 재료 영역 테스트:")
    print(f"호재 임박: {calculator.calculate_imminent_event_score(True)}")        # 예상: +1
    print(f"고배당 3%: {calculator.calculate_high_dividend_score(3)}")           # 예상: +1
    print(f"이자보상배율 0.8: {calculator.calculate_interest_coverage_score(0.8)}")  # 예상: -1
    
    # 종합 테스트
    print("\n5. 종합 테스트:")
    test_data = {
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
    
    all_scores = calculator.calculate_all_scores(test_data)
    print(f"재무 총합: {all_scores['totals']['financial_sum']}")
    print(f"기술 총합: {all_scores['totals']['technical_sum']}")
    print(f"가격 총합: {all_scores['totals']['price_sum']}")
    print(f"재료 총합: {all_scores['totals']['material_sum']}")
    
    print("\n✅ 모든 테스트 완료!")


if __name__ == "__main__":
    test_vlookup_calculator()