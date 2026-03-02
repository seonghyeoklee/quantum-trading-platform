"""KIS 거래량 순위 클라이언트 테스트"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.kis.volume_rank import KISVolumeRankClient
from app.models import VolumeRankItem


def _make_client() -> tuple[KISVolumeRankClient, AsyncMock]:
    """테스트용 클라이언트 + mock HTTP client 생성"""
    auth = MagicMock()
    auth.config.base_url = "https://openapivts.koreainvestment.com:29443"
    auth.get_token = AsyncMock()
    auth.get_base_headers.return_value = {
        "Content-Type": "application/json",
        "authorization": "Bearer test",
        "appkey": "test",
        "appsecret": "test",
    }
    mock_http = AsyncMock()
    auth._client = mock_http
    client = KISVolumeRankClient(auth)
    return client, mock_http


@pytest.mark.asyncio
async def test_get_volume_ranking_success():
    """정상 응답 파싱"""
    client, mock_http = _make_client()
    mock_http.get.return_value = {
        "rt_cd": "0",
        "output": [
            {
                "mksc_shrn_iscd": "005930",
                "hts_kor_isnm": "삼성전자",
                "stck_prpr": "72000",
                "prdy_ctrt": "2.50",
                "acml_vol": "15000000",
                "vol_inrt": "120.5",
                "acml_tr_pbmn": "1080000000000",
            },
            {
                "mksc_shrn_iscd": "000660",
                "hts_kor_isnm": "SK하이닉스",
                "stck_prpr": "180000",
                "prdy_ctrt": "3.10",
                "acml_vol": "5000000",
                "vol_inrt": "85.3",
                "acml_tr_pbmn": "900000000000",
            },
        ],
    }

    items = await client.get_volume_ranking(top_n=30)
    assert len(items) == 2
    assert items[0].symbol == "005930"
    assert items[0].name == "삼성전자"
    assert items[0].current_price == 72000.0
    assert items[0].change_rate == 2.5
    assert items[0].volume == 15_000_000
    assert items[0].volume_increase_rate == 120.5


@pytest.mark.asyncio
async def test_get_volume_ranking_empty():
    """빈 응답"""
    client, mock_http = _make_client()
    mock_http.get.return_value = {"rt_cd": "0", "output": []}

    items = await client.get_volume_ranking()
    assert items == []


@pytest.mark.asyncio
async def test_get_volume_ranking_api_error():
    """API 에러 시 RuntimeError"""
    client, mock_http = _make_client()
    mock_http.get.return_value = {
        "rt_cd": "1",
        "msg_cd": "ERR001",
        "msg1": "서비스 오류",
    }

    with pytest.raises(RuntimeError, match="KIS API 오류"):
        await client.get_volume_ranking()


@pytest.mark.asyncio
async def test_get_volume_ranking_skip_invalid_symbol():
    """유효하지 않은 종목코드(빈 문자열, 길이 다름) 스킵"""
    client, mock_http = _make_client()
    mock_http.get.return_value = {
        "rt_cd": "0",
        "output": [
            {"mksc_shrn_iscd": "", "stck_prpr": "100"},  # 빈 코드
            {"mksc_shrn_iscd": "12345", "stck_prpr": "100"},  # 5자리
            {
                "mksc_shrn_iscd": "005930",
                "hts_kor_isnm": "삼성전자",
                "stck_prpr": "72000",
                "prdy_ctrt": "2.5",
                "acml_vol": "15000000",
                "vol_inrt": "120.5",
                "acml_tr_pbmn": "1080000000000",
            },
        ],
    }

    items = await client.get_volume_ranking()
    assert len(items) == 1
    assert items[0].symbol == "005930"


@pytest.mark.asyncio
async def test_get_volume_ranking_top_n():
    """top_n 파라미터로 결과 제한"""
    client, mock_http = _make_client()
    mock_http.get.return_value = {
        "rt_cd": "0",
        "output": [
            {
                "mksc_shrn_iscd": f"00{i:04d}",
                "hts_kor_isnm": f"종목{i}",
                "stck_prpr": "10000",
                "prdy_ctrt": "1.0",
                "acml_vol": "100000",
                "vol_inrt": "10.0",
                "acml_tr_pbmn": "100000000",
            }
            for i in range(10)
        ],
    }

    items = await client.get_volume_ranking(top_n=3)
    assert len(items) == 3
