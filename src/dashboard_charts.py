import tempfile
import webbrowser
import plotly.graph_objects as go
from plotly.offline import plot
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from dashboard_db import connect_db


# ── HTML wrapper ─────────────────────────────────────────────────────────────

def _open_html(fig, title, header_color):
    html_content = plot(fig, output_type='div', include_plotlyjs=True)
    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Chizzling POS - {title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #FAF3E1; }}
        .header {{ background-color: {header_color}; color: white; padding: 20px; text-align: center; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="header"><h1>Chizzling POS - {title}</h1></div>
    {html_content}
</body>
</html>"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(full_html)
        temp_path = f.name
    webbrowser.open(f'file://{temp_path}')


# ── Top Products chart ────────────────────────────────────────────────────────

def open_top_products_chart(fig):
    _open_html(fig, "Sales Analytics", "#FF6600")


def build_top_products_figure(products, quantities, sales, title, screen_width):
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Top Products by Quantity', 'Top Products by Revenue'),
        horizontal_spacing=0.15
    )
    fig.add_trace(go.Bar(
        y=products, x=quantities, orientation='h', name='Quantity',
        marker_color='#28A745', text=[f'{int(q)}' for q in quantities],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Quantity: %{x}<extra></extra>'
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        y=products, x=sales, orientation='h', name='Revenue',
        marker_color='#007BFF', text=[f'₱{s:.0f}' for s in sales],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Revenue: ₱%{x:.2f}<extra></extra>'
    ), row=1, col=2)
    fig.update_layout(
        title={'text': f'<b>{title}</b>', 'x': 0.5, 'xanchor': 'center',
               'font': {'size': 18, 'color': '#333'}},
        showlegend=False, height=500,
        width=min(int(screen_width * 0.8), 1400),
        plot_bgcolor='white', paper_bgcolor='white',
        font={'family': 'Arial', 'size': 12},
        margin=dict(l=40, r=40, t=80, b=60)
    )
    fig.update_xaxes(title_text="Quantity Sold", row=1, col=1, gridcolor='#E5E5E5')
    fig.update_xaxes(title_text="Revenue (₱)", row=1, col=2, gridcolor='#E5E5E5')
    fig.update_yaxes(categoryorder='total ascending', row=1, col=1)
    fig.update_yaxes(categoryorder='total ascending', row=1, col=2)
    return fig


# ── Revenue chart ─────────────────────────────────────────────────────────────

def open_revenue_chart(results, title, screen_width):
    top = results[:10]
    products = [r[0] for r in top]
    revenues = [r[3] for r in top]
    quantities = [r[2] for r in top]
    prices = [r[1] for r in top]

    qty_sorted = sorted(zip(products, quantities), key=lambda x: x[1], reverse=True)
    qty_products = [i[0] for i in qty_sorted]
    qty_values = [i[1] for i in qty_sorted]

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Top Products by Revenue', 'Top Products by Quantity Sold',
                        'Price vs Revenue Analysis', 'Revenue Distribution'),
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "scatter"}, {"type": "pie"}]]
    )
    fig.add_trace(go.Bar(x=products, y=revenues, name='Total Revenue',
                         marker_color='#28A745',
                         text=[f'₱{r:.0f}' for r in revenues],
                         textposition='outside'), row=1, col=1)
    fig.add_trace(go.Bar(x=qty_products, y=qty_values, name='Quantity Sold',
                         marker_color='#007BFF',
                         text=[f'{int(q)}' for q in qty_values],
                         textposition='outside'), row=1, col=2)
    fig.add_trace(go.Scatter(x=prices, y=revenues, mode='markers+text',
                             name='Price vs Revenue',
                             marker=dict(size=10, color='#FFC107'),
                             text=[p[:10] + '...' if len(p) > 10 else p for p in products],
                             textposition='top center'), row=2, col=1)
    fig.add_trace(go.Pie(
        labels=[p[:15] + '...' if len(p) > 15 else p for p in products],
        values=revenues, name="Revenue Share"), row=2, col=2)

    fig.update_layout(
        title={'text': f'<b>Revenue Analysis - {title}</b>', 'x': 0.5,
               'xanchor': 'center', 'font': {'size': 20, 'color': '#333'}},
        showlegend=False, height=800,
        width=min(int(screen_width * 0.9), 1600),
        plot_bgcolor='white', paper_bgcolor='white',
        font={'family': 'Arial', 'size': 11}
    )
    fig.update_xaxes(title_text="Products", row=1, col=1, tickangle=45)
    fig.update_yaxes(title_text="Revenue (₱)", row=1, col=1)
    fig.update_xaxes(title_text="Products", row=1, col=2, tickangle=45)
    fig.update_yaxes(title_text="Quantity Sold", row=1, col=2)
    fig.update_xaxes(title_text="Unit Price (₱)", row=2, col=1)
    fig.update_yaxes(title_text="Revenue (₱)", row=2, col=1)

    _open_html(fig, "Revenue Analysis", "#17A2B8")


# ── Time-series helpers ───────────────────────────────────────────────────────

def _build_period_dates(period):
    """Return list of date specs and a title string."""
    today = datetime.now()
    if period == "daily":
        dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
        return "daily", dates, "Daily Sales Progression (Last 7 Days)"
    elif period == "weekly":
        dates = []
        for i in range(3, -1, -1):
            ws = today - timedelta(weeks=i, days=today.weekday())
            we = ws + timedelta(days=6)
            dates.append((ws.strftime("%Y-%m-%d"), we.strftime("%Y-%m-%d"), f"Week {4-i}"))
        return "range", dates, "Weekly Sales Progression (Last 4 Weeks)"
    else:
        dates = []
        for i in range(5, -1, -1):
            md = today.replace(day=1) - timedelta(days=32 * i)
            md = md.replace(day=1)
            nm = md.replace(year=md.year + 1, month=1) if md.month == 12 else md.replace(month=md.month + 1)
            me = nm - timedelta(days=1)
            dates.append((md.strftime("%Y-%m-%d"), me.strftime("%Y-%m-%d"), md.strftime("%b %Y")))
        return "range", dates, "Monthly Revenue Progression (Last 6 Months)"


def open_sales_time_series(period, screen_width):
    conn = connect_db()
    with conn:
        cursor = conn.cursor()
        mode, dates, title = _build_period_dates(period if period in ("daily", "weekly") else "weekly")

        sales_data, transaction_data, labels = [], [], []
        if mode == "daily":
            for date in dates:
                cursor.execute("SELECT COUNT(*), COALESCE(SUM(total),0) FROM transactions WHERE DATE(date)=?", (date,))
                r = cursor.fetchone()
                transaction_data.append(r[0] or 0)
                sales_data.append(r[1] or 0)
                labels.append(datetime.fromisoformat(date).strftime("%m/%d"))
        else:
            for start, end, label in dates:
                cursor.execute("SELECT COUNT(*), COALESCE(SUM(total),0) FROM transactions WHERE DATE(date) BETWEEN ? AND ?", (start, end))
                r = cursor.fetchone()
                transaction_data.append(r[0] or 0)
                sales_data.append(r[1] or 0)
                labels.append(label)
    conn.close()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=labels, y=sales_data, mode='lines+markers+text',
                             name='Total Sales', line=dict(color='#28A745', width=3),
                             marker=dict(size=8, color='#28A745'),
                             text=[f'₱{s:.0f}' for s in sales_data],
                             textposition='top center',
                             hovertemplate='<b>%{x}</b><br>Sales: ₱%{y:.2f}<extra></extra>'))
    fig.add_trace(go.Scatter(x=labels, y=transaction_data, mode='lines+markers+text',
                             name='Transactions', line=dict(color='#007BFF', width=3),
                             marker=dict(size=8, color='#007BFF'),
                             text=[str(t) for t in transaction_data],
                             textposition='bottom center', yaxis='y2',
                             hovertemplate='<b>%{x}</b><br>Transactions: %{y}<extra></extra>'))
    fig.update_layout(
        title={'text': f'<b>{title}</b>', 'x': 0.5, 'xanchor': 'center',
               'font': {'size': 18, 'color': '#333'}},
        xaxis_title='Time Period',
        yaxis=dict(title='Sales (₱)', side='left', color='#28A745'),
        yaxis2=dict(title='Number of Transactions', side='right', overlaying='y', color='#007BFF'),
        height=500, width=min(int(screen_width * 0.8), 1200),
        plot_bgcolor='white', paper_bgcolor='white',
        font={'family': 'Arial', 'size': 12},
        legend=dict(x=0.02, y=0.98), hovermode='x unified'
    )
    _open_html(fig, "Sales Progression", "#28A745")


def open_revenue_time_series(period, screen_width):
    conn = connect_db()
    with conn:
        cursor = conn.cursor()
        mode, dates, title = _build_period_dates(period)

        revenue_data, quantity_data, labels = [], [], []
        if mode == "daily":
            for date in dates:
                cursor.execute("""SELECT COALESCE(SUM(ti.subtotal),0), COALESCE(SUM(ti.quantity),0)
                                  FROM transaction_items ti JOIN transactions t ON ti.transaction_id=t.id
                                  WHERE DATE(t.date)=?""", (date,))
                r = cursor.fetchone()
                revenue_data.append(r[0] or 0)
                quantity_data.append(r[1] or 0)
                labels.append(datetime.fromisoformat(date).strftime("%m/%d"))
        else:
            for start, end, label in dates:
                cursor.execute("""SELECT COALESCE(SUM(ti.subtotal),0), COALESCE(SUM(ti.quantity),0)
                                  FROM transaction_items ti JOIN transactions t ON ti.transaction_id=t.id
                                  WHERE DATE(t.date) BETWEEN ? AND ?""", (start, end))
                r = cursor.fetchone()
                revenue_data.append(r[0] or 0)
                quantity_data.append(r[1] or 0)
                labels.append(label)
    conn.close()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=labels, y=revenue_data, mode='lines+markers+text',
                             name='Total Revenue', line=dict(color='#17A2B8', width=3),
                             marker=dict(size=8, color='#17A2B8'),
                             text=[f'₱{r:.0f}' for r in revenue_data],
                             textposition='top center',
                             hovertemplate='<b>%{x}</b><br>Revenue: ₱%{y:.2f}<extra></extra>'))
    fig.add_trace(go.Scatter(x=labels, y=quantity_data, mode='lines+markers+text',
                             name='Items Sold', line=dict(color='#FFC107', width=3),
                             marker=dict(size=8, color='#FFC107'),
                             text=[str(int(q)) for q in quantity_data],
                             textposition='bottom center', yaxis='y2',
                             hovertemplate='<b>%{x}</b><br>Items Sold: %{y}<extra></extra>'))
    fig.update_layout(
        title={'text': f'<b>{title}</b>', 'x': 0.5, 'xanchor': 'center',
               'font': {'size': 18, 'color': '#333'}},
        xaxis_title='Time Period',
        yaxis=dict(title='Revenue (₱)', side='left', color='#17A2B8'),
        yaxis2=dict(title='Items Sold', side='right', overlaying='y', color='#FFC107'),
        height=500, width=min(int(screen_width * 0.8), 1200),
        plot_bgcolor='white', paper_bgcolor='white',
        font={'family': 'Arial', 'size': 12},
        legend=dict(x=0.02, y=0.98), hovermode='x unified'
    )
    _open_html(fig, "Revenue Progression", "#17A2B8")
