#!/usr/bin/env python3
"""
Transform a bank CSV export into a cleaned transaction CSV.

Usage: python transactions_sanitizer.py input.csv output.csv

The Source field is derived from the input filename prefix before the first '-'.
e.g. "navyfed-2025_11-1.csv" -> source "navyfed"

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
import sys
from datetime import datetime


AMAZON_KEEP_KEYWORDS = ["prime", "kindle", "audible"]

DATE_FORMATS = ["%m/%d/%Y", "%Y-%m-%d", "%Y/%m/%d"]
OUTPUT_DATE_FORMAT = "%Y/%m/%d"


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
    out_rows.sort(key=lambda r: r["Date"])
    fieldnames = ["Date", "Amount", "Description", "Category", "Tag", "Source", "Credit Debit Indicator"]
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
    out_rows.sort(key=lambda r: r["Date"])
    fieldnames = ["Date", "Amount", "Description", "Category", "Tag", "Source", "Debit", "Credit"]
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
    out_rows.sort(key=lambda r: r["Date"])
    fieldnames = ["Date", "Amount", "Description", "Category", "Tag", "Source", "Type"]
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
    out_rows.sort(key=lambda r: r["Date"])
    fieldnames = ["Date", "Amount", "Description", "Category", "Tag", "Source", "Amazon #"]
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
    out_rows.sort(key=lambda r: r["Date"])
    fieldnames = ["Date", "Amount", "Description", "Category", "Tag", "Source"]
    return out_rows, fieldnames


def transform(input_path, output_path):
    basename = os.path.basename(input_path)
    source = basename.split("-")[0]

    with open(input_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fmt = detect_format(reader.fieldnames, source)

    if fmt == "navyfed":
        out_rows, fieldnames = transform_navyfed(rows, source)
    elif fmt == "atlanticunion":
        out_rows, fieldnames = transform_atlanticunion(rows, source)
    elif fmt == "chase":
        out_rows, fieldnames = transform_chase(rows, source)
    elif fmt == "amazon":
        out_rows, fieldnames = transform_amazon(rows, source)
    elif fmt == "penfed":
        out_rows, fieldnames = transform_penfed(rows, source)

    with open(output_path, newline="", mode="w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in out_rows:
            amt = row["Amount"]
            row["Amount"] = f"{amt:.2f}"
            writer.writerow(row)

    print(f"Wrote {len(out_rows)} rows to {output_path} (format: {fmt})")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python transactions_sanitizer.py input.csv output.csv")
        sys.exit(1)
    transform(sys.argv[1], sys.argv[2])