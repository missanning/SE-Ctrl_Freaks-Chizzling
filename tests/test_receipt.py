# Test for US-02: Receipt After Sale

import pytest
import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from receipt_module import generate_receipt_text, save_receipt


@pytest.fixture
def sample_cart():
    """Sample cart: (id, name, qty, subtotal)"""
    return [
        (1, "Sizzling Sisig", 2, 398.0),
        (2, "Nachos", 1, 80.0),
        (3, "Milk Tea", 3, 117.0)
    ]


@pytest.fixture
def sample_receipt(sample_cart):
    return generate_receipt_text(
        transaction_id=101,
        date="2024-01-15 14:30:00",
        cart=sample_cart,
        total=595.0,
        change=5.0
    )


@pytest.fixture
def temp_receipts_dir(monkeypatch, tmp_path):
    """Redirect receipt saves to a temp directory."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


class TestGenerateReceiptText:
    """Test receipt text generation"""

    def test_receipt_contains_store_name(self, sample_receipt):
        assert "CHIZZLING POS" in sample_receipt

    def test_receipt_contains_transaction_id(self, sample_receipt):
        assert "Transaction ID: 101" in sample_receipt

    def test_receipt_contains_date(self, sample_receipt):
        assert "Date: 2024-01-15 14:30:00" in sample_receipt

    def test_receipt_contains_total(self, sample_receipt):
        assert "Total: 595.00" in sample_receipt

    def test_receipt_contains_payment(self, sample_receipt):
        # Payment = total + change = 595 + 5 = 600
        assert "Payment: 600.00" in sample_receipt

    def test_receipt_contains_change(self, sample_receipt):
        assert "Change: 5.00" in sample_receipt

    def test_receipt_contains_all_items(self, sample_receipt):
        assert "Sizzling Sisig" in sample_receipt
        assert "Nachos" in sample_receipt
        assert "Milk Tea" in sample_receipt

    def test_receipt_contains_item_quantity_and_subtotal(self, sample_receipt):
        # Sizzling Sisig: qty=2, subtotal=398.0, unit price=199.0
        assert "2 x 199.00 = 398.00" in sample_receipt

    def test_receipt_contains_thank_you(self, sample_receipt):
        assert "Thank you for your purchase!" in sample_receipt

    def test_receipt_has_separator_lines(self, sample_receipt):
        assert "=" * 30 in sample_receipt

    def test_receipt_single_item(self):
        cart = [(1, "Nachos", 1, 80.0)]
        receipt = generate_receipt_text(1, "2024-01-01 10:00:00", cart, 80.0, 20.0)
        assert "Nachos" in receipt
        assert "Total: 80.00" in receipt
        assert "Change: 20.00" in receipt

    def test_receipt_zero_change(self):
        cart = [(1, "Nachos", 1, 80.0)]
        receipt = generate_receipt_text(1, "2024-01-01 10:00:00", cart, 80.0, 0.0)
        assert "Change: 0.00" in receipt
        assert "Payment: 80.00" in receipt

    def test_receipt_multiple_quantities(self):
        cart = [(1, "Milk Tea", 5, 195.0)]
        receipt = generate_receipt_text(1, "2024-01-01 10:00:00", cart, 195.0, 5.0)
        assert "5 x 39.00 = 195.00" in receipt

    def test_receipt_returns_string(self, sample_cart):
        receipt = generate_receipt_text(1, "2024-01-01", sample_cart, 595.0, 5.0)
        assert isinstance(receipt, str)


class TestSaveReceipt:
    """Test receipt file saving"""

    def test_receipt_file_is_created(self, temp_receipts_dir):
        receipt_text = "Test receipt content"
        save_receipt(receipt_text, transaction_id=42)

        receipts_dir = temp_receipts_dir / "Receipts after Sale"
        files = list(receipts_dir.glob("receipt_42_*.txt"))
        assert len(files) == 1

    def test_receipt_file_contains_correct_content(self, temp_receipts_dir):
        receipt_text = "Test receipt content"
        save_receipt(receipt_text, transaction_id=99)

        receipts_dir = temp_receipts_dir / "Receipts after Sale"
        files = list(receipts_dir.glob("receipt_99_*.txt"))
        assert files[0].read_text() == receipt_text

    def test_receipts_directory_is_created(self, temp_receipts_dir):
        save_receipt("content", transaction_id=1)
        assert (temp_receipts_dir / "Receipts after Sale").is_dir()

    def test_multiple_receipts_saved_separately(self, temp_receipts_dir):
        save_receipt("Receipt A", transaction_id=1)
        save_receipt("Receipt B", transaction_id=2)

        receipts_dir = temp_receipts_dir / "Receipts after Sale"
        assert len(list(receipts_dir.glob("*.txt"))) == 2

    def test_receipt_filename_contains_transaction_id(self, temp_receipts_dir):
        save_receipt("content", transaction_id=777)

        receipts_dir = temp_receipts_dir / "Receipts after Sale"
        files = list(receipts_dir.glob("*.txt"))
        assert any("777" in f.name for f in files)


if __name__ == "__main__":
    pytest.main([__file__])
