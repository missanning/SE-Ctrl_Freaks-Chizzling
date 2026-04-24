import csv
import os
import tempfile
import webbrowser
from collections import namedtuple
from datetime import datetime
from tkinter import filedialog, messagebox

from dashboard_db import connect_db, get_date_range

ReportData = namedtuple("ReportData", ["title", "date_from", "date_to", "summary", "products", "transactions"])

_SAFE_EXPORT_DIR = os.path.expanduser("~")


def _safe_path(path):
    """Ensure the save path stays within the user's home directory tree."""
    abs_path = os.path.realpath(os.path.abspath(path))
    if not abs_path.startswith(os.path.realpath(_SAFE_EXPORT_DIR)):
        raise ValueError(f"Export path outside allowed directory: {abs_path}")
    return abs_path


# ── Data fetching ─────────────────────────────────────────────────────────────

def _fetch_report_data(period):
    date_from, date_to, title = get_date_range(period)
    conn = connect_db()
    with conn:
        cur = conn.cursor()

        cur.execute("""SELECT COUNT(*), COALESCE(SUM(total), 0)
                       FROM transactions WHERE DATE(date) BETWEEN ? AND ?""",
                    (date_from, date_to))
        summary = cur.fetchone()

        cur.execute("""SELECT p.name, SUM(ti.quantity), SUM(ti.subtotal)
                       FROM transaction_items ti
                       JOIN products p ON ti.product_id = p.id
                       JOIN transactions t ON ti.transaction_id = t.id
                       WHERE DATE(t.date) BETWEEN ? AND ?
                       GROUP BY p.id, p.name ORDER BY 3 DESC""",
                    (date_from, date_to))
        products = cur.fetchall()

        cur.execute("""SELECT id, date, total, payment, change
                       FROM transactions WHERE DATE(date) BETWEEN ? AND ?
                       ORDER BY date DESC""",
                    (date_from, date_to))
        transactions = cur.fetchall()

    conn.close()
    return ReportData(title, date_from, date_to, summary, products, transactions)


# ── CSV Export ────────────────────────────────────────────────────────────────

def export_csv(period):
    data = _fetch_report_data(period)

    default_name = f"sales_report_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")],
        initialfile=default_name,
        title="Save CSV Report"
    )
    if not path:
        return

    try:
        path = _safe_path(path)
    except ValueError as e:
        messagebox.showerror("Export Error", str(e))
        return

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow(["CHIZZLING POS - SALES REPORT"])
        writer.writerow(["Period", data.title])
        writer.writerow(["Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow([])

        writer.writerow(["SUMMARY"])
        writer.writerow(["Total Transactions", data.summary[0]])
        writer.writerow(["Total Sales", f"{data.summary[1]:.2f}"])
        avg = data.summary[1] / data.summary[0] if data.summary[0] else 0
        writer.writerow(["Average Transaction", f"{avg:.2f}"])
        writer.writerow([])

        writer.writerow(["TOP PRODUCTS"])
        writer.writerow(["Product", "Quantity Sold", "Total Revenue"])
        for name, qty, rev in data.products:
            writer.writerow([name, int(qty), f"{rev:.2f}"])
        writer.writerow([])

        writer.writerow(["TRANSACTIONS"])
        writer.writerow(["ID", "Date", "Total", "Payment", "Change"])
        for tid, date, total, payment, change in data.transactions:
            writer.writerow([tid, date, f"{total:.2f}", f"{payment:.2f}", f"{change:.2f}"])

    messagebox.showinfo("Export Successful", f"CSV report saved to:\n{path}")


# ── PDF Export (HTML → browser print) ────────────────────────────────────────

def export_pdf(period):
    data = _fetch_report_data(period)
    avg = data.summary[1] / data.summary[0] if data.summary[0] else 0

    product_rows = "".join(
        f"<tr><td>{name}</td><td>{int(qty)}</td><td>&#8369;{rev:.2f}</td></tr>"
        for name, qty, rev in data.products
    )
    transaction_rows = "".join(
        f"<tr><td>{tid}</td><td>{date}</td><td>&#8369;{total:.2f}</td>"
        f"<td>&#8369;{payment:.2f}</td><td>&#8369;{change:.2f}</td></tr>"
        for tid, date, total, payment, change in data.transactions
    )

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Sales Report - {data.title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 40px; color: #333; }}
    h1 {{ color: #FF6600; border-bottom: 3px solid #FF6600; padding-bottom: 10px; }}
    h2 {{ color: #555; margin-top: 30px; }}
    .meta {{ color: #888; font-size: 13px; margin-bottom: 20px; }}
    .cards {{ display: flex; gap: 20px; margin: 20px 0; }}
    .card {{ background: #f5f5f5; border-left: 5px solid #FF6600;
             padding: 15px 25px; border-radius: 4px; flex: 1; }}
    .card .val {{ font-size: 24px; font-weight: bold; color: #FF6600; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
    th {{ background: #FF6600; color: white; padding: 8px 12px; text-align: left; }}
    td {{ padding: 7px 12px; border-bottom: 1px solid #ddd; }}
    tr:nth-child(even) td {{ background: #fafafa; }}
    .footer {{ margin-top: 40px; font-size: 12px; color: #aaa; text-align: center; }}
    @media print {{ button {{ display: none; }} }}
  </style>
</head>
<body>
  <h1>&#127859; Chizzling POS &mdash; Sales Report</h1>
  <p class="meta">Period: <strong>{data.title}</strong> &nbsp;|&nbsp;
     Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

  <button onclick="window.print()"
    style="background:#FF6600;color:white;border:none;padding:10px 24px;
           font-size:14px;border-radius:4px;cursor:pointer;margin-bottom:20px;">
    &#128438; Print / Save as PDF
  </button>

  <h2>Summary</h2>
  <div class="cards">
    <div class="card"><div>Total Transactions</div><div class="val">{data.summary[0]}</div></div>
    <div class="card"><div>Total Sales</div><div class="val">&#8369;{data.summary[1]:.2f}</div></div>
    <div class="card"><div>Avg Transaction</div><div class="val">&#8369;{avg:.2f}</div></div>
  </div>

  <h2>Top Products</h2>
  <table>
    <tr><th>Product</th><th>Quantity Sold</th><th>Total Revenue</th></tr>
    {product_rows if product_rows else '<tr><td colspan="3">No data</td></tr>'}
  </table>

  <h2>Transactions</h2>
  <table>
    <tr><th>ID</th><th>Date</th><th>Total</th><th>Payment</th><th>Change</th></tr>
    {transaction_rows if transaction_rows else '<tr><td colspan="5">No data</td></tr>'}
  </table>

  <div class="footer">Chizzling POS &mdash; Confidential Sales Report</div>
</body>
</html>"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        temp_path = f.name

    webbrowser.open(f"file://{temp_path}")
