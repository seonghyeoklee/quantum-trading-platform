"""API 입력 검증 테스트"""

from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.models import BacktestRequest, validate_symbol


# --- validate_symbol ---


class TestValidateSymbol:
    """심볼 포맷 검증"""

    def test_domestic_6digit(self):
        assert validate_symbol("005930") == "005930"

    def test_domestic_all_digits(self):
        assert validate_symbol("000660") == "000660"

    def test_us_upper(self):
        assert validate_symbol("AAPL") == "AAPL"

    def test_us_lower_normalized(self):
        assert validate_symbol("aapl") == "AAPL"

    def test_us_single_char(self):
        assert validate_symbol("F") == "F"

    def test_us_five_chars(self):
        assert validate_symbol("GOOGL") == "GOOGL"

    def test_invalid_5digit(self):
        with pytest.raises(ValueError, match="유효하지 않은 심볼"):
            validate_symbol("12345")

    def test_invalid_7digit(self):
        with pytest.raises(ValueError, match="유효하지 않은 심볼"):
            validate_symbol("1234567")

    def test_invalid_6char_alpha(self):
        with pytest.raises(ValueError, match="유효하지 않은 심볼"):
            validate_symbol("ABCDEF")

    def test_invalid_mixed(self):
        with pytest.raises(ValueError, match="유효하지 않은 심볼"):
            validate_symbol("ABC123")

    def test_invalid_empty(self):
        with pytest.raises(ValueError, match="유효하지 않은 심볼"):
            validate_symbol("")

    def test_invalid_special_chars(self):
        with pytest.raises(ValueError, match="유효하지 않은 심볼"):
            validate_symbol("AA-B")


# --- BacktestRequest validation ---


class TestBacktestRequestValidation:
    """백테스트 요청 검증"""

    def test_valid_defaults(self):
        req = BacktestRequest()
        assert req.symbol == "005930"
        assert req.start_date == "20240101"

    def test_valid_us_symbol(self):
        req = BacktestRequest(symbol="AAPL")
        assert req.symbol == "AAPL"

    def test_invalid_symbol(self):
        with pytest.raises(ValidationError, match="유효하지 않은 심볼"):
            BacktestRequest(symbol="INVALID!")

    def test_valid_dates(self):
        req = BacktestRequest(start_date="20230101", end_date="20231231")
        assert req.start_date == "20230101"
        assert req.end_date == "20231231"

    def test_empty_end_date_ok(self):
        req = BacktestRequest(end_date="")
        assert req.end_date == ""

    def test_invalid_date_format_alpha(self):
        with pytest.raises(ValidationError, match="YYYYMMDD"):
            BacktestRequest(start_date="2024-01-01")

    def test_invalid_date_format_short(self):
        with pytest.raises(ValidationError, match="YYYYMMDD"):
            BacktestRequest(start_date="240101")

    def test_invalid_date_nonexistent(self):
        with pytest.raises(ValidationError, match="유효하지 않은 날짜"):
            BacktestRequest(start_date="20241301")

    def test_future_date_rejected(self):
        future = (date.today() + timedelta(days=30)).strftime("%Y%m%d")
        with pytest.raises(ValidationError, match="미래 날짜"):
            BacktestRequest(start_date=future)

    def test_end_before_start(self):
        with pytest.raises(ValidationError, match="이전"):
            BacktestRequest(start_date="20240601", end_date="20240101")

    def test_same_start_end_ok(self):
        req = BacktestRequest(start_date="20240101", end_date="20240101")
        assert req.start_date == req.end_date


# --- StartRequest validation ---


from app.api.routes import StartRequest, _MAX_SYMBOLS


class TestStartRequestValidation:
    """StartRequest 검증"""

    def test_none_symbols(self):
        req = StartRequest()
        assert req.symbols is None

    def test_valid_domestic(self):
        req = StartRequest(symbols=["005930", "000660"])
        assert req.symbols == ["005930", "000660"]

    def test_valid_us(self):
        req = StartRequest(symbols=["AAPL", "TSLA"])
        assert req.symbols == ["AAPL", "TSLA"]

    def test_valid_mixed(self):
        req = StartRequest(symbols=["005930", "AAPL"])
        assert req.symbols == ["005930", "AAPL"]

    def test_empty_strings_removed(self):
        req = StartRequest(symbols=["005930", "", "  ", "AAPL"])
        assert req.symbols == ["005930", "AAPL"]

    def test_all_empty_becomes_none(self):
        req = StartRequest(symbols=["", "  "])
        assert req.symbols is None

    def test_duplicates_removed(self):
        req = StartRequest(symbols=["005930", "AAPL", "005930", "AAPL"])
        assert req.symbols == ["005930", "AAPL"]

    def test_us_symbol_uppercased(self):
        req = StartRequest(symbols=["aapl", "tsla"])
        assert req.symbols == ["AAPL", "TSLA"]

    def test_invalid_symbol_rejected(self):
        with pytest.raises(ValidationError, match="유효하지 않은 심볼"):
            StartRequest(symbols=["INVALID!"])

    def test_max_symbols_exceeded(self):
        symbols = [f"{i:06d}" for i in range(_MAX_SYMBOLS + 1)]
        with pytest.raises(ValidationError, match="최대"):
            StartRequest(symbols=symbols)

    def test_max_symbols_exact(self):
        symbols = [f"{i:06d}" for i in range(_MAX_SYMBOLS)]
        req = StartRequest(symbols=symbols)
        assert len(req.symbols) == _MAX_SYMBOLS

    def test_market_domestic(self):
        req = StartRequest(market="domestic")
        assert req.market == "domestic"

    def test_market_us(self):
        req = StartRequest(market="us")
        assert req.market == "us"

    def test_market_invalid(self):
        with pytest.raises(ValidationError):
            StartRequest(market="invalid")
