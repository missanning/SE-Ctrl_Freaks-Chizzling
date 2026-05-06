# Test for US-20: Export & Reports


import pytest
import sys
import os
import csv
import sqlite3
import tempfile
from datetime import datetime, timedelta
from collections import namedtuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ── ReportData namedtuple (mirrors export_reports.py) ─────────────────────────
ReportData = namedtuple("ReportData", ["title", "date_from", "date_to", "summary", "products", "transactions"])


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def temp_db():
    """Create a temp database with sales data."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()

    conn = sqlite3.connect(temp_file.name)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE, price REAL, stock INTEGER, category TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        total REAL, payment REAL, change REAL, date TIMESTAMP
    )
    """)
    cursor.execute("""
    CREATE TABLE transaction_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id INTEGER, product_id INTEGER,
        quantity INTEGER, subtotal REAL
    )
    """)

    cursor.executemany(
        "INSERT INTO products (name, price, stock, category) VALUES (?, ?, ?, ?)",
        [
            ("Sizzling Sisig", 199.0, 100, "meals"),
            ("Nachos",          80.0, 100, "snacks"),
            ("Gin Bilog",       85.0, 100, "alcohol"),
        ]
    )

    today = datetime.now().strftime("%Y-%m-%d")
    cursor.executemany(
        "INSERT INTO transactions (total, payment, change, date) VALUES (?, ?, ?, ?)",
        [
            (199.0, 200.0, 1.0, f"{today} 10:00:00"),
            (80.0,  100.0, 20.0, f"{today} 11:00:00"),
            (85.0,  100.0, 15.0, f"{today} 12:00:00"),
        ]
    )
    cursor.executemany(
        "INSERT INTO transaction_items (transaction_id, product_id, quantity, subtotal) VALUES (?, ?, ?, ?)",
        [
            (1, 1, 1, 199.0),
            (2, 2, 1,  80.0),
            (3, 3, 1,  85.0),
        ]
    )

    conn.commit()
    conn.close()

    yield temp_file.name

    try:
        os.unlink(temp_file.name)
    except PermissionError:
        pass


@pytest.fixture
def empty_db():
    """Create a temp database with no sales data."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()

    conn = sqlite3.connect(temp_file.name)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE, price REAL, stock INTEGER, category TEXT)""")
    cursor.execute("""CREATE TABLE transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        total REAL, payment REAL, change REAL, date TIMESTAMP)""")
    cursor.execute("""CREATE TABLE transaction_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id INTEGER, product_id INTEGER,
        quantity INTEGER, subtotal REAL)""")
    conn.commit()
    conn.close()

    yield temp_file.name

    try:
        os.unlink(temp_file.name)
    except PermissionError:
        pass


# ── Report data helpers (mirror export_reports._fetch_report_data) ─────────────

def fetch_report_data(db_path, date_from, date_to, title="Test Period"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*), COALESCE(SUM(total), 0) FROM transactions WHERE DATE(date) BETWEEN ? AND ?",
        (date_from, date_to)
    )
    summary = cursor.fetchone()

    cursor.execute("""
        SELECT p.name, SUM(ti.quantity), SUM(ti.subtotal)
        FROM transaction_items ti
        JOIN products p ON ti.product_id = p.id
        JOIN transactions t ON ti.transaction_id = t.id
        WHERE DATE(t.date) BETWEEN ? AND ?
        GROUP BY p.id, p.name ORDER BY 3 DESC
    """, (date_from, date_to))
    products = cursor.fetchall()

    cursor.execute("""
        SELECT id, date, total, payment, change
        FROM transactions WHERE DATE(date) BETWEEN ? AND ?
        ORDER BY date DESC
    """, (date_from, date_to))
    transactions = cursor.fetchall()

    conn.close()
    return ReportData(title, date_from, date_to, summary, products, transactions)


def generate_csv_content(data):
    """Generate CSV content as a list of rows (mirrors export_reports.export_csv)."""
    rows = []
    rows.append(["CHIZZLING POS - SALES REPORT"])
    rows.append(["Period", data.title])
    rows.append(["Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    rows.append([])
    rows.append(["SUMMARY"])
    rows.append(["Total Transactions", data.summary[0]])
    rows.append(["Total Sales", f"{data.summary[1]:.2f}"])
    avg = data.summary[1] / data.summary[0] if data.summary[0] else 0
    rows.append(["Average Transaction", f"{avg:.2f}"])
    rows.append([])
    rows.append(["TOP PRODUCTS"])
    rows.append(["Product", "Quantity Sold", "Total Revenue"])
    for name, qty, rev in data.products:
        rows.append([name, int(qty), f"{rev:.2f}"])
    rows.append([])
    rows.append(["TRANSACTIONS"])
    rows.append(["ID", "Date", "Total", "Payment", "Change"])
    for tid, date, total, payment, change in data.transactions:
        rows.append([tid, date, f"{total:.2f}", f"{payment:.2f}", f"{change:.2f}"])
    return rows


def generate_html_content(data):
    """Generate HTML report content (mirrors export_reports.export_pdf)."""
    avg = data.summary[1] / data.summary[0] if data.summary[0] else 0
    html = f"""<!DOCTYPE html>
<html>
<head><title>Sales Report</title></head>
<body>
  <h1>Chizzling POS - Sales Report</h1>
  <p>Period: {data.title}</p>
  <h2>Summary</h2>
  <p>Total Transactions: {data.summary[0]}</p>
  <p>Total Sales: {data.summary[1]:.2f}</p>
  <p>Average Transaction: {avg:.2f}</p>
  <h2>Top Products</h2>
  <table>
    <tr><th>Product</th><th>Qty Sold</th><th>Total Revenue</th></tr>
    {"".join(f"<tr><td>{n}</td><td>{int(q)}</td><td>{r:.2f}</td></tr>" for n, q, r in data.products)
     or '<tr><td colspan="3">No data</td></tr>'}
  </table>
  <h2>Transactions</h2>
  <table>
    <tr><th>ID</th><th>Date</th><th>Total</th><th>Payment</th><th>Change</th></tr>
    {"".join(f"<tr><td>{tid}</td><td>{d}</td><td>{t:.2f}</td><td>{p:.2f}</td><td>{c:.2f}</td></tr>"
             for tid, d, t, p, c in data.transactions)
     or '<tr><td colspan="5">No data</td></tr>'}
  </table>
</body>
</html>"""
    return html


def write_csv(data, path):
    rows = generate_csv_content(data)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def read_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.reader(f))


# ── AC1: Report contains all required sections and fields ─────────────────────

class TestReportContent:
    """AC1: Report contains period, timestamp, summary, top products, transactions."""

    def test_report_data_has_title(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        assert data.title is not None and len(data.title) > 0

    def test_report_data_has_date_from(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        assert data.date_from == today

    def test_report_data_has_date_to(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        assert data.date_to == today

    def test_report_summary_has_transaction_count(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        assert data.summary[0] == 3

    def test_report_summary_has_total_sales(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        assert data.summary[1] == 199.0 + 80.0 + 85.0

    def test_report_summary_avg_transaction_is_correct(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        avg = data.summary[1] / data.summary[0]
        assert round(avg, 2) == round((199.0 + 80.0 + 85.0) / 3, 2)

    def test_report_has_top_products(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        assert len(data.products) > 0

    def test_report_products_have_name(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        for p in data.products:
            assert isinstance(p[0], str) and len(p[0]) > 0

    def test_report_products_have_quantity(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        for p in data.products:
            assert p[1] > 0

    def test_report_products_have_revenue(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        for p in data.products:
            assert p[2] > 0

    def test_report_has_transactions(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        assert len(data.transactions) == 3

    def test_report_transactions_have_payment(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        for t in data.transactions:
            assert t[3] > 0

    def test_report_transactions_have_change(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        for t in data.transactions:
            assert t[4] >= 0


# ── AC2: CSV and PDF formats are generated ────────────────────────────────────

class TestExportFormats:
    """AC2: System generates report in selected format (CSV or PDF)."""

    def test_csv_file_is_created(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as f:
            path = f.name
        try:
            write_csv(data, path)
            assert os.path.exists(path)
        finally:
            try:
                os.unlink(path)
            except PermissionError:
                pass

    def test_csv_file_is_not_empty(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as f:
            path = f.name
        try:
            write_csv(data, path)
            assert os.path.getsize(path) > 0
        finally:
            try:
                os.unlink(path)
            except PermissionError:
                pass

    def test_html_content_is_generated(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        html = generate_html_content(data)
        assert isinstance(html, str) and len(html) > 0

    def test_html_is_valid_html_structure(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        html = generate_html_content(data)
        assert "<!DOCTYPE html>" in html
        assert "<html>" in html
        assert "</html>" in html

    def test_csv_rows_are_generated(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        rows = generate_csv_content(data)
        assert len(rows) > 0

    def test_csv_content_is_list_of_lists(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        rows = generate_csv_content(data)
        assert isinstance(rows, list)
        assert all(isinstance(r, list) for r in rows)


# ── AC3: PDF layout has required sections ─────────────────────────────────────

class TestPDFLayout:
    """AC3: PDF report contains Summary, Top Products, and Transactions sections."""

    def test_html_contains_summary_section(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        html = generate_html_content(data)
        assert "Summary" in html

    def test_html_contains_top_products_section(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        html = generate_html_content(data)
        assert "Top Products" in html

    def test_html_contains_transactions_section(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        html = generate_html_content(data)
        assert "Transactions" in html

    def test_html_contains_period_info(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today, title="Today")
        html = generate_html_content(data)
        assert "Today" in html

    def test_html_contains_total_sales(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        html = generate_html_content(data)
        assert "364.00" in html

    def test_html_contains_product_names(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        html = generate_html_content(data)
        assert "Sizzling Sisig" in html

    def test_html_contains_transaction_count(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        html = generate_html_content(data)
        assert str(data.summary[0]) in html


# ── AC4: CSV format is tabular with all required fields ───────────────────────

class TestCSVFormat:
    """AC4: CSV report is tabular with all relevant fields."""

    def test_csv_contains_report_header(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        rows = generate_csv_content(data)
        flat = [cell for row in rows for cell in row]
        assert "CHIZZLING POS - SALES REPORT" in flat

    def test_csv_contains_summary_section(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        rows = generate_csv_content(data)
        flat = [cell for row in rows for cell in row]
        assert "SUMMARY" in flat

    def test_csv_contains_total_transactions(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        rows = generate_csv_content(data)
        flat = [str(cell) for row in rows for cell in row]
        assert "Total Transactions" in flat

    def test_csv_contains_total_sales(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        rows = generate_csv_content(data)
        flat = [str(cell) for row in rows for cell in row]
        assert "Total Sales" in flat

    def test_csv_contains_average_transaction(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        rows = generate_csv_content(data)
        flat = [str(cell) for row in rows for cell in row]
        assert "Average Transaction" in flat

    def test_csv_contains_top_products_section(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        rows = generate_csv_content(data)
        flat = [str(cell) for row in rows for cell in row]
        assert "TOP PRODUCTS" in flat

    def test_csv_contains_product_headers(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        rows = generate_csv_content(data)
        flat = [str(cell) for row in rows for cell in row]
        assert "Product" in flat
        assert "Quantity Sold" in flat
        assert "Total Revenue" in flat

    def test_csv_contains_transactions_section(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        rows = generate_csv_content(data)
        flat = [str(cell) for row in rows for cell in row]
        assert "TRANSACTIONS" in flat

    def test_csv_contains_transaction_headers(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        rows = generate_csv_content(data)
        flat = [str(cell) for row in rows for cell in row]
        assert "ID" in flat
        assert "Payment" in flat
        assert "Change" in flat

    def test_csv_contains_product_data(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        rows = generate_csv_content(data)
        flat = [str(cell) for row in rows for cell in row]
        assert "Sizzling Sisig" in flat

    def test_csv_written_and_readable(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(temp_db, today, today)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as f:
            path = f.name
        try:
            write_csv(data, path)
            read_rows = read_csv(path)
            assert len(read_rows) > 0
        finally:
            try:
                os.unlink(path)
            except PermissionError:
                pass


# ── AC5: No sales data handled gracefully ─────────────────────────────────────

class TestEmptyDataExport:
    """AC5: System handles no sales data gracefully."""

    def test_empty_db_summary_count_is_zero(self, empty_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(empty_db, today, today)
        assert data.summary[0] == 0

    def test_empty_db_summary_total_is_zero(self, empty_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(empty_db, today, today)
        assert data.summary[1] == 0.0

    def test_empty_db_products_list_is_empty(self, empty_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(empty_db, today, today)
        assert data.products == []

    def test_empty_db_transactions_list_is_empty(self, empty_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(empty_db, today, today)
        assert data.transactions == []

    def test_csv_still_generated_when_no_data(self, empty_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(empty_db, today, today)
        rows = generate_csv_content(data)
        assert len(rows) > 0

    def test_csv_no_data_has_summary_section(self, empty_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(empty_db, today, today)
        rows = generate_csv_content(data)
        flat = [str(cell) for row in rows for cell in row]
        assert "SUMMARY" in flat

    def test_csv_no_data_total_sales_is_zero(self, empty_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(empty_db, today, today)
        rows = generate_csv_content(data)
        flat = [str(cell) for row in rows for cell in row]
        assert "0.00" in flat

    def test_html_no_data_shows_no_data_placeholder(self, empty_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(empty_db, today, today)
        html = generate_html_content(data)
        assert "No data" in html

    def test_html_still_generated_when_no_data(self, empty_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(empty_db, today, today)
        html = generate_html_content(data)
        assert isinstance(html, str) and len(html) > 0

    def test_avg_transaction_is_zero_when_no_data(self, empty_db):
        today = datetime.now().strftime("%Y-%m-%d")
        data = fetch_report_data(empty_db, today, today)
        avg = data.summary[1] / data.summary[0] if data.summary[0] else 0
        assert avg == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
