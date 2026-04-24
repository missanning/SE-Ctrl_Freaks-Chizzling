import csv
import os
import subprocess
import tempfile
import time
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


# ── PDF Export (HTML → Microsoft Print to PDF) ───────────────────────────────

def export_pdf(period):
    data = _fetch_report_data(period)
    avg = data.summary[1] / data.summary[0] if data.summary[0] else 0
    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    default_name = f"sales_report_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")],
        initialfile=default_name,
        title="Save PDF Report"
    )
    if not path:
        return

    try:
        path = _safe_path(path)
    except ValueError as e:
        messagebox.showerror("Export Error", str(e))
        return

    product_rows = "".join(
        f"<tr><td>{name}</td><td>{int(qty)}</td><td>&#8369;{rev:.2f}</td></tr>"
        for name, qty, rev in data.products
    ) or '<tr><td colspan="3">No data</td></tr>'

    transaction_rows = "".join(
        f"<tr><td>{tid}</td><td>{date}</td><td>&#8369;{total:.2f}</td>"
        f"<td>&#8369;{payment:.2f}</td><td>&#8369;{change:.2f}</td></tr>"
        for tid, date, total, payment, change in data.transactions
    ) or '<tr><td colspan="5">No data</td></tr>'

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: Arial, sans-serif; font-size: 12px; color: #333; padding: 40px; }}
    .header {{ background: #FF6600; color: white; padding: 20px 30px; margin-bottom: 24px; }}
    .header h1 {{ font-size: 22px; margin-bottom: 4px; }}
    .header p {{ font-size: 11px; opacity: 0.85; }}
    .section {{ margin-bottom: 28px; }}
    .section h2 {{ font-size: 14px; color: #FF6600; border-bottom: 2px solid #FF6600;
                   padding-bottom: 4px; margin-bottom: 12px; }}
    .cards {{ display: flex; gap: 16px; margin-bottom: 8px; }}
    .card {{ flex: 1; border: 1px solid #ddd; border-left: 5px solid #FF6600;
             border-radius: 4px; padding: 14px 18px; background: #fff8f3; }}
    .card .label {{ font-size: 10px; color: #888; text-transform: uppercase; }}
    .card .value {{ font-size: 20px; font-weight: bold; color: #FF6600; margin-top: 4px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
    th {{ background: #FF6600; color: white; padding: 8px 10px; text-align: left; }}
    td {{ padding: 7px 10px; border-bottom: 1px solid #eee; }}
    tr:nth-child(even) td {{ background: #fff8f3; }}
    .footer {{ margin-top: 40px; text-align: center; font-size: 10px; color: #aaa; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>&#127859; Chizzling POS &mdash; Sales Report</h1>
    <p>Period: {data.title} &nbsp;&nbsp;|&nbsp;&nbsp; Generated: {generated}</p>
  </div>

  <div class="section">
    <h2>Summary</h2>
    <div class="cards">
      <div class="card"><div class="label">Total Transactions</div>
        <div class="value">{data.summary[0]}</div></div>
      <div class="card"><div class="label">Total Sales</div>
        <div class="value">&#8369;{data.summary[1]:.2f}</div></div>
      <div class="card"><div class="label">Avg Transaction</div>
        <div class="value">&#8369;{avg:.2f}</div></div>
    </div>
  </div>

  <div class="section">
    <h2>Top Products</h2>
    <table>
      <tr><th>Product</th><th>Qty Sold</th><th>Total Revenue</th></tr>
      {product_rows}
    </table>
  </div>

  <div class="section">
    <h2>Transactions</h2>
    <table>
      <tr><th>ID</th><th>Date</th><th>Total</th><th>Payment</th><th>Change</th></tr>
      {transaction_rows}
    </table>
  </div>

  <div class="footer">Chizzling POS &mdash; Confidential Sales Report</div>
</body>
</html>"""

    # Write HTML to a temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html",
                                     delete=False, encoding="utf-8") as f:
        f.write(html)
        tmp_html = f.name

    # Use Chrome/Edge headless to print HTML directly to PDF
    browsers = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    browser = next((b for b in browsers if os.path.exists(b)), None)

    if not browser:
        messagebox.showerror("Export Error", "Chrome or Edge not found. Cannot generate PDF.")
        os.remove(tmp_html)
        return

    try:
        subprocess.run([
            browser,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            f"--print-to-pdf={path}",
            "--print-to-pdf-no-header",
            tmp_html
        ], check=True, timeout=30,
           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        time.sleep(4)  # wait for Chrome to finish writing the file
        os.startfile(path)
        messagebox.showinfo("Export Successful", f"PDF report saved to:\n{path}")
    except Exception as e:
        messagebox.showerror("Export Error", f"Failed to generate PDF:\n{e}")
    finally:
        try:
            os.remove(tmp_html)
        except OSError:
            pass
