#!/usr/bin/env python3
"""
Transform a bank CSV export into a cleaned transaction CSV.

Usage: python transactions_sanitizer.py input.csv output.csv

The Source field is derived from the input filename prefix before the first '-' or '_'.
e.g. "navyfed-2025_11-1.csv" -> source "navyfed"

Supported formats are auto-detected by their column headers:

  navyfed (Navy Federal):
    Input columns:  Posting Date, Transaction Date, Amount, Credit Debit Indicator, Description, Category, ...
    Output columns: Transaction Date, Amount, Description, Category, Tag, Source, Credit Debit Indicator
    Sign logic:     Debit = positive, Credit = negative

  atlanticunion (Atlantic Union):
    Input columns:  Account Number, Post Date, Check, Description, Debit, Credit, Status, Balance
    Output columns: Post Date, Amount, Description, Category, Tag, Source, Debit, Credit
    Sign logic:     Debit column present = positive Amount, Credit column present = negative Amount

Both formats are sorted ascending by date.
"""

import csv
import os
import re
import sys
from datetime import datetime


def detect_format(fieldnames) -> str:
    if "Credit Debit Indicator" in fieldnames:
        return "navyfed"
    if "Debit" in fieldnames and "Credit" in fieldnames:
        return "atlanticunion"
    raise ValueError(f"Unrecognized CSV format. Headers: {fieldnames}")


def transform_navyfed(rows, source):
    out_rows = []
    for row in rows:
        amount = float(row["Amount"])
        if row["Credit Debit Indicator"] == "Credit":
            amount = -amount
        out_rows.append({
            "Transaction Date": row["Transaction Date"],
            "Amount": amount,
            "Description": row["Description"],
            "Category": row["Category"],
            "Tag": "",
            "Source": source,
            "Credit Debit Indicator": row["Credit Debit Indicator"],
        })
    out_rows.sort(key=lambda r: datetime.strptime(r["Transaction Date"], "%m/%d/%Y"))
    fieldnames = ["Transaction Date", "Amount", "Description", "Category", "Tag", "Source", "Credit Debit Indicator"]
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
            "Post Date": row["Post Date"],
            "Amount": amount,
            "Description": row["Description"],
            "Category": "",
            "Tag": "",
            "Source": source,
            "Debit": debit,
            "Credit": credit,
        })
    out_rows.sort(key=lambda r: datetime.strptime(r["Post Date"], "%m/%d/%Y"))
    fieldnames = ["Post Date", "Amount", "Description", "Category", "Tag", "Source", "Debit", "Credit"]
    return out_rows, fieldnames


def transform(input_path: str, output_path: str) -> None:
    basename = os.path.basename(input_path)
    source = re.split(r"[-_]", basename)[0]

    with open(input_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fmt = detect_format(reader.fieldnames)

    if fmt == "navyfed":
        out_rows, fieldnames = transform_navyfed(rows, source)
    elif fmt == "atlanticunion":
        out_rows, fieldnames = transform_atlanticunion(rows, source)

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