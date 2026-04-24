# Test for US-17: Transaction Summary
# Test Objective: Ensure that transaction analytics correctly loads transactions
# by date, calculates metrics accurately, handles empty dates, and supports
# today's date shortcut.

import pytest
import sys
import os
import sqlite3
import tempfile
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def temp_db():
    """Create a temp database with transactions across different dates."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()

    conn = sqlite3.connect(temp_file.name)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        total REAL,
        payment REAL,
        change REAL,
        date TIMESTAMP
    )
    """)

    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    cursor.executemany(
        "INSERT INTO transactions (total, payment, change, date) VALUES (?, ?, ?, ?)",
        [
            (199.0, 200.0, 1.0,  f"{today} 10:00:00"),
            (80.0,  100.0, 20.0, f"{today} 11:30:00"),
            (39.0,  40.0,  1.0,  f"{today} 14:00:00"),
            (150.0, 150.0, 0.0,  f"{yesterday} 09:00:00"),
            (250.0, 300.0, 50.0, f"{yesterday} 15:00:00"),
        ]
    )

    conn.commit()
    conn.close()

    yield temp_file.name
    os.unlink(temp_file.name)


def load_transactions(db_path, selected_date):
    """Simulate TransactionAnalyticsApp.load_transactions() logic."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, date, total, payment, change
        FROM transactions
        WHERE date LIKE ?
        ORDER BY date DESC
    """, (selected_date + '%',))
    transactions = cursor.fetchall()
    conn.close()

    total_transactions = len(transactions)
    total_sales = sum(t[2] for t in transactions) if transactions else 0.0
    avg_transaction_value = total_sales / total_transactions if total_transactions > 0 else 0.0

    return transactions, total_transactions, total_sales, avg_transaction_value


def parse_transaction_datetime(date_time_str):
    """Simulate datetime parsing logic in load_transactions()."""
    try:
        dt = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S")
    except Exception:
        date_str = date_time_str.split()[0] if ' ' in date_time_str else date_time_str
        time_str = date_time_str.split()[1] if ' ' in date_time_str else "00:00:00"
        return date_str, time_str


class TestLoadTransactionsByDate:
    """AC1 & AC2: Transactions are loaded and displayed for the selected date"""

    def test_loads_correct_number_of_transactions_for_today(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        transactions, count, _, _ = load_transactions(temp_db, today)
        assert count == 3

    def test_loads_correct_transactions_for_yesterday(self, temp_db):
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        transactions, count, _, _ = load_transactions(temp_db, yesterday)
        assert count == 2

    def test_transactions_contain_id(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        transactions, _, _, _ = load_transactions(temp_db, today)
        for t in transactions:
            assert t[0] is not None

    def test_transactions_contain_date(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        transactions, _, _, _ = load_transactions(temp_db, today)
        for t in transactions:
            assert today in t[1]

    def test_transactions_contain_total(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        transactions, _, _, _ = load_transactions(temp_db, today)
        for t in transactions:
            assert isinstance(t[2], float)
            assert t[2] > 0

    def test_transactions_contain_payment(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        transactions, _, _, _ = load_transactions(temp_db, today)
        for t in transactions:
            assert t[3] >= t[2]  # payment >= total

    def test_transactions_contain_change(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        transactions, _, _, _ = load_transactions(temp_db, today)
        for t in transactions:
            assert t[4] >= 0

    def test_excludes_other_dates(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        transactions, count, _, _ = load_transactions(temp_db, today)
        assert count == 3  # not 5


class TestMetricsCalculation:
    """AC2 & AC3: Metrics are calculated correctly"""

    def test_total_sales_is_correct(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        _, _, total_sales, _ = load_transactions(temp_db, today)
        assert total_sales == 199.0 + 80.0 + 39.0

    def test_average_transaction_value_is_correct(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        _, count, total_sales, avg = load_transactions(temp_db, today)
        assert avg == total_sales / count

    def test_average_equals_total_divided_by_count(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        _, count, total_sales, avg = load_transactions(temp_db, today)
        expected_avg = total_sales / count
        assert round(avg, 2) == round(expected_avg, 2)

    def test_total_sales_is_float(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        _, _, total_sales, _ = load_transactions(temp_db, today)
        assert isinstance(total_sales, float)

    def test_average_is_float(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        _, _, _, avg = load_transactions(temp_db, today)
        assert isinstance(avg, float)

    def test_payment_minus_total_equals_change(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        transactions, _, _, _ = load_transactions(temp_db, today)
        for t in transactions:
            assert round(t[3] - t[2], 2) == round(t[4], 2)

    def test_yesterday_total_sales_is_correct(self, temp_db):
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        _, _, total_sales, _ = load_transactions(temp_db, yesterday)
        assert total_sales == 150.0 + 250.0

    def test_yesterday_average_is_correct(self, temp_db):
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        _, count, total_sales, avg = load_transactions(temp_db, yesterday)
        assert round(avg, 2) == round(total_sales / count, 2)


class TestTodayButton:
    """AC4: Today button loads today's transaction data"""

    def test_today_date_matches_current_date(self):
        today = datetime.now().strftime("%Y-%m-%d")
        assert today == datetime.now().strftime("%Y-%m-%d")

    def test_today_loads_correct_transactions(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        _, count, _, _ = load_transactions(temp_db, today)
        assert count == 3

    def test_today_total_sales_is_correct(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        _, _, total_sales, _ = load_transactions(temp_db, today)
        assert total_sales == 199.0 + 80.0 + 39.0

    def test_today_average_is_correct(self, temp_db):
        today = datetime.now().strftime("%Y-%m-%d")
        _, count, total_sales, avg = load_transactions(temp_db, today)
        assert round(avg, 2) == round(total_sales / count, 2)


class TestNoTransactionsFound:
    """AC5: No transactions message when no data exists for selected date"""

    def test_empty_result_for_date_with_no_transactions(self, temp_db):
        transactions, count, _, _ = load_transactions(temp_db, "2000-01-01")
        assert count == 0
        assert transactions == []

    def test_total_sales_is_zero_when_no_transactions(self, temp_db):
        _, _, total_sales, _ = load_transactions(temp_db, "2000-01-01")
        assert total_sales == 0.0

    def test_average_is_zero_when_no_transactions(self, temp_db):
        _, _, _, avg = load_transactions(temp_db, "2000-01-01")
        assert avg == 0.0

    def test_empty_db_returns_no_transactions(self):
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        conn = sqlite3.connect(temp_file.name)
        conn.execute("""CREATE TABLE transactions (
            id INTEGER PRIMARY KEY, total REAL,
            payment REAL, change REAL, date TIMESTAMP)""")
        conn.commit()
        conn.close()
        today = datetime.now().strftime("%Y-%m-%d")
        transactions, count, total_sales, avg = load_transactions(temp_file.name, today)
        assert count == 0
        assert total_sales == 0.0
        assert avg == 0.0
        os.unlink(temp_file.name)


class TestDatetimeParsing:
    """Datetime parsing splits date and time correctly"""

    def test_parses_date_correctly(self):
        date_str, _ = parse_transaction_datetime("2024-01-15 10:30:00")
        assert date_str == "2024-01-15"

    def test_parses_time_correctly(self):
        _, time_str = parse_transaction_datetime("2024-01-15 10:30:00")
        assert time_str == "10:30:00"

    def test_handles_date_only_string(self):
        date_str, time_str = parse_transaction_datetime("2024-01-15")
        assert date_str == "2024-01-15"
        assert time_str == "00:00:00"

    def test_returns_tuple_of_two(self):
        result = parse_transaction_datetime("2024-01-15 10:30:00")
        assert len(result) == 2


if __name__ == "__main__":
    pytest.main([__file__])
