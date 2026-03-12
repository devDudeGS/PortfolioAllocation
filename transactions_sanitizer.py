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
    Sign logic:     Debit = positive, Credit = negative

  atlanticunion (Atlantic Union):
    Input columns:  Account Number, Post Date, Check, Description, Debit, Credit, Status, Balance
    Sign logic:     Debit column present = positive Amount, Credit column present = negative Amount

  chase (Chase credit card):
    Input columns:  Transaction Date, Post Date, Description, Category, Type, Amount, Memo
    Sign logic:     Input Amount is already signed (sales negative, payments positive);
                    negate to get output convention (sales positive, payments negative)

  amazon (Amazon Chase credit card):
    Input columns:  Transaction Date, Post Date, Description, Category, Type, Amount, Memo
    Sign logic:     Same as chase (negate input Amount)
    Tag:            Set to Type value (Sale, Return, Payment)
    Description:    Simplified to "Amazon" unless Type is Payment, or description
                    contains "Prime", "Kindle", or "Audible" (case-insensitive)
    Amazon #:       Empty column added for manual order number entry

  penfed (PenFed credit card):
    Input columns:  Date, Description, Amount
    Sign logic:     Input Amount is already signed (purchases negative, payments positive);
                    negate to get output convention (purchases positive, payments negative)

Output columns for all formats: Date, Amount, Description, Category, Tag, Source
  (plus Amazon # for amazon format)
"""

import csv
import os
import re
import shutil
import sys
import json
from collections import defaultdict
from datetime import datetime


AMAZON_KEEP_KEYWORDS = ["prime", "kindle", "audible"]

DATE_FORMATS = ["%m/%d/%Y", "%Y-%m-%d", "%Y/%m/%d"]
OUTPUT_DATE_FORMAT = "%Y/%m/%d"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPT_DIR, "data", "transactions", "raw")
SANITIZED_DIR = os.path.join(RAW_DIR, "sanitized")
OUT_DIR = os.path.join(SCRIPT_DIR, "data", "transactions")
AMAZON_DIR = os.path.join(SCRIPT_DIR, "data", "transactions", "amazon")
RULES_PATH = os.path.join(SCRIPT_DIR, "data", "transactions", "rules.json")
AMAZON_MATCH_TOLERANCE = 0.01
AMAZON_MATCH_DAY_WINDOW = 7

MONTH_PATTERN = re.compile(r"(?<!\d)\d{4}_(?:0[1-9]|1[0-2])(?!\d)")

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
        elif credit:
            amount = -float(credit)     # Credit = negative (money in)
        else:
            continue                    # Skip rows with no amount
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
    return out_rows, BASE_COLS


def load_amazon_lookups():
    """Build a list of {order_id, date, amount, desc} from the amazon lookup files."""
    lookups = []

    # Order_History: group rows by (order_id, ship_date, subtotal) -> unique shipment charge
    order_path = os.path.join(AMAZON_DIR, "Order_History.csv")
    if os.path.isfile(order_path):
        shipments = defaultdict(list)
        with open(order_path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                if row.get("Ship Date", "Not Applicable") == "Not Applicable":
                    continue
                try:
                    float(row["Shipment Item Subtotal"])
                except (ValueError, KeyError):
                    continue
                key = (row["Order ID"], row["Ship Date"][:10], row["Shipment Item Subtotal"])
                shipments[key].append(row)
        for (order_id, ship_date_str, subtotal), items in shipments.items():
            try:
                date = datetime.strptime(ship_date_str, "%Y-%m-%d")
                amount = round(float(subtotal) + float(items[0].get("Shipment Item Subtotal Tax") or 0), 2)
            except (ValueError, KeyError):
                continue
            names = [i["Product Name"].strip()[:60] for i in items if i.get("Product Name")]
            lookups.append({"order_id": order_id, "date": date, "amount": amount,
                            "desc": " + ".join(names) or None})

    # Digital_Content_Orders: group Price Amount rows by (order_id, order_date), add Tax rows
    digital_path = os.path.join(AMAZON_DIR, "Digital_Content_Orders.csv")
    if os.path.isfile(digital_path):
        price_rows = defaultdict(list)
        tax_totals = defaultdict(float)
        with open(digital_path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                key = (row["Order ID"], row["Order Date"][:10])
                try:
                    amt = float(row["Transaction Amount"])
                except (ValueError, KeyError):
                    continue
                if row.get("Component Type") == "Tax":
                    tax_totals[key] += amt
                else:
                    price_rows[key].append(row)
        for (order_id, date_str), items in price_rows.items():
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
                amount = round(sum(float(i["Transaction Amount"]) for i in items)
                               + tax_totals.get((order_id, date_str), 0.0), 2)
            except (ValueError, KeyError):
                continue
            names = list(dict.fromkeys(i["Product Name"].strip()[:60] for i in items if i.get("Product Name")))
            lookups.append({"order_id": order_id, "date": date, "amount": amount,
                            "desc": " + ".join(names) or None})

    # Refund_Details: deduplicate by (order_id, date, amount); no product name available
    refund_path = os.path.join(AMAZON_DIR, "Refund_Details.csv")
    if os.path.isfile(refund_path):
        seen = set()
        with open(refund_path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                try:
                    date = datetime.strptime(row["Refund Date"][:10], "%Y-%m-%d")
                    amount = round(float(row["Refund Amount"]), 2)
                except (ValueError, KeyError):
                    continue
                key = (row["Order ID"], row["Refund Date"][:10], amount)
                if key in seen:
                    continue
                seen.add(key)
                lookups.append({"order_id": row["Order ID"], "date": date,
                                "amount": amount, "desc": None})

    return lookups


def enrich_amazon_rows(all_rows):
    """Fill Amazon # (and Description if available) for matched amazon Sale/Return rows."""
    if not os.path.isdir(AMAZON_DIR):
        return
    lookups = load_amazon_lookups()
    if not lookups:
        return
    claimed = set()
    for row in all_rows:
        if row.get("Source") != "amazon" or row.get("Tag") not in ("Sale", "Return"):
            continue
        if row.get("Amazon #", "").strip():
            continue
        try:
            txn_date = parse_date(row["Date"])
            txn_amt = abs(float(row["Amount"]))
        except (ValueError, KeyError):
            continue
        candidates = [
            (abs((lkp["date"] - txn_date).days), idx, lkp)
            for idx, lkp in enumerate(lookups)
            if idx not in claimed and abs(lkp["amount"] - txn_amt) <= AMAZON_MATCH_TOLERANCE
            and abs((lkp["date"] - txn_date).days) <= AMAZON_MATCH_DAY_WINDOW
        ]
        if not candidates:
            continue
        _, best_idx, best = min(candidates)
        claimed.add(best_idx)
        row["Amazon #"] = best["order_id"]
        if best["desc"] is not None:
            row["Description"] = best["desc"]


def load_rules():
    if not os.path.isfile(RULES_PATH):
        return []
    with open(RULES_PATH, encoding="utf-8") as f:
        return json.load(f)["rules"]


def apply_rules(row, rules):
    for rule in rules:
        if not row["Description"].lower().startswith(rule["description"].lower()):
            continue
        if "amount" in rule and abs(float(row["Amount"]) - rule["amount"]) > 0.01:
            continue
        if "source" in rule and row["Source"] != rule["source"]:
            continue
        row["Category"] = rule["category"]
        row["Tag"] = rule["tag"]
        return


def get_month_key(filename):
    m = MONTH_PATTERN.search(filename)
    if not m:
        raise ValueError(f"Cannot extract month key (YYYY_MM) from filename: {filename}")
    return m.group()


def process_file(input_path, rules):
    """Process a single input CSV, returning (out_rows, fieldnames)."""
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
    else:
        raise ValueError(f"No transform function for format: {fmt}")

    for row in out_rows:
        apply_rules(row, rules)

    return out_rows, fieldnames


def write_monthly(month_key, all_rows, extra_cols):
    """Write combined monthly CSV sorted by date, merging with any existing output."""
    output_path = os.path.join(OUT_DIR, f"{month_key}.csv")

    # Merge with existing output so re-runs don't silently drop previously processed data
    if os.path.isfile(output_path):
        with open(output_path, newline="", encoding="utf-8") as f:
            existing = list(csv.DictReader(f))
        new_keys = {(r["Date"], r["Amount"] if isinstance(r["Amount"], str) else f"{r['Amount']:.2f}", r["Description"], r["Source"]) for r in all_rows}
        for row in existing:
            key = (row["Date"], row["Amount"], row["Description"], row["Source"])
            if key not in new_keys:
                all_rows.append(row)
                new_keys.add(key)
        for col in existing[0].keys() if existing else []:
            if col not in BASE_COLS and col not in DROP_COLS and col not in extra_cols:
                extra_cols.append(col)

    fieldnames = BASE_COLS + extra_cols
    enrich_amazon_rows(all_rows)
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
    os.makedirs(OUT_DIR, exist_ok=True)

    rules = load_rules()

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
            out_rows, fieldnames = process_file(input_path, rules)
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
