#!/usr/bin/env python3
"""
불성실 공시 판단기

DART API를 통해 기업의 공시 이력을 분석하여 불성실 공시 여부를 판단합니다.
"""

import logging
import requests
import pandas as pd
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DisclosureAnalysis:
    """공시 분석 결과"""
    company_name: str
    stock_code: str
    total_disclosures: int
    recent_disclosures_30d: int
    correction_rate: float  # 정정공시 비율
    periodic_report_delays: int  # 정기보고서 지연 건수
    disclosure_quality_score: float  # 공시 품질 점수 (0-1)
    is_poor_disclosure: bool  # 불성실 공시 판정
    risk_factors: List[str]  # 위험 요소 목록

class DisclosureAnalyzer:
    """공시 분석기"""
    
    def __init__(self, external_api_base_url: str = "http://external-api.quantum-trading.com:8001"):
        self.base_url = external_api_base_url
        self.logger = logging.getLogger(__name__)
        
        # 정기공시 보고서 유형
        self.periodic_reports = [
            "사업보고서",
            "반기보고서", 
            "분기보고서"
        ]
        
        # 중요공시 키워드
        self.important_keywords = [
            "감사보고서",
            "연결재무제표",
            "투자위험",
            "중요한계약",
            "경영진변경",
            "자금조달"
        ]
    
    def get_company_code_by_stock_code(self, stock_code: str) -> Optional[str]:
        """종목코드로 기업코드 찾기"""
        try:
            # DART API에서 삼성전자(005930) -> 00126380 같은 매핑이 필요
            # 임시로 주요 기업 매핑 테이블 사용
            stock_to_corp_mapping = {
                "005930": "00126380",  # 삼성전자
                "000660": "00164779",  # SK하이닉스
                "035720": "00401731",  # 카카오
                "051910": "00126380",  # LG화학
                "003550": "00164742"   # LG
            }
            
            return stock_to_corp_mapping.get(stock_code)
            
        except Exception as e:
            self.logger.error(f"기업코드 조회 실패 - {stock_code}: {e}")
            return None
    
    def fetch_disclosure_data(self, corp_code: str, days: int = 90) -> Optional[List[Dict]]:
        """DART API로 공시 데이터 조회"""
        try:
            url = f"{self.base_url}/disclosure/company/{corp_code}"
            params = {"days": days, "count": 100}  # 최대 100건 조회
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") == "000":
                return data.get("list", [])
            else:
                self.logger.warning(f"DART API 오류: {data.get('message', 'Unknown error')}")
                return None
                
        except Exception as e:
            self.logger.error(f"공시 데이터 조회 실패 - {corp_code}: {e}")
            return None
    
    def analyze_correction_rate(self, disclosures: List[Dict]) -> float:
        """정정공시 비율 분석"""
        if not disclosures:
            return 0.0
        
        total_count = len(disclosures)
        correction_count = 0
        
        for disclosure in disclosures:
            report_name = disclosure.get("report_nm", "")
            # 정정, 취소, 변경 키워드로 정정공시 판단
            if any(keyword in report_name for keyword in ["정정", "취소", "변경", "정정보고서"]):
                correction_count += 1
        
        correction_rate = correction_count / total_count if total_count > 0 else 0.0
        
        self.logger.info(f"정정공시 분석: 전체 {total_count}건 중 {correction_count}건 정정 (비율: {correction_rate:.2%})")
        
        return correction_rate
    
    def analyze_periodic_report_delays(self, disclosures: List[Dict]) -> int:
        """정기보고서 지연 분석"""
        delay_count = 0
        current_year = datetime.now().year
        
        # 정기보고서 법정 기한 (간략화)
        report_deadlines = {
            "사업보고서": f"{current_year}-03-31",     # 3월 31일
            "반기보고서": f"{current_year}-08-14",     # 8월 14일 (2개월 이내)
            "분기보고서": f"{current_year}-05-15"      # 5월 15일 (45일 이내)
        }
        
        try:
            for disclosure in disclosures:
                report_name = disclosure.get("report_nm", "")
                rcept_dt = disclosure.get("rcept_dt", "")
                
                if not rcept_dt or len(rcept_dt) != 8:
                    continue
                
                # 날짜 변환
                try:
                    submission_date = datetime.strptime(rcept_dt, "%Y%m%d")
                except:
                    continue
                
                # 정기보고서 여부 확인
                for report_type, deadline_str in report_deadlines.items():
                    if report_type in report_name:
                        deadline = datetime.strptime(deadline_str, "%Y-%m-%d")
                        
                        # 해당 연도 보고서인지 확인하고 지연 여부 판단
                        if submission_date.year == deadline.year and submission_date > deadline:
                            delay_count += 1
                            self.logger.info(f"지연 공시 발견: {report_name} - 제출일: {rcept_dt}, 기한: {deadline_str}")
                            break
        
        except Exception as e:
            self.logger.error(f"정기보고서 지연 분석 실패: {e}")
        
        return delay_count
    
    def calculate_disclosure_quality_score(self, disclosures: List[Dict]) -> float:
        """공시 품질 점수 계산 (0.0-1.0)"""
        if not disclosures:
            return 0.0
        
        quality_factors = {
            "regularity": 0.0,      # 규칙성 (0.3)
            "completeness": 0.0,    # 완전성 (0.3) 
            "timeliness": 0.0,      # 적시성 (0.2)
            "transparency": 0.0     # 투명성 (0.2)
        }
        
        # 1. 규칙성: 월별 공시 분포의 일관성
        monthly_counts = {}
        for disclosure in disclosures:
            rcept_dt = disclosure.get("rcept_dt", "")
            if len(rcept_dt) == 8:
                month_key = rcept_dt[:6]  # YYYYMM
                monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
        
        if monthly_counts:
            avg_monthly = sum(monthly_counts.values()) / len(monthly_counts)
            variance = sum((count - avg_monthly) ** 2 for count in monthly_counts.values()) / len(monthly_counts)
            regularity = max(0.0, 1.0 - (variance / (avg_monthly + 1)))
            quality_factors["regularity"] = regularity
        
        # 2. 완전성: 중요공시 포함 여부
        important_disclosure_count = 0
        for disclosure in disclosures:
            report_name = disclosure.get("report_nm", "")
            if any(keyword in report_name for keyword in self.important_keywords):
                important_disclosure_count += 1
        
        completeness = min(1.0, important_disclosure_count / 10)  # 10개 기준으로 정규화
        quality_factors["completeness"] = completeness
        
        # 3. 적시성: 최근 30일 내 공시 활동
        recent_count = 0
        cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        
        for disclosure in disclosures:
            rcept_dt = disclosure.get("rcept_dt", "")
            if rcept_dt >= cutoff_date:
                recent_count += 1
        
        timeliness = min(1.0, recent_count / 5)  # 5건 기준으로 정규화
        quality_factors["timeliness"] = timeliness
        
        # 4. 투명성: 공시 제목의 구체성 (간단한 휴리스틱)
        specific_count = 0
        for disclosure in disclosures:
            report_name = disclosure.get("report_nm", "")
            # 구체적인 금액, 날짜, 비율이 포함된 공시
            if any(char in report_name for char in ["억원", "조원", "%", "일자", "계약"]):
                specific_count += 1
        
        transparency = min(1.0, specific_count / len(disclosures))
        quality_factors["transparency"] = transparency
        
        # 가중 평균으로 최종 품질 점수 계산
        final_score = (
            quality_factors["regularity"] * 0.3 +
            quality_factors["completeness"] * 0.3 +
            quality_factors["timeliness"] * 0.2 +
            quality_factors["transparency"] * 0.2
        )
        
        self.logger.info(f"공시 품질 점수: {final_score:.3f} (규칙성:{quality_factors['regularity']:.2f}, "
                        f"완전성:{quality_factors['completeness']:.2f}, 적시성:{quality_factors['timeliness']:.2f}, "
                        f"투명성:{quality_factors['transparency']:.2f})")
        
        return final_score
    
    def determine_poor_disclosure(self, analysis: DisclosureAnalysis) -> Tuple[bool, List[str]]:
        """불성실 공시 여부 최종 판정"""
        risk_factors = []
        
        # 위험 요소 체크
        if analysis.correction_rate > 0.15:  # 정정공시 비율 15% 초과
            risk_factors.append(f"정정공시 비율 높음 ({analysis.correction_rate:.1%})")
        
        if analysis.periodic_report_delays > 0:
            risk_factors.append(f"정기보고서 지연 제출 ({analysis.periodic_report_delays}건)")
        
        if analysis.disclosure_quality_score < 0.4:  # 품질 점수 40% 미만
            risk_factors.append(f"공시 품질 낮음 ({analysis.disclosure_quality_score:.1%})")
        
        if analysis.recent_disclosures_30d == 0:  # 최근 30일 공시 없음
            risk_factors.append("최근 공시 활동 부족")
        
        if analysis.total_disclosures < 5:  # 전체 공시 건수 부족
            risk_factors.append("전체 공시 건수 부족")
        
        # 불성실 공시 판정: 위험 요소 2개 이상이면 불성실
        is_poor = len(risk_factors) >= 2
        
        return is_poor, risk_factors
    
    def analyze_disclosure_compliance(self, stock_code: str) -> Optional[DisclosureAnalysis]:
        """공시 성실성 종합 분석"""
        self.logger.info(f"=== {stock_code} 공시 성실성 분석 시작 ===")
        
        try:
            # 1. 기업코드 조회
            corp_code = self.get_company_code_by_stock_code(stock_code)
            if not corp_code:
                self.logger.warning(f"기업코드를 찾을 수 없음: {stock_code}")
                return None
            
            # 2. 공시 데이터 수집 (최근 90일)
            disclosures = self.fetch_disclosure_data(corp_code, days=90)
            if not disclosures:
                self.logger.warning(f"공시 데이터가 없음: {stock_code}")
                return None
            
            company_name = disclosures[0].get("corp_name", stock_code)
            
            # 3. 각종 분석 수행
            correction_rate = self.analyze_correction_rate(disclosures)
            delay_count = self.analyze_periodic_report_delays(disclosures)
            quality_score = self.calculate_disclosure_quality_score(disclosures)
            
            # 최근 30일 공시 건수
            cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
            recent_count = sum(1 for d in disclosures if d.get("rcept_dt", "") >= cutoff_date)
            
            # 4. 분석 결과 생성
            analysis = DisclosureAnalysis(
                company_name=company_name,
                stock_code=stock_code,
                total_disclosures=len(disclosures),
                recent_disclosures_30d=recent_count,
                correction_rate=correction_rate,
                periodic_report_delays=delay_count,
                disclosure_quality_score=quality_score,
                is_poor_disclosure=False,  # 임시값, 아래에서 계산
                risk_factors=[]
            )
            
            # 5. 최종 판정
            is_poor, risk_factors = self.determine_poor_disclosure(analysis)
            analysis.is_poor_disclosure = is_poor
            analysis.risk_factors = risk_factors
            
            self.logger.info(f"공시 분석 완료 - {company_name}: {'불성실' if is_poor else '성실'} "
                            f"(위험요소: {len(risk_factors)}개)")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"공시 성실성 분석 실패 - {stock_code}: {e}")
            return None

if __name__ == "__main__":
    # 테스트 코드
    logging.basicConfig(level=logging.INFO)
    
    analyzer = DisclosureAnalyzer()
    result = analyzer.analyze_disclosure_compliance("005930")  # 삼성전자
    
    if result:
        print(f"\n📊 {result.company_name} ({result.stock_code}) 공시 분석 결과")
        print(f"전체 공시: {result.total_disclosures}건")
        print(f"최근 30일: {result.recent_disclosures_30d}건")
        print(f"정정 비율: {result.correction_rate:.2%}")
        print(f"지연 건수: {result.periodic_report_delays}건")
        print(f"품질 점수: {result.disclosure_quality_score:.2%}")
        print(f"판정: {'🔴 불성실' if result.is_poor_disclosure else '🟢 성실'}")
        
        if result.risk_factors:
            print("위험 요소:")
            for factor in result.risk_factors:
                print(f"  - {factor}")