"""
Pydantic models for DART (전자공시시스템) API responses and requests.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from datetime import datetime, date
import re


class DartListParams(BaseModel):
    """Parameters for DART disclosure list request."""
    
    crtfc_key: str = Field(..., description="API 인증키")
    corp_code: Optional[str] = Field(None, min_length=8, max_length=8, description="고유번호 (8자리)")
    bgn_de: Optional[str] = Field(None, description="시작일 (YYYYMMDD)")
    end_de: Optional[str] = Field(None, description="종료일 (YYYYMMDD)")
    last_reprt_at: Optional[Literal["Y", "N"]] = Field("N", description="최종보고서 검색여부")
    pblntf_ty: Optional[Literal["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]] = Field(None, description="공시유형")
    pblntf_detail_ty: Optional[str] = Field(None, max_length=4, description="공시상세유형")
    corp_cls: Optional[Literal["Y", "K", "N", "E"]] = Field(None, description="법인구분")
    sort: Optional[Literal["date", "crp", "rpt"]] = Field("date", description="정렬")
    sort_mth: Optional[Literal["asc", "desc"]] = Field("desc", description="정렬방법")
    page_no: Optional[int] = Field(1, ge=1, description="페이지 번호")
    page_count: Optional[int] = Field(10, ge=1, le=100, description="페이지 별 건수")
    
    @validator('bgn_de', 'end_de')
    def validate_date_format(cls, v):
        """Validate date format YYYYMMDD."""
        if v is not None:
            if not re.match(r'^\d{8}$', v):
                raise ValueError("날짜는 YYYYMMDD 형식이어야 합니다")
        return v
    
    @validator('corp_code')
    def validate_corp_code(cls, v):
        """Validate corp_code format."""
        if v is not None:
            if not re.match(r'^\d{8}$', v):
                raise ValueError("고유번호는 8자리 숫자여야 합니다")
        return v


class DartDisclosureItem(BaseModel):
    """Individual disclosure item from DART API."""
    
    corp_cls: str = Field(..., description="법인구분")
    corp_name: str = Field(..., description="종목명(법인명)")
    corp_code: str = Field(..., description="고유번호")
    stock_code: Optional[str] = Field(None, description="종목코드")
    report_nm: str = Field(..., description="보고서명")
    rcept_no: str = Field(..., description="접수번호")
    flr_nm: str = Field(..., description="공시 제출인명")
    rcept_dt: str = Field(..., description="접수일자")
    rm: Optional[str] = Field(None, description="비고")
    
    @property
    def corp_cls_name(self) -> str:
        """Get readable corp_cls name."""
        corp_cls_map = {
            "Y": "유가증권시장",
            "K": "코스닥",
            "N": "코넥스",
            "E": "기타"
        }
        return corp_cls_map.get(self.corp_cls, self.corp_cls)
    
    @property
    def dart_viewer_url(self) -> str:
        """Get DART viewer URL for this disclosure."""
        return f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={self.rcept_no}"
    
    @property
    def formatted_rcept_dt(self) -> str:
        """Get formatted reception date."""
        if len(self.rcept_dt) == 8:
            return f"{self.rcept_dt[:4]}-{self.rcept_dt[4:6]}-{self.rcept_dt[6:8]}"
        return self.rcept_dt


class DartListResponse(BaseModel):
    """Response from DART disclosure list API."""
    
    status: str = Field(..., description="에러 및 정보 코드")
    message: str = Field(..., description="에러 및 정보 메시지")
    page_no: int = Field(..., description="페이지 번호")
    page_count: int = Field(..., description="페이지 별 건수")
    total_count: int = Field(..., description="총 건수")
    total_page: int = Field(..., description="총 페이지 수")
    list: List[DartDisclosureItem] = Field(default=[], description="공시 목록")
    
    @property
    def is_success(self) -> bool:
        """Check if the response is successful."""
        return self.status == "000"
    
    @property
    def has_more(self) -> bool:
        """Check if there are more results available."""
        return self.page_no < self.total_page
    
    @property
    def next_page(self) -> Optional[int]:
        """Get the next page number."""
        if self.has_more:
            return self.page_no + 1
        return None


class DartListRequest(BaseModel):
    """Request wrapper for DART disclosure list search."""
    
    params: DartListParams
    
    def to_api_params(self) -> dict:
        """Convert to API parameter dictionary."""
        # Convert model to dict and remove None values
        params_dict = self.params.dict(exclude_none=True)
        
        # Ensure crtfc_key is included (required parameter)
        if 'crtfc_key' not in params_dict:
            raise ValueError("crtfc_key is required")
        
        return params_dict


# DART 공시유형 상수
DART_DISCLOSURE_TYPES = {
    "A": "정기공시",
    "B": "주요사항보고",
    "C": "발행공시",
    "D": "지분공시",
    "E": "기타공시",
    "F": "외부감사관련",
    "G": "펀드공시",
    "H": "자산유동화",
    "I": "거래소공시",
    "J": "공정위공시"
}

# DART 법인구분 상수
DART_CORP_TYPES = {
    "Y": "유가증권시장",
    "K": "코스닥",
    "N": "코넥스",
    "E": "기타"
}

# DART 정렬 타입 상수
DART_SORT_TYPES = {
    "date": "접수일자",
    "crp": "회사명",
    "rpt": "보고서명"
}


# === DART 기업개황 API 모델들 ===

class DartCompanyParams(BaseModel):
    """Parameters for DART company info request."""
    
    crtfc_key: str = Field(..., description="API 인증키")
    corp_code: str = Field(..., min_length=8, max_length=8, description="고유번호 (8자리)")
    
    @validator('corp_code')
    def validate_corp_code(cls, v):
        """Validate corp_code format."""
        if not re.match(r'^\d{8}$', v):
            raise ValueError("고유번호는 8자리 숫자여야 합니다")
        return v


class DartCompanyInfo(BaseModel):
    """Company information from DART API."""
    
    status: str = Field(..., description="에러 및 정보 코드")
    message: str = Field(..., description="에러 및 정보 메시지")
    corp_name: Optional[str] = Field(None, description="정식명칭")
    corp_name_eng: Optional[str] = Field(None, description="영문명칭")
    stock_name: Optional[str] = Field(None, description="종목명 또는 약식명칭")
    stock_code: Optional[str] = Field(None, description="종목코드")
    ceo_nm: Optional[str] = Field(None, description="대표자명")
    corp_cls: Optional[str] = Field(None, description="법인구분")
    jurir_no: Optional[str] = Field(None, description="법인등록번호")
    bizr_no: Optional[str] = Field(None, description="사업자등록번호")
    adres: Optional[str] = Field(None, description="주소")
    hm_url: Optional[str] = Field(None, description="홈페이지")
    ir_url: Optional[str] = Field(None, description="IR홈페이지")
    phn_no: Optional[str] = Field(None, description="전화번호")
    fax_no: Optional[str] = Field(None, description="팩스번호")
    induty_code: Optional[str] = Field(None, description="업종코드")
    est_dt: Optional[str] = Field(None, description="설립일 (YYYYMMDD)")
    acc_mt: Optional[str] = Field(None, description="결산월 (MM)")
    
    @property
    def is_success(self) -> bool:
        """Check if the response is successful."""
        return self.status == "000"
    
    @property
    def corp_cls_name(self) -> str:
        """Get readable corp_cls name."""
        corp_cls_map = {
            "Y": "유가증권시장",
            "K": "코스닥",
            "N": "코넥스",
            "E": "기타"
        }
        return corp_cls_map.get(self.corp_cls, self.corp_cls)
    
    @property
    def formatted_est_dt(self) -> Optional[str]:
        """Get formatted establishment date."""
        if self.est_dt and len(self.est_dt) == 8:
            return f"{self.est_dt[:4]}-{self.est_dt[4:6]}-{self.est_dt[6:8]}"
        return self.est_dt
    
    @property
    def is_listed(self) -> bool:
        """Check if the company is listed (has stock code)."""
        return bool(self.stock_code)
    
    @property
    def company_summary(self) -> dict:
        """Get company summary information."""
        return {
            "name": self.corp_name,
            "english_name": self.corp_name_eng,
            "stock_name": self.stock_name,
            "stock_code": self.stock_code,
            "ceo": self.ceo_nm,
            "market": self.corp_cls_name,
            "establishment_date": self.formatted_est_dt,
            "website": self.hm_url,
            "ir_website": self.ir_url,
            "is_listed": self.is_listed
        }


class DartCompanyRequest(BaseModel):
    """Request wrapper for DART company info."""
    
    params: DartCompanyParams
    
    def to_api_params(self) -> dict:
        """Convert to API parameter dictionary."""
        return self.params.dict()