"""공통 HTML 리포트 테마 — 다크 테마 CSS + HTML 골격"""

CHART_JS_CDN = "https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"

# 모든 리포트에서 공유하는 다크 테마 기본 CSS
DARK_THEME_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, 'Pretendard', sans-serif; background: #0f1117; color: #e0e0e0; }
.container { max-width: 1400px; margin: 0 auto; padding: 24px; }
header { text-align: center; padding: 40px 0 24px; }
header h1 { font-size: 28px; font-weight: 700; color: #fff; }
header p { color: #888; margin-top: 8px; font-size: 14px; }

.positive { color: #22c55e; }
.negative { color: #ef4444; }

.section { background: #1a1d27; border-radius: 12px; padding: 24px; margin: 20px 0; }
.section h2 { font-size: 18px; color: #fff; margin-bottom: 16px; }
.summary-card { background: #1a1d27; border-radius: 12px; padding: 20px; }
.summary-card h3 { font-size: 14px; color: #aaa; margin-bottom: 8px; }
.metric-main { font-size: 32px; font-weight: 700; }
.metric-label { font-size: 12px; color: #666; margin-bottom: 12px; }
.metric-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.metric-value { font-size: 16px; font-weight: 600; display: block; }
.metric-sub { font-size: 11px; color: #666; }

table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { background: #252830; color: #aaa; font-weight: 600; padding: 10px 12px; text-align: right; }
th:first-child { text-align: left; }
td { padding: 10px 12px; border-bottom: 1px solid #252830; text-align: right; }
td:first-child { text-align: left; }

.stock-cell { display: flex; flex-direction: column; gap: 2px; }
.stock-code { font-weight: 600; color: #fff; font-size: 13px; }
.stock-name { color: #888; font-size: 11px; }

.detail-btn { background: #2563eb; color: #fff; border: none; border-radius: 6px; padding: 4px 12px; cursor: pointer; font-size: 12px; }
.detail-btn:hover { background: #1d4ed8; }
.detail-panel { background: #1a1d27; border-radius: 12px; padding: 24px; margin: 12px 0; }
.detail-panel h3 { font-size: 16px; color: #fff; margin-bottom: 16px; }
.chart-container { height: 300px; margin-bottom: 24px; }

.trade-table { font-size: 12px; }
.trade-table th { background: #1e2028; font-size: 11px; padding: 6px; }
.trade-table td { padding: 5px 6px; border-bottom: 1px solid #1e2028; }

.badge { display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; }
.badge-red { background: rgba(239,68,68,0.15); color: #f87171; }
.badge-orange { background: rgba(245,158,11,0.15); color: #fbbf24; }
.badge-blue { background: rgba(59,130,246,0.15); color: #60a5fa; }
.badge-green { background: rgba(34,197,94,0.15); color: #4ade80; }

.buy-badge { background: #065f46; color: #10b981; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.sell-badge { background: #7f1d1d; color: #ef4444; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.hold-badge { background: #374151; color: #9ca3af; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.reason-badge { color: #fff; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 600; }

footer { text-align: center; padding: 32px; color: #555; font-size: 12px; }
""".strip()


def wrap_html(
    title: str,
    body: str,
    *,
    extra_css: str = "",
    extra_js: str = "",
    include_chartjs: bool = True,
) -> str:
    """공통 HTML 골격: <!DOCTYPE html> + <head>(CSS) + <body> + Chart.js

    Args:
        title: 페이지 제목
        body: <body> 내부 HTML
        extra_css: 리포트별 추가 CSS
        extra_js: </body> 직전에 삽입할 JavaScript
        include_chartjs: Chart.js CDN 포함 여부 (canvas 기반 리포트는 False)
    """
    chartjs_tag = f'<script src="{CHART_JS_CDN}"></script>' if include_chartjs else ""
    js_block = f"<script>\n{extra_js}\n</script>" if extra_js else ""

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
{chartjs_tag}
<style>
{DARK_THEME_CSS}
{extra_css}
</style>
</head>
<body>
{body}
{js_block}
</body>
</html>"""
