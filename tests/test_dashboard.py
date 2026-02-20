"""대시보드 HTML 구조 테스트"""

from app.dashboard import build_dashboard_html


def _html():
    return build_dashboard_html()


class TestDashboardHTML:
    def test_doctype(self):
        assert "<!DOCTYPE html>" in _html()

    def test_chartjs_cdn(self):
        assert "chart.js" in _html()

    def test_dark_theme(self):
        assert "#0f1117" in _html()

    def test_title(self):
        assert "<title>Trading Dashboard</title>" in _html()

    def test_status_badge_id(self):
        assert 'id="status-badge"' in _html()

    def test_positions_body_id(self):
        assert 'id="positions-body"' in _html()

    def test_signals_body_id(self):
        assert 'id="signals-body"' in _html()

    def test_orders_body_id(self):
        assert 'id="orders-body"' in _html()

    def test_pnl_chart_id(self):
        assert 'id="pnl-chart"' in _html()

    def test_fetch_status_url(self):
        assert "/trading/status" in _html()

    def test_fetch_positions_url(self):
        assert "/trading/positions" in _html()

    def test_fetch_strategy_url(self):
        assert "/trading/strategy" in _html()

    def test_responsive_css(self):
        assert "@media" in _html()

    def test_polling_intervals(self):
        html = _html()
        assert "setInterval(fetchStatus, 5000)" in html
        assert "setInterval(fetchPositions, 10000)" in html

    def test_signal_reason_column(self):
        """시그널 테이블에 판단 근거 헤더 존재"""
        assert "판단 근거" in _html()

    def test_signal_reason_in_js(self):
        """JS가 reason_detail 필드를 시그널 테이블에 렌더링"""
        assert "s.reason_detail" in _html()

    def test_order_reason_detail_column(self):
        """주문 테이블에 상세 헤더 존재"""
        html = _html()
        # 주문 테이블 thead에 상세 컬럼
        assert "o.reason_detail" in html

    def test_signal_hold_grey_style(self):
        """HOLD 시그널은 회색 스타일"""
        assert "color:#64748b" in _html()
