#!/usr/bin/env python3
"""
Transform bank CSV exports into cleaned monthly transaction CSVs.

Looks for CSV files in data/transactions/raw/ (relative to this script's directory),
processes each one, and writes combined monthly output files to data/transactions/.
Processed input files are moved to data/transactions/raw/sanitized/.

The Source field is derived from the input filename prefix before the first '-'.
e.g. "navyfed-2025_11-1.csv" -> source "navyfed"

The month key is extracted from the filename as YYYY_MM pattern.
e.g. "amazon-2025_12.csv" -> month "2025_12"

All output dates are normalized to YYYY/MM/DD.
All formats are sorted ascending by date.
Output always uses "Date" as the date column name.

Supported formats are auto-detected by their column headers:

  navyfed (Navy Federal):
    Input columns:  Posting Date, Transaction Date, Amount, Credit Debit Indicator, Description, Category, ...
    Output columns: Date, Amount, Description, Category, Tag, Source, Credit Debit Indicator
    Sign logic:     Debit = positive, Credit = negative

  atlanticunion (Atlantic Union):
    Input columns:  Account Number, Post Date, Check, Description, Debit, Credit, Status, Balance
    Output columns: Date, Amount, Description, Category, Tag, Source, Debit, Credit
    Sign logic:     Debit column present = positive Amount, Credit column present = negative Amount

  chase (Chase credit card):
    Input columns:  Transaction Date, Post Date, Description, Category, Type, Amount, Memo
    Output columns: Date, Amount, Description, Category, Tag, Source, Type
    Sign logic:     Input Amount is already signed (sales negative, payments positive);
                    negate to get output convention (sales positive, payments negative)

  amazon (Amazon Chase credit card):
    Input columns:  Transaction Date, Post Date, Description, Category, Type, Amount, Memo
    Output columns: Date, Amount, Description, Category, Tag, Source, Amazon #
    Sign logic:     Same as chase (negate input Amount)
    Tag:            Set to Type value (Sale, Return, Payment)
    Description:    Simplified to "Amazon" unless Type is Payment, or description
                    contains "Prime", "Kindle", or "Audible" (case-insensitive)
    Amazon #:       Empty column added for manual order number entry

  penfed (PenFed credit card):
    Input columns:  Date, Description, Amount
    Output columns: Date, Amount, Description, Category, Tag, Source
    Sign logic:     Input Amount is already signed (purchases negative, payments positive);
                    negate to get output convention (purchases positive, payments negative)
"""

import csv
import os
import re
import shutil
import sys
from datetime import datetime


AMAZON_KEEP_KEYWORDS = ["prime", "kindle", "audible"]

DATE_FORMATS = ["%m/%d/%Y", "%Y-%m-%d", "%Y/%m/%d"]
OUTPUT_DATE_FORMAT = "%Y/%m/%d"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPT_DIR, "data", "transactions", "raw")
SANITIZED_DIR = os.path.join(RAW_DIR, "sanitized")
OUT_DIR = os.path.join(SCRIPT_DIR, "data", "transactions")

MONTH_PATTERN = re.compile(r"\d{4}_\d{2}")

BASE_COLS = ["Date", "Amount", "Description", "Category", "Tag", "Source"]
DROP_COLS = {"Debit", "Credit", "Type", "Credit Debit Indicator"}


def parse_date(date_str):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date format: '{date_str}'")


def fmt_date(date_str):
    return parse_date(date_str).strftime(OUTPUT_DATE_FORMAT)


def detect_format(fieldnames, source):
    if "Credit Debit Indicator" in fieldnames:
        return "navyfed"
    if "Debit" in fieldnames and "Credit" in fieldnames:
        return "atlanticunion"
    if "Type" in fieldnames and "Memo" in fieldnames:
        return "amazon" if source == "amazon" else "chase"
    if fieldnames == ["Date", "Description", "Amount"]:
        return "penfed"
    raise ValueError(f"Unrecognized CSV format. Headers: {fieldnames}")


def transform_navyfed(rows, source):
    out_rows = []
    for row in rows:
        amount = float(row["Amount"])
        if row["Credit Debit Indicator"] == "Credit":
            amount = -amount
        out_rows.append({
            "Date": fmt_date(row["Transaction Date"]),
            "Amount": amount,
            "Description": row["Description"],
            "Category": row["Category"],
            "Tag": "",
            "Source": source,
            "Credit Debit Indicator": row["Credit Debit Indicator"],
        })
    fieldnames = BASE_COLS + ["Credit Debit Indicator"]
    return out_rows, fieldnames


def transform_atlanticunion(rows, source):
    out_rows = []
    for row in rows:
        debit = row["Debit"].strip()
        credit = row["Credit"].strip()
        if debit:
            amount = float(debit)       # Debit = positive (money out)
        else:
            amount = -float(credit)     # Credit = negative (money in)
        out_rows.append({
            "Date": fmt_date(row["Post Date"]),
            "Amount": amount,
            "Description": row["Description"],
            "Category": "",
            "Tag": "",
            "Source": source,
            "Debit": debit,
            "Credit": credit,
        })
    fieldnames = BASE_COLS + ["Debit", "Credit"]
    return out_rows, fieldnames


def transform_chase(rows, source):
    out_rows = []
    for row in rows:
        amount = -float(row["Amount"])  # Input is negated: sales negative, payments positive
        out_rows.append({
            "Date": fmt_date(row["Transaction Date"]),
            "Amount": amount,
            "Description": row["Description"],
            "Category": row["Category"],
            "Tag": "",
            "Source": source,
            "Type": row["Type"],
        })
    fieldnames = BASE_COLS + ["Type"]
    return out_rows, fieldnames


def transform_amazon(rows, source):
    out_rows = []
    for row in rows:
        amount = -float(row["Amount"])
        tx_type = row["Type"]
        desc = row["Description"]
        # Keep description for payments and known Amazon services; simplify everything else
        is_payment = tx_type == "Payment"
        has_keyword = any(kw in desc.lower() for kw in AMAZON_KEEP_KEYWORDS)
        if not is_payment and not has_keyword:
            desc = "Amazon"
        out_rows.append({
            "Date": fmt_date(row["Transaction Date"]),
            "Amount": amount,
            "Description": desc,
            "Category": row["Category"],
            "Tag": tx_type,
            "Source": source,
            "Amazon #": "",
        })
    fieldnames = BASE_COLS + ["Amazon #"]
    return out_rows, fieldnames


def transform_penfed(rows, source):
    out_rows = []
    for row in rows:
        amount = -float(row["Amount"])  # Input is negated: purchases negative, payments positive
        out_rows.append({
            "Date": fmt_date(row["Date"]),
            "Amount": amount,
            "Description": row["Description"],
            "Category": "",
            "Tag": "",
            "Source": source,
        })
    fieldnames = BASE_COLS[:]
    return out_rows, fieldnames


def get_month_key(filename):
    m = MONTH_PATTERN.search(filename)
    if not m:
        raise ValueError(f"Cannot extract month key (YYYY_MM) from filename: {filename}")
    return m.group()


def process_file(input_path):
    """Process a single input CSV, returning (out_rows, fieldnames)."""
    basename = os.path.basename(input_path)
    source = basename.split("-")[0]

    with open(input_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fmt = detect_format(reader.fieldnames, source)

    if fmt == "navyfed":
        return transform_navyfed(rows, source)
    elif fmt == "atlanticunion":
        return transform_atlanticunion(rows, source)
    elif fmt == "chase":
        return transform_chase(rows, source)
    elif fmt == "amazon":
        return transform_amazon(rows, source)
    elif fmt == "penfed":
        return transform_penfed(rows, source)


def write_monthly(month_key, all_rows, extra_cols):
    """Write combined monthly CSV sorted by date."""
    output_path = os.path.join(OUT_DIR, f"{month_key}.csv")
    fieldnames = BASE_COLS + extra_cols
    all_rows.sort(key=lambda r: r["Date"])

    with open(output_path, newline="", mode="w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", restval="")
        writer.writeheader()
        for row in all_rows:
            amt = row["Amount"]
            row["Amount"] = f"{amt:.2f}" if isinstance(amt, float) else amt
            writer.writerow(row)

    print(f"Wrote {len(all_rows)} rows to {output_path}")


def main():
    os.makedirs(SANITIZED_DIR, exist_ok=True)

    raw_files = sorted(
        f for f in os.listdir(RAW_DIR)
        if f.endswith(".csv") and os.path.isfile(os.path.join(RAW_DIR, f))
    )

    if not raw_files:
        print(f"No CSV files found in {RAW_DIR}")
        return

    # month_key -> {"rows": [...], "extra_cols": [...]}
    monthly = {}
    processed = []

    for filename in raw_files:
        input_path = os.path.join(RAW_DIR, filename)
        try:
            month_key = get_month_key(filename)
            out_rows, fieldnames = process_file(input_path)
        except Exception as e:
            print(f"Error processing {filename}: {e}", file=sys.stderr)
            continue

        if month_key not in monthly:
            monthly[month_key] = {"rows": [], "extra_cols": []}

        monthly[month_key]["rows"].extend(out_rows)
        for col in fieldnames:
            if col not in BASE_COLS and col not in DROP_COLS and col not in monthly[month_key]["extra_cols"]:
                monthly[month_key]["extra_cols"].append(col)

        processed.append(input_path)
        print(f"Processed {filename} ({len(out_rows)} rows, month: {month_key})")

    for month_key in sorted(monthly.keys()):
        write_monthly(month_key, monthly[month_key]["rows"], monthly[month_key]["extra_cols"])

    for input_path in processed:
        dest = os.path.join(SANITIZED_DIR, os.path.basename(input_path))
        shutil.move(input_path, dest)
        print(f"Moved {os.path.basename(input_path)} -> sanitized/")


if __name__ == "__main__":
    main()
