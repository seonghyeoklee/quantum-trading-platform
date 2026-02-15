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
