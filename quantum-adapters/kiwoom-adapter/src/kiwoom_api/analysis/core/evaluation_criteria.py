"""
구글 시트 평가기준표 ('디노테스트_평가기준') 구현

Google Sheets의 VLOOKUP 평가기준표를 Python으로 완전 구현합니다.
각 코드(A001~D009, Z999)별로 부여기준과 점수를 정의합니다.
"""

from typing import Dict, Any
from enum import Enum


class EvaluationCode(Enum):
    """평가 코드 열거형"""
    # 재무 영역 (Financial)
    A001 = "A001"  # 매출증가 10%이상
    A002 = "A002"  # 영업이익률 10%이상
    A003 = "A003"  # 전년 대비 영업이익 흑자 전환
    A004 = "A004"  # 유보율 1,000% 이상
    A005 = "A005"  # 부채비율 50% 이하
    A006 = "A006"  # 전년 대비 매출 감소
    A007 = "A007"  # 영업이익 적자 전환
    A008 = "A008"  # 영업이익 적자 지속
    A009 = "A009"  # 유보율 300% 이하
    A010 = "A010"  # 부채비율 200% 이상
    
    # 기술 영역 (Technical)
    B001 = "B001"  # OBV만족
    B002 = "B002"  # 투자심리도침체 (25%이하)
    B003 = "B003"  # RSI침체 (30%이하)
    B004 = "B004"  # OBV불만족
    B005 = "B005"  # 투자심리도과열 (75%이상)
    B006 = "B006"  # RSI과열 (70%이상)
    
    # 가격 영역 (Price)
    C001 = "C001"  # -40% 이상
    C002 = "C002"  # -30% 이상
    C003 = "C003"  # -20% 이상
    C004 = "C004"  # +300% 이상
    C005 = "C005"  # +200% 이상
    C006 = "C006"  # +100% 이상
    
    # 재료 영역 (Material)
    D001 = "D001"  # 구체화된 이벤트/호재 임박
    D002 = "D002"  # 확실한 주도 테마
    D003 = "D003"  # 기관/외국인 수급
    D004 = "D004"  # 고배당
    D005 = "D005"  # 어닝서프라이즈
    D006 = "D006"  # 불성실 공시
    D007 = "D007"  # 악재뉴스
    D008 = "D008"  # 호재뉴스 도배
    D009 = "D009"  # 이자보상배율
    
    # 기타
    Z999 = "Z999"  # 해당없음


class EvaluationCriteria:
    """평가기준표 클래스"""
    
    # 평가기준표 데이터 (구글 시트와 동일)
    CRITERIA_TABLE: Dict[str, Dict[str, Any]] = {
        # 재무 영역 코드표
        "A001": {
            "category": "재무",
            "item": "매출증가 10%이상",
            "condition": "매출증가율 ≥ 10%",
            "score": 1
        },
        "A002": {
            "category": "재무",
            "item": "영업이익률 10%이상",
            "condition": "영업이익률 ≥ 10%",
            "score": 1
        },
        "A003": {
            "category": "재무",
            "item": "전년 대비 영업이익 흑자 전환",
            "condition": "적자→흑자",
            "score": 1
        },
        "A004": {
            "category": "재무",
            "item": "유보율 1,000% 이상",
            "condition": "유보율 ≥ 1,000%",
            "score": 1
        },
        "A005": {
            "category": "재무",
            "item": "부채비율 50% 이하",
            "condition": "부채비율 ≤ 50%",
            "score": 1
        },
        "A006": {
            "category": "재무",
            "item": "전년 대비 매출 감소",
            "condition": "매출 감소",
            "score": -1
        },
        "A007": {
            "category": "재무",
            "item": "영업이익 적자 전환",
            "condition": "흑자→적자",
            "score": -1
        },
        "A008": {
            "category": "재무",
            "item": "영업이익 적자 지속",
            "condition": "적자→적자",
            "score": -2
        },
        "A009": {
            "category": "재무",
            "item": "유보율 300% 이하",
            "condition": "유보율 ≤ 300%",
            "score": -1
        },
        "A010": {
            "category": "재무",
            "item": "부채비율 200% 이상",
            "condition": "부채비율 ≥ 200%",
            "score": -1
        },
        
        # 기술 영역 코드표
        "B001": {
            "category": "기술",
            "item": "OBV만족",
            "condition": "OBV 조건 만족",
            "score": 1
        },
        "B002": {
            "category": "기술",
            "item": "투자심리도침체 (25%이하)",
            "condition": "투자심리도 ≤ 25%",
            "score": 1
        },
        "B003": {
            "category": "기술",
            "item": "RSI침체 (30%이하)",
            "condition": "RSI ≤ 30%",
            "score": 1
        },
        "B004": {
            "category": "기술",
            "item": "OBV불만족",
            "condition": "OBV 조건 불만족",
            "score": -1
        },
        "B005": {
            "category": "기술",
            "item": "투자심리도과열 (75%이상)",
            "condition": "투자심리도 ≥ 75%",
            "score": -1
        },
        "B006": {
            "category": "기술",
            "item": "RSI과열 (70%이상)",
            "condition": "RSI ≥ 70%",
            "score": -1
        },
        
        # 가격 영역 코드표
        "C001": {
            "category": "가격",
            "item": "-40% 이상",
            "condition": "52주 대비 위치 ≤ -40%",
            "score": 3
        },
        "C002": {
            "category": "가격",
            "item": "-30% 이상",
            "condition": "52주 대비 위치 ≤ -30%",
            "score": 2
        },
        "C003": {
            "category": "가격",
            "item": "-20% 이상",
            "condition": "52주 대비 위치 ≤ -20%",
            "score": 1
        },
        "C004": {
            "category": "가격",
            "item": "+300% 이상",
            "condition": "52주 대비 위치 ≥ +300%",
            "score": -3
        },
        "C005": {
            "category": "가격",
            "item": "+200% 이상",
            "condition": "52주 대비 위치 ≥ +200%",
            "score": -2
        },
        "C006": {
            "category": "가격",
            "item": "+100% 이상",
            "condition": "52주 대비 위치 ≥ +100%",
            "score": -1
        },
        
        # 재료 영역 코드표
        "D001": {
            "category": "재료",
            "item": "구체화된 이벤트/호재 임박",
            "condition": "호재 임박",
            "score": 1
        },
        "D002": {
            "category": "재료",
            "item": "확실한 주도 테마",
            "condition": "주도 테마",
            "score": 1
        },
        "D003": {
            "category": "재료",
            "item": "기관/외국인 수급",
            "condition": "최근 1~3개월, 상장주식수 1% 이상",
            "score": 1
        },
        "D004": {
            "category": "재료",
            "item": "고배당",
            "condition": "배당수익률 ≥ 2%",
            "score": 1
        },
        "D005": {
            "category": "재료",
            "item": "어닝서프라이즈",
            "condition": "실적 서프라이즈",
            "score": 1
        },
        "D006": {
            "category": "재료",
            "item": "불성실 공시",
            "condition": "불성실 공시",
            "score": -1
        },
        "D007": {
            "category": "재료",
            "item": "악재뉴스",
            "condition": "대형 클레임, 계약취소 등",
            "score": -1
        },
        "D008": {
            "category": "재료",
            "item": "호재뉴스 도배",
            "condition": "호재뉴스 도배",
            "score": 1
        },
        "D009": {
            "category": "재료",
            "item": "이자보상배율",
            "condition": "이자보상배율 < 1",
            "score": -1
        },
        
        # 기타
        "Z999": {
            "category": "기타",
            "item": "해당없음",
            "condition": "기타 모든 경우",
            "score": 0
        }
    }
    
    @classmethod
    def get_score(cls, code: str) -> int:
        """
        평가 코드에 해당하는 점수 반환
        
        Args:
            code: 평가 코드 (A001~D009, Z999)
            
        Returns:
            점수 (int)
            
        Example:
            >>> EvaluationCriteria.get_score("A001")
            1
            >>> EvaluationCriteria.get_score("A008")
            -2
            >>> EvaluationCriteria.get_score("Z999")
            0
        """
        return cls.CRITERIA_TABLE.get(code, cls.CRITERIA_TABLE["Z999"])["score"]
    
    @classmethod
    def get_criteria(cls, code: str) -> Dict[str, Any]:
        """
        평가 코드에 해당하는 전체 평가기준 반환
        
        Args:
            code: 평가 코드
            
        Returns:
            평가기준 딕셔너리
        """
        return cls.CRITERIA_TABLE.get(code, cls.CRITERIA_TABLE["Z999"])
    
    @classmethod
    def get_category_codes(cls, category: str) -> list[str]:
        """
        특정 카테고리의 모든 코드 반환
        
        Args:
            category: 카테고리명 ("재무", "기술", "가격", "재료")
            
        Returns:
            해당 카테고리의 코드 리스트
        """
        return [
            code for code, criteria in cls.CRITERIA_TABLE.items()
            if criteria["category"] == category
        ]
    
    @classmethod
    def vlookup(cls, code: str) -> int:
        """
        Google Sheets VLOOKUP 함수와 동일한 동작
        
        Args:
            code: 평가 코드
            
        Returns:
            점수 (구글 시트의 3번째 열 값)
        """
        return cls.get_score(code)


# 테스트 함수
def test_evaluation_criteria():
    """평가기준표 테스트"""
    print("=== 평가기준표 테스트 ===")
    
    # 각 영역별 코드 테스트
    test_codes = [
        ("A001", "매출증가 10%이상"),
        ("A008", "영업이익 적자 지속"),
        ("B003", "RSI침체 (30%이하)"),
        ("B006", "RSI과열 (70%이상)"),
        ("C001", "-40% 이상"),
        ("C004", "+300% 이상"),
        ("D004", "고배당"),
        ("D009", "이자보상배율"),
        ("Z999", "해당없음")
    ]
    
    for code, expected_item in test_codes:
        criteria = EvaluationCriteria.get_criteria(code)
        score = EvaluationCriteria.get_score(code)
        vlookup_score = EvaluationCriteria.vlookup(code)
        
        print(f"코드 {code}: {criteria['item']} → 점수 {score} (VLOOKUP: {vlookup_score})")
        assert criteria["item"] == expected_item, f"항목명 불일치: {code}"
        assert score == vlookup_score, f"VLOOKUP 점수 불일치: {code}"
    
    # 카테고리별 코드 수 테스트
    financial_codes = EvaluationCriteria.get_category_codes("재무")
    technical_codes = EvaluationCriteria.get_category_codes("기술")
    price_codes = EvaluationCriteria.get_category_codes("가격")
    material_codes = EvaluationCriteria.get_category_codes("재료")
    
    print(f"\n카테고리별 코드 개수:")
    print(f"재무: {len(financial_codes)}개 - {financial_codes}")
    print(f"기술: {len(technical_codes)}개 - {technical_codes}")
    print(f"가격: {len(price_codes)}개 - {price_codes}")
    print(f"재료: {len(material_codes)}개 - {material_codes}")
    
    print("\n✅ 모든 테스트 통과!")


if __name__ == "__main__":
    test_evaluation_criteria()