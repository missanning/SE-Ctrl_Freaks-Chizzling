import csv
import os
from collections import namedtuple
from datetime import datetime
from tkinter import filedialog, messagebox

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

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


# ── PDF Export (matplotlib PdfPages) ─────────────────────────────────────────

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

    ORANGE, DARK, GRAY = "#FF6600", "#333333", "#888888"

    with PdfPages(path) as pdf:
        # ── Page 1: Summary ───────────────────────────────────────────────────
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis("off")
        fig.patch.set_facecolor("white")

        y = 0.97
        ax.text(0.5, y, "Chizzling POS — Sales Report", ha="center", va="top",
                fontsize=18, fontweight="bold", color=ORANGE, transform=ax.transAxes)
        y -= 0.04
        ax.plot([0.05, 0.95], [y, y], color=ORANGE, linewidth=2,
                transform=ax.transAxes)
        y -= 0.03
        ax.text(0.5, y, f"Period: {data.title}    |    Generated: {generated}",
                ha="center", va="top", fontsize=9, color=GRAY, transform=ax.transAxes)

        y -= 0.06
        ax.text(0.05, y, "Summary", fontsize=13, fontweight="bold",
                color=DARK, transform=ax.transAxes)
        y -= 0.04
        for label, value in [
            ("Total Transactions", str(data.summary[0])),
            ("Total Sales",        f"P{data.summary[1]:.2f}"),
            ("Avg Transaction",    f"P{avg:.2f}"),
        ]:
            ax.text(0.07, y, label, fontsize=10, color=DARK, transform=ax.transAxes)
            ax.text(0.45, y, value, fontsize=10, fontweight="bold",
                    color=ORANGE, transform=ax.transAxes)
            y -= 0.035

        y -= 0.04
        ax.text(0.05, y, "Top Products", fontsize=13, fontweight="bold",
                color=DARK, transform=ax.transAxes)
        y -= 0.04

        col_x = [0.07, 0.55, 0.75]
        for header, x in zip(["Product", "Qty Sold", "Revenue"], col_x):
            ax.text(x, y, header, fontsize=10, fontweight="bold",
                    color="white", transform=ax.transAxes,
                    bbox=dict(facecolor=ORANGE, edgecolor="none", pad=3))
        y -= 0.035

        for i, (name, qty, rev) in enumerate(data.products):
            bg = "#FFF3E0" if i % 2 == 0 else "white"
            ax.axhspan(y - 0.005, y + 0.025, xmin=0.05, xmax=0.95,
                       color=bg, transform=ax.transAxes)
            ax.text(col_x[0], y, name[:45], fontsize=9, color=DARK, transform=ax.transAxes)
            ax.text(col_x[1], y, str(int(qty)), fontsize=9, color=DARK, transform=ax.transAxes)
            ax.text(col_x[2], y, f"P{rev:.2f}", fontsize=9, color=DARK, transform=ax.transAxes)
            y -= 0.03
            if y < 0.05:
                pdf.savefig(fig, bbox_inches="tight")
                plt.close(fig)
                fig, ax = plt.subplots(figsize=(8.5, 11))
                ax.axis("off")
                fig.patch.set_facecolor("white")
                y = 0.95

        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        # ── Page 2+: Transactions ─────────────────────────────────────────────
        fig, ax = plt.subplots(figsize=(8.5, 11))
        ax.axis("off")
        fig.patch.set_facecolor("white")

        y = 0.97
        ax.text(0.05, y, "Transactions", fontsize=13, fontweight="bold",
                color=DARK, transform=ax.transAxes)
        y -= 0.04

        t_cols = [0.05, 0.15, 0.45, 0.62, 0.78]
        for header, x in zip(["ID", "Date", "Total", "Payment", "Change"], t_cols):
            ax.text(x, y, header, fontsize=10, fontweight="bold",
                    color="white", transform=ax.transAxes,
                    bbox=dict(facecolor=ORANGE, edgecolor="none", pad=3))
        y -= 0.035

        for i, (tid, date, total, payment, change) in enumerate(data.transactions):
            bg = "#FFF3E0" if i % 2 == 0 else "white"
            ax.axhspan(y - 0.005, y + 0.025, xmin=0.03, xmax=0.97,
                       color=bg, transform=ax.transAxes)
            for val, x in zip([str(tid), date, f"P{total:.2f}",
                                f"P{payment:.2f}", f"P{change:.2f}"], t_cols):
                ax.text(x, y, val, fontsize=8, color=DARK, transform=ax.transAxes)
            y -= 0.028
            if y < 0.05:
                pdf.savefig(fig, bbox_inches="tight")
                plt.close(fig)
                fig, ax = plt.subplots(figsize=(8.5, 11))
                ax.axis("off")
                fig.patch.set_facecolor("white")
                y = 0.95

        ax.text(0.5, 0.02, "Chizzling POS — Confidential Sales Report",
                ha="center", fontsize=8, color=GRAY, transform=ax.transAxes)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    os.startfile(path)
    messagebox.showinfo("Export Successful", f"PDF report saved to:\n{path}")
