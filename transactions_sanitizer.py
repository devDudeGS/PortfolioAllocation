#!/usr/bin/env python3
"""
Transform a bank CSV export into a cleaned transaction CSV.

Usage: python transactions_sanitizer.py input.csv output.csv

The Source field is derived from the input filename prefix before the first '-' or '_'.
e.g. "navyfed-2025_11-1.csv" -> source "navyfed"

Key transformations:
- Select only: Transaction Date, Amount, Description, Category, Credit Debit Indicator
- Add Tag (empty) and Source (from filename) columns
- Make Credit amounts negative, Debit amounts positive
- Sort rows by Transaction Date ascending (uses Transaction Date, not Posting Date)
- Output column order: Transaction Date, Amount, Description, Category, Tag, Source, Credit Debit Indicator
"""

import csv
import os
import re
import sys
from datetime import datetime


def transform(input_path: str, output_path: str) -> None:
    # Derive source from filename prefix (everything before first '-' or '_')
    basename = os.path.basename(input_path)
    source = re.split(r"[-_]", basename)[0]

    with open(input_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

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
    with open(output_path, newline="", mode="w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in out_rows:
            amt = row["Amount"]
            row["Amount"] = f"{amt:.2f}"
            writer.writerow(row)

    print(f"Wrote {len(out_rows)} rows to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python transactions_sanitizer.py input.csv output.csv")
        sys.exit(1)
    transform(sys.argv[1], sys.argv[2]) 