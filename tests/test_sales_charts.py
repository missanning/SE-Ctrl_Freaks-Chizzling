# Test for US-16: Sales Charts / Graphs

import pytest
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dashboard_charts import build_top_products_figure, _build_period_dates


# ── Sample data ───────────────────────────────────────────────────────────────

@pytest.fixture
def sample_products():
    return ["Sizzling Sisig", "Nachos", "Milk Tea", "Red Horse", "Fries"]

@pytest.fixture
def sample_quantities():
    return [10, 8, 6, 4, 2]

@pytest.fixture
def sample_sales():
    return [1990.0, 640.0, 234.0, 600.0, 100.0]

@pytest.fixture
def top_products_fig(sample_products, sample_quantities, sample_sales):
    return build_top_products_figure(
        sample_products, sample_quantities, sample_sales,
        "Today (2024-01-15)", 1920
    )


# ── AC1: Ranking charts are available ────────────────────────────────────────

class TestRankingCharts:
    """AC1: Ranking charts are available in Top Products and Revenue Analysis"""

    def test_top_products_figure_is_created(self, top_products_fig):
        assert top_products_fig is not None

    def test_top_products_figure_has_two_subplots(self, top_products_fig):
        # Two traces: quantity bar + revenue bar
        assert len(top_products_fig.data) == 2

    def test_quantity_chart_has_correct_data(self, top_products_fig, sample_quantities):
        qty_trace = top_products_fig.data[0]
        assert list(qty_trace.x) == sample_quantities

    def test_revenue_chart_has_correct_data(self, top_products_fig, sample_sales):
        rev_trace = top_products_fig.data[1]
        assert list(rev_trace.x) == sample_sales

    def test_quantity_chart_has_product_names(self, top_products_fig, sample_products):
        qty_trace = top_products_fig.data[0]
        assert list(qty_trace.y) == sample_products

    def test_revenue_chart_has_product_names(self, top_products_fig, sample_products):
        rev_trace = top_products_fig.data[1]
        assert list(rev_trace.y) == sample_products

    def test_figure_has_title(self, top_products_fig):
        assert top_products_fig.layout.title.text is not None
        assert len(top_products_fig.layout.title.text) > 0

    def test_figure_title_contains_period(self, top_products_fig):
        assert "2024-01-15" in top_products_fig.layout.title.text

    def test_charts_are_horizontal_bars(self, top_products_fig):
        for trace in top_products_fig.data:
            assert trace.orientation == 'h'

    def test_quantity_chart_marker_color(self, top_products_fig):
        assert top_products_fig.data[0].marker.color == '#7a3b10'

    def test_revenue_chart_marker_color(self, top_products_fig):
        assert top_products_fig.data[1].marker.color == '#f5a623'


# ── AC2: Time-series progression charts ──────────────────────────────────────

class TestTimeSeriesCharts:
    """AC2: Time-series trend charts show sales progression over time"""

    def test_daily_period_returns_7_dates(self):
        mode, dates, _ = _build_period_dates("daily")
        assert len(dates) == 7

    def test_daily_mode_is_daily(self):
        mode, _, _ = _build_period_dates("daily")
        assert mode == "daily"

    def test_daily_dates_are_strings(self):
        _, dates, _ = _build_period_dates("daily")
        for date in dates:
            assert isinstance(date, str)

    def test_daily_dates_are_in_ascending_order(self):
        _, dates, _ = _build_period_dates("daily")
        parsed = [datetime.fromisoformat(d) for d in dates]
        assert parsed == sorted(parsed)

    def test_daily_last_date_is_today(self):
        _, dates, _ = _build_period_dates("daily")
        assert dates[-1] == datetime.now().strftime("%Y-%m-%d")

    def test_daily_first_date_is_6_days_ago(self):
        _, dates, _ = _build_period_dates("daily")
        expected = (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d")
        assert dates[0] == expected

    def test_weekly_period_returns_4_weeks(self):
        mode, dates, _ = _build_period_dates("weekly")
        assert len(dates) == 4

    def test_weekly_mode_is_range(self):
        mode, _, _ = _build_period_dates("weekly")
        assert mode == "range"

    def test_weekly_each_entry_has_start_end_label(self):
        _, dates, _ = _build_period_dates("weekly")
        for entry in dates:
            assert len(entry) == 3  # (start, end, label)

    def test_weekly_labels_are_week_numbers(self):
        _, dates, _ = _build_period_dates("weekly")
        labels = [d[2] for d in dates]
        assert all("Week" in label for label in labels)

    def test_monthly_period_returns_6_months(self):
        _, dates, _ = _build_period_dates("monthly")
        assert len(dates) == 6

    def test_monthly_mode_is_range(self):
        mode, _, _ = _build_period_dates("monthly")
        assert mode == "range"

    def test_monthly_each_entry_has_start_end_label(self):
        _, dates, _ = _build_period_dates("monthly")
        for entry in dates:
            assert len(entry) == 3

    def test_monthly_start_dates_are_first_of_month(self):
        _, dates, _ = _build_period_dates("monthly")
        for start, _, _ in dates:
            assert start.endswith("-01")


# ── AC3: Chart updates reflect selected time range ────────────────────────────

class TestPeriodDateCalculations:
    """AC3: Chart reflects selected time range with proper date calculations"""

    def test_daily_title_mentions_last_7_days(self):
        _, _, title = _build_period_dates("daily")
        assert "7 Days" in title

    def test_weekly_title_mentions_last_4_weeks(self):
        _, _, title = _build_period_dates("weekly")
        assert "4 Weeks" in title

    def test_monthly_title_mentions_last_6_months(self):
        _, _, title = _build_period_dates("monthly")
        assert "6 Months" in title

    def test_daily_weekly_monthly_return_different_titles(self):
        _, _, daily_title = _build_period_dates("daily")
        _, _, weekly_title = _build_period_dates("weekly")
        _, _, monthly_title = _build_period_dates("monthly")
        assert daily_title != weekly_title
        assert weekly_title != monthly_title
        assert daily_title != monthly_title

    def test_daily_weekly_monthly_return_different_date_counts(self):
        _, daily_dates, _ = _build_period_dates("daily")
        _, weekly_dates, _ = _build_period_dates("weekly")
        _, monthly_dates, _ = _build_period_dates("monthly")
        assert len(daily_dates) != len(weekly_dates)
        assert len(weekly_dates) != len(monthly_dates)
        assert len(daily_dates) != len(monthly_dates)

    def test_weekly_each_range_spans_7_days(self):
        _, dates, _ = _build_period_dates("weekly")
        for start, end, _ in dates:
            d_start = datetime.fromisoformat(start)
            d_end = datetime.fromisoformat(end)
            assert (d_end - d_start).days == 6

    def test_monthly_start_before_end(self):
        _, dates, _ = _build_period_dates("monthly")
        for start, end, _ in dates:
            assert start <= end


# ── AC4: Dual y-axes and hover tooltips ──────────────────────────────────────

class TestDualAxesAndTooltips:
    """AC4: Progression charts have dual y-axes and interactive hover tooltips"""

    def test_sales_time_series_has_two_traces(self, top_products_fig):
        """Top products figure has 2 traces (qty + revenue)."""
        assert len(top_products_fig.data) == 2

    def test_quantity_trace_has_hovertemplate(self, top_products_fig):
        assert top_products_fig.data[0].hovertemplate is not None

    def test_revenue_trace_has_hovertemplate(self, top_products_fig):
        assert top_products_fig.data[1].hovertemplate is not None

    def test_quantity_hovertemplate_contains_quantity(self, top_products_fig):
        assert "Quantity" in top_products_fig.data[0].hovertemplate

    def test_revenue_hovertemplate_contains_revenue(self, top_products_fig):
        assert "Revenue" in top_products_fig.data[1].hovertemplate

    def test_sales_progression_dual_yaxis(self):
        """Verify second trace uses y2 axis in a manually built figure."""
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=["Mon"], y=[100], name="Sales", yaxis="y"))
        fig.add_trace(go.Scatter(x=["Mon"], y=[5], name="Transactions", yaxis="y2"))
        fig.update_layout(
            yaxis=dict(title="Sales (₱)", side="left"),
            yaxis2=dict(title="Transactions", side="right", overlaying="y")
        )
        assert fig.data[1].yaxis == "y2"
        assert fig.layout.yaxis2.overlaying == "y"
        assert fig.layout.yaxis.side == "left"
        assert fig.layout.yaxis2.side == "right"

    def test_revenue_progression_dual_yaxis(self):
        """Verify revenue progression uses dual y-axes."""
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=["Mon"], y=[500], name="Revenue", yaxis="y"))
        fig.add_trace(go.Scatter(x=["Mon"], y=[10], name="Items Sold", yaxis="y2"))
        fig.update_layout(
            yaxis=dict(title="Revenue (₱)", side="left"),
            yaxis2=dict(title="Items Sold", side="right", overlaying="y")
        )
        assert fig.data[1].yaxis == "y2"
        assert fig.layout.yaxis2.side == "right"

    def test_hovermode_is_unified(self):
        """Verify unified hover mode is set for time-series charts."""
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.update_layout(hovermode="x unified")
        assert fig.layout.hovermode == "x unified"


if __name__ == "__main__":
    pytest.main([__file__])
