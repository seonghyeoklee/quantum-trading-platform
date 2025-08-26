"""
지표 점수화 시스템

Google Sheets 방식의 점수화 로직을 구현합니다.
각 지표를 -1~+1 범위로 점수화하여 표준화된 분석 결과를 제공합니다.
"""

from typing import Dict, Any


class AnalysisScorer:
    """분석 지표 점수화 클래스"""
    
    @staticmethod
    def score_rsi(rsi: float) -> float:
        """
        RSI를 -1~+1 점수로 변환
        
        Args:
            rsi: RSI 값 (0-100)
        
        Returns:
            점수 (-1~+1)
            - RSI <= 30: +1.0 (과매도 → 매수 기회)
            - RSI >= 70: -1.0 (과매수 → 매도 신호)
            - 30 < RSI < 70: 선형 변환
        """
        if rsi <= 30:
            return 1.0  # 과매도 → 매수 기회
        elif rsi >= 70:
            return -1.0  # 과매수 → 매도 신호
        else:
            # 30-70 구간을 선형 변환: 50이 중립(0점)
            return (50 - rsi) / 20
    
    @staticmethod
    def score_per(per: float, industry_avg_per: float = None) -> float:
        """
        PER를 -1~+1 점수로 변환
        
        Args:
            per: PER 값
            industry_avg_per: 업종 평균 PER
        
        Returns:
            점수 (-1~+1)
        """
        if per <= 0:
            return -1.0  # 적자 기업
        
        if industry_avg_per is None:
            # 업종 평균이 없는 경우 절대값 기준
            if per <= 10:
                return 1.0  # 저평가
            elif per >= 25:
                return -1.0  # 고평가
            else:
                return (17.5 - per) / 7.5  # 선형 변환 (중립값 17.5)
        else:
            # 업종 평균 대비 상대 평가
            ratio = per / industry_avg_per
            if ratio <= 0.7:
                return 1.0  # 업종 평균 대비 저평가
            elif ratio >= 1.5:
                return -1.0  # 업종 평균 대비 고평가
            else:
                return (1.1 - ratio) / 0.4  # 선형 변환
    
    @staticmethod
    def score_pbr(pbr: float) -> float:
        """
        PBR을 -1~+1 점수로 변환
        
        Args:
            pbr: PBR 값
        
        Returns:
            점수 (-1~+1)
        """
        if pbr <= 0:
            return -1.0  # 부채초과
        
        if pbr <= 0.5:
            return 1.0  # 청산 가치 대비 저평가
        elif pbr >= 2.0:
            return -1.0  # 고평가
        else:
            return (1.25 - pbr) / 0.75  # 선형 변환 (중립값 1.25)
    
    @staticmethod
    def score_roe(roe: float, industry_avg_roe: float = None) -> float:
        """
        ROE를 -1~+1 점수로 변환
        
        Args:
            roe: ROE 값 (%)
            industry_avg_roe: 업종 평균 ROE
        
        Returns:
            점수 (-1~+1)
        """
        if industry_avg_roe is None:
            # 업종 평균이 없는 경우 절대값 기준
            if roe >= 15:
                return 1.0  # 우수
            elif roe <= 5:
                return -1.0  # 부진
            else:
                return (roe - 10) / 5  # 선형 변환 (중립값 10%)
        else:
            # 업종 평균 대비 상대 평가
            diff = roe - industry_avg_roe
            if diff >= 5:
                return 1.0
            elif diff <= -5:
                return -1.0
            else:
                return diff / 5
    
    @staticmethod
    def get_interpretation(score: float) -> str:
        """
        점수를 해석으로 변환
        
        Args:
            score: 점수 (-1~+1)
        
        Returns:
            해석 문자열
        """
        if score >= 0.5:
            return "매수"
        elif score >= 0.2:
            return "긍정"
        elif score >= -0.2:
            return "중립"
        elif score >= -0.5:
            return "부정"
        else:
            return "매도"
    
    @staticmethod
    def score_obv(obv: float, price_trend: str = "neutral") -> float:
        """
        OBV를 -1~+1 점수로 변환
        
        Args:
            obv: OBV 값
            price_trend: 가격 추세 ("up", "down", "neutral")
        
        Returns:
            점수 (-1~+1)
            - 가격 상승 + OBV 상승: 긍정적 신호
            - 가격 하락 + OBV 하락: 부정적 신호  
            - 가격과 OBV 다이버전스: 주의 신호
        """
        # OBV 자체 값으로는 의미가 적으므로 가격 추세와의 관계로 점수화
        if price_trend == "up" and obv > 0:
            return 0.8  # 가격 상승 + 거래량 증가
        elif price_trend == "down" and obv < 0:
            return -0.8  # 가격 하락 + 거래량 감소
        elif price_trend == "up" and obv < 0:
            return -0.3  # 다이버전스 (상승하지만 거래량 부족)
        elif price_trend == "down" and obv > 0:
            return 0.3  # 다이버전스 (하락하지만 거래량 증가)
        else:
            return 0.0  # 중립
    
    @staticmethod
    def score_sma_trend(current_price: float, sma_20: float, sma_60: float) -> float:
        """
        이동평균선 추세를 -1~+1 점수로 변환
        
        Args:
            current_price: 현재가
            sma_20: 20일 이동평균
            sma_60: 60일 이동평균
        
        Returns:
            점수 (-1~+1)
        """
        # 가격과 이동평균선 관계
        price_vs_sma20 = (current_price - sma_20) / sma_20 * 100  # %
        sma20_vs_sma60 = (sma_20 - sma_60) / sma_60 * 100  # %
        
        score = 0.0
        
        # 현재가가 20일선 위에 있으면 긍정적
        if price_vs_sma20 > 2:
            score += 0.4
        elif price_vs_sma20 < -2:
            score -= 0.4
        
        # 20일선이 60일선 위에 있으면 긍정적 (골든크로스)
        if sma20_vs_sma60 > 1:
            score += 0.6
        elif sma20_vs_sma60 < -1:
            score -= 0.6  # 데드크로스
        
        return max(-1.0, min(1.0, score))  # -1~+1 범위 제한
    
    @staticmethod
    def calculate_technical_score(rsi_score: float, obv_score: float = 0, 
                                sma_score: float = 0, sentiment_score: float = 0) -> Dict[str, Any]:
        """
        기술 영역 종합 점수 계산 (4점 만점)
        
        Args:
            rsi_score: RSI 점수
            obv_score: OBV 점수  
            sma_score: 이동평균선 점수
            sentiment_score: 투자심리도 점수
        
        Returns:
            기술 영역 분석 결과
        """
        total_score = rsi_score + obv_score + sma_score + sentiment_score
        
        return {
            "scores": {
                "rsi": rsi_score,
                "obv": obv_score,
                "sma": sma_score,
                "sentiment": sentiment_score
            },
            "total_score": total_score,
            "max_score": 4.0,
            "percentage": (total_score + 4) / 8 * 100,  # -4~+4를 0~100%로 변환
            "interpretation": AnalysisScorer.get_interpretation(total_score / 4)
        }


# 테스트용 함수
def test_scoring():
    """점수화 함수 테스트"""
    scorer = AnalysisScorer()
    
    # RSI 테스트
    test_rsi_values = [25, 50, 75, 67.48]
    print("=== RSI 점수화 테스트 ===")
    for rsi in test_rsi_values:
        score = scorer.score_rsi(rsi)
        interpretation = scorer.get_interpretation(score)
        print(f"RSI {rsi:5.2f} → 점수 {score:5.2f} ({interpretation})")
    
    print("\n=== PER 점수화 테스트 ===")
    test_per_values = [8, 15, 25, 30]
    for per in test_per_values:
        score = scorer.score_per(per)
        interpretation = scorer.get_interpretation(score)
        print(f"PER {per:5.2f} → 점수 {score:5.2f} ({interpretation})")
    
    print("\n=== 기술 영역 종합 점수 테스트 ===")
    rsi_score = scorer.score_rsi(67.48)
    tech_result = scorer.calculate_technical_score(rsi_score)
    print(f"RSI만으로 기술 점수: {tech_result['total_score']:.2f}/4.0 ({tech_result['percentage']:.1f}%)")
    print(f"해석: {tech_result['interpretation']}")


if __name__ == "__main__":
    test_scoring()