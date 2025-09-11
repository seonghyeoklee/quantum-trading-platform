#!/usr/bin/env python3
"""
KIS 재무 API 응답 구조 디버깅 스크립트
실제 API 응답을 확인하여 데이터 파싱 로직을 수정하기 위함
"""

import sys
import logging
import pandas as pd

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 경로 설정
sys.path.extend(['.', 'examples_llm'])
import kis_auth as ka

def debug_income_statement(stock_code="005930"):
    """손익계산서 API 응답 구조 확인"""
    logger.info("=== 손익계산서 API 응답 구조 디버깅 ===")
    
    try:
        from examples_llm.domestic_stock.finance_income_statement.finance_income_statement import finance_income_statement
        
        result = finance_income_statement(
            fid_div_cls_code="0",  # 연간
            fid_cond_mrkt_div_code="J",
            fid_input_iscd=stock_code
        )
        
        if result is not None and not result.empty:
            logger.info(f"데이터 건수: {len(result)}")
            logger.info(f"컬럼들: {list(result.columns)}")
            
            # 첫 번째 행 데이터 출력
            if len(result) > 0:
                first_row = result.iloc[0]
                logger.info("=== 첫 번째 행 데이터 ===")
                for col, value in first_row.items():
                    if pd.notna(value) and str(value).strip():
                        logger.info(f"{col}: {value}")
                
                # 두 번째 행 데이터 출력 (전년 비교용)
                if len(result) > 1:
                    logger.info("\n=== 두 번째 행 데이터 (전년) ===")
                    second_row = result.iloc[1]
                    for col, value in second_row.items():
                        if pd.notna(value) and str(value).strip():
                            logger.info(f"{col}: {value}")
        else:
            logger.warning("데이터 없음")
            
    except Exception as e:
        logger.error(f"손익계산서 디버깅 실패: {e}")

def debug_balance_sheet(stock_code="005930"):
    """대차대조표 API 응답 구조 확인"""
    logger.info("\n=== 대차대조표 API 응답 구조 디버깅 ===")
    
    try:
        from examples_llm.domestic_stock.finance_balance_sheet.finance_balance_sheet import finance_balance_sheet
        
        result = finance_balance_sheet(
            fid_div_cls_code="0",  # 연간
            fid_cond_mrkt_div_code="J",
            fid_input_iscd=stock_code
        )
        
        if result is not None and not result.empty:
            logger.info(f"데이터 건수: {len(result)}")
            logger.info(f"컬럼들: {list(result.columns)}")
            
            # 첫 번째 행 데이터 출력
            if len(result) > 0:
                first_row = result.iloc[0]
                logger.info("=== 첫 번째 행 데이터 ===")
                for col, value in first_row.items():
                    if pd.notna(value) and str(value).strip():
                        logger.info(f"{col}: {value}")
        else:
            logger.warning("데이터 없음")
            
    except Exception as e:
        logger.error(f"대차대조표 디버깅 실패: {e}")

def debug_financial_ratio(stock_code="005930"):
    """재무비율 API 응답 구조 확인"""
    logger.info("\n=== 재무비율 API 응답 구조 디버깅 ===")
    
    try:
        from examples_llm.domestic_stock.finance_financial_ratio.finance_financial_ratio import finance_financial_ratio
        
        result = finance_financial_ratio(
            fid_div_cls_code="0",  # 연간
            fid_cond_mrkt_div_code="J",
            fid_input_iscd=stock_code
        )
        
        if result is not None and not result.empty:
            logger.info(f"데이터 건수: {len(result)}")
            logger.info(f"컬럼들: {list(result.columns)}")
            
            # 첫 번째 행 데이터 출력
            if len(result) > 0:
                first_row = result.iloc[0]
                logger.info("=== 첫 번째 행 데이터 ===")
                for col, value in first_row.items():
                    if pd.notna(value) and str(value).strip():
                        logger.info(f"{col}: {value}")
        else:
            logger.warning("데이터 없음")
            
    except Exception as e:
        logger.error(f"재무비율 디버깅 실패: {e}")

def main():
    try:
        # KIS API 인증
        ka.auth(svr="prod", product="01")
        logger.info("✅ KIS API 인증 성공")
        
        # 실제 API 응답 구조 확인
        debug_income_statement("005930")  # 삼성전자
        debug_balance_sheet("005930")
        debug_financial_ratio("005930")
        
    except Exception as e:
        logger.error(f"디버깅 실패: {e}")

if __name__ == "__main__":
    main()