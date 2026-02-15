from __future__ import annotations

import csv
from dataclasses import dataclass, field
import numpy as np
from numpy.typing import NDArray

# CSV format requirements:
#   Column 1:   "security_type" — asset class labels (e.g. total_stock, gold)
#   Column 2:   "ideal_portfolio" — target allocation proportions (must sum to 1.0, none may be 0)
#   Columns 3+: Account holding values, IRA prices, and IRA fund tickers, with these naming conventions:
#       - IRA holdings:   "ira_<person>"              (e.g. ira_g, ira_j)
#       - 401k holdings:  "401k_<person>"             (e.g. 401k_g, 401k_j)
#       - Other holdings: any name without an "ira_prices_" or "ira_fund_" prefix
#       - IRA prices:     "ira_prices_<person>"       (e.g. ira_prices_g) — one per IRA,
#                          must match an ira_<person> column. Use -1 where a fund is unavailable.
#       - IRA fund names: "ira_fund_<person>"         (e.g. ira_fund_g) — optional, one per IRA,
#                          ticker symbols for each asset class in that account. Use "N/A" where unavailable.
#   Last row:   security_type must be "cash", with available cash in IRA holding columns
#               and 0 elsewhere.
#   The <person> suffix generates labels (e.g. ira_g -> "G's IRA").
#   IRAs are allocated in the order their price columns appear in the header.

DATA_FILE = "data/RetirementData.csv"


@dataclass
class CSVLayout:
    """Column indices and per-IRA metadata parsed from the CSV header."""

    holding_col_indices: list[int] = field(default_factory=list)
    ira_configs: list[tuple[str, int, int, int | None]] = field(default_factory=list)  # (label, holding_col, price_col, fund_col)


@dataclass
class IRAAllocation:
    """Per-account data grouping label, available cash, share counts, prices, and fund tickers."""

    label:  str
    cash:   float
    shares: NDArray
    prices: NDArray
    funds:  list[str]


def balance_iras() -> None:
    """Orchestrates IRA allocation for all account holders and prints results."""
    all_data_np = get_data()
    starting_portfolio, goal_proportions, security_types, ira_configs = get_params(all_data_np)

    ideal_cash_allocation = get_ideal_cash_allocation(
        starting_portfolio, goal_proportions)

    current_portfolio = starting_portfolio.copy()
    iras: list[IRAAllocation] = []

    for label, cash, prices, funds in ira_configs:
        cash_alloc = get_cash_allocation(
            current_portfolio, goal_proportions, cash, prices)
        shares_alloc = get_shares_allocation(
            current_portfolio, goal_proportions, cash_alloc, prices)
        current_portfolio = current_portfolio + shares_alloc * prices
        iras.append(IRAAllocation(label=label, cash=cash, shares=shares_alloc, prices=prices, funds=funds))

    print_results(iras, starting_portfolio, goal_proportions, security_types, ideal_cash_allocation)


def get_data() -> NDArray:
    """Reads the retirement CSV and returns its contents as a numpy array."""
    with open(DATA_FILE, "r") as file:
        reader = csv.reader(file)
        data = list(reader)

    return np.array(data)


def _parse_csv_layout(headers: list[str]) -> CSVLayout:
    """Identifies holding columns, IRA columns, price columns, and fund columns from CSV headers."""
    price_persons: dict[str, int] = {}
    fund_persons: dict[str, int] = {}
    ira_holding_persons: dict[str, int] = {}
    holding_col_indices: list[int] = []

    for i, header in enumerate(headers):
        if i < 2:
            continue
        if header.startswith("ira_prices_"):
            price_persons[header[len("ira_prices_"):]] = i
        elif header.startswith("ira_fund_"):
            fund_persons[header[len("ira_fund_"):]] = i
        else:
            holding_col_indices.append(i)
            if header.startswith("ira_"):
                ira_holding_persons[header[len("ira_"):]] = i

    ira_configs: list[tuple[str, int, int, int | None]] = []
    for person, price_col in price_persons.items():
        if person not in ira_holding_persons:
            raise ValueError(
                f"Price column 'ira_prices_{person}' has no matching "
                f"'ira_{person}' holding column in {DATA_FILE}."
            )
        label = f"{person.capitalize()}'s IRA"
        fund_col = fund_persons.get(person)
        ira_configs.append((label, ira_holding_persons[person], price_col, fund_col))

    if not ira_configs:
        raise ValueError(f"No IRA price columns (ira_prices_*) found in {DATA_FILE}.")

    return CSVLayout(holding_col_indices=holding_col_indices, ira_configs=ira_configs)


def _find_cash_row_index(all_data_np: NDArray) -> int:
    """Returns the row index of the cash row (security_type == 'cash')."""
    for i in range(1, len(all_data_np)):
        if all_data_np[i, 0] == "cash":
            return i
    raise ValueError(f"No row with security_type 'cash' found in {DATA_FILE}.")


def _parse_goal_proportions(all_data_np: NDArray, asset_rows: slice) -> NDArray:
    """Extracts target allocation proportions from the CSV data."""
    return all_data_np[asset_rows, 1].astype(float)


def _build_starting_portfolio(
    all_data_np: NDArray, asset_rows: slice, holding_col_indices: list[int]
) -> NDArray:
    """Sums current holdings across all accounts to form the starting portfolio."""
    return np.round(
        all_data_np[asset_rows][:, holding_col_indices].astype(float).sum(axis=1), 2
    )


def get_params(
    all_data_np: NDArray,
) -> tuple[NDArray, NDArray, list[str], list[tuple[str, float, NDArray, list[str]]]]:
    """Extracts portfolio parameters from raw CSV data.

    Returns starting portfolio values, goal proportions, asset class names, and a list of
    (label, cash, prices, funds) tuples — one per IRA found in the CSV header.
    """
    headers = all_data_np[0].tolist()
    layout = _parse_csv_layout(headers)
    cash_row_index = _find_cash_row_index(all_data_np)
    asset_rows = slice(1, cash_row_index)

    goal_proportions = _parse_goal_proportions(all_data_np, asset_rows)

    if np.any(goal_proportions == 0):
        zero_classes = np.where(goal_proportions == 0)[0]
        raise ValueError(
            f"Goal proportions cannot be 0 (found at index {zero_classes.tolist()}). "
            f"Remove zero-allocation classes from {DATA_FILE} or set a non-zero target."
        )

    proportion_sum = np.round(np.sum(goal_proportions), 10)
    if proportion_sum != 1.0:
        raise ValueError(
            f"Goal proportions must sum to 1.0, but sum to {proportion_sum}. "
            f"Check the ideal_portfolio column in {DATA_FILE}."
        )

    starting_portfolio = _build_starting_portfolio(
        all_data_np, asset_rows, layout.holding_col_indices)

    security_types: list[str] = all_data_np[asset_rows, 0].tolist()

    ira_configs: list[tuple[str, float, NDArray, list[str]]] = []
    for label, holding_col, price_col, fund_col in layout.ira_configs:
        cash = float(all_data_np[cash_row_index, holding_col])
        prices = all_data_np[asset_rows, price_col].astype(float)
        funds = all_data_np[asset_rows, fund_col].tolist() if fund_col is not None else [""] * len(security_types)
        ira_configs.append((label, cash, prices, funds))

    return starting_portfolio, goal_proportions, security_types, ira_configs


def get_ideal_cash_allocation(portfolio: NDArray, allocation: NDArray) -> float:
    """Returns the cash needed to bring the portfolio exactly in line with target allocation.

    Finds the most over-allocated asset class and calculates how much total cash
    would be needed to make every other class proportionally match it.
    """

    most_over_index = np.argmax(portfolio / allocation)
    ideal_portfolio_total = portfolio[most_over_index] / allocation[most_over_index]

    ideal_cash_allocation = np.round(
        ideal_portfolio_total - np.sum(portfolio), 2)

    return ideal_cash_allocation


def get_cash_allocation(
    portfolio: NDArray, allocation: NDArray, cash: float, prices: NDArray
) -> NDArray:
    """Distributes available cash across under-allocated asset classes.

    Proportionally fills gaps relative to target allocation, skipping asset
    classes with no available price (price <= 0).
    """
    # amount of cash to reach ideal
    ideal_totals = allocation * (np.sum(portfolio) + cash)
    diff_totals = portfolio - ideal_totals

    # Funding gaps: how much each asset class is under-allocated (zero if over-allocated or unavailable)
    revised_totals = np.where(prices > 0, np.maximum(-diff_totals, 0), 0)

    # determine biggest gaps
    proportion_totals = revised_totals / np.sum(revised_totals)

    return np.round(proportion_totals * cash, 2)


def get_shares_allocation(
    starting_portfolio: NDArray,
    ideal_allocation: NDArray,
    cash_allocation: NDArray,
    prices: NDArray,
) -> NDArray:
    """Converts a cash allocation into whole share counts.

    First pass: iteratively buys shares in proportion to funding gaps until
    no full shares can be purchased. Greedy fallback: spends remaining cash
    share-by-share, prioritising the cheapest under-allocated asset.
    """
    shares_total = np.zeros(len(prices))
    current_portfolio = starting_portfolio.copy()

    while True:
        shares, remainder = np.divmod(cash_allocation, prices)  # type: ignore
        if np.sum(shares) == 0:
            break
        else:
            shares_total += shares
            current_portfolio = current_portfolio + shares * prices
            cash_allocation = get_cash_allocation(
                current_portfolio, ideal_allocation, np.sum(remainder), prices)

    # Greedy fallback: proportional allocation stalled; spend remaining cash share-by-share
    remaining_cash = np.sum(cash_allocation)
    available = prices > 0  # excludes -1 (unavailable funds)

    while remaining_cash > 0:
        ideal_totals = ideal_allocation * (np.sum(current_portfolio) + remaining_cash)
        under_allocated = (current_portfolio - ideal_totals) < 0

        # Prefer cheapest under-allocated affordable share; fall back to any affordable share
        candidates = under_allocated & available & (prices <= remaining_cash)
        if not np.any(candidates):
            candidates = available & (prices <= remaining_cash)
        if not np.any(candidates):
            break

        idx = np.argmin(np.where(candidates, prices, np.inf))
        shares_total[idx] += 1
        current_portfolio[idx] += prices[idx]
        remaining_cash -= prices[idx]

    return shares_total


def print_results(
    iras: list[IRAAllocation],
    starting_portfolio: NDArray,
    goal_proportions: NDArray,
    security_types: list[str],
    ideal_cash_allocation: float,
) -> None:
    """Prints a summary of the allocation results for all IRAs."""
    total_increase = np.zeros(len(starting_portfolio))
    for ira in iras:
        total_increase += ira.shares * ira.prices

    goal_pct   = goal_proportions * 100
    start_pct  = get_proportions(starting_portfolio) * 100
    end_pct    = get_proportions(starting_portfolio + total_increase) * 100
    name_width = max(len(n) for n in security_types)

    print()
    print(f"  {'Asset class':<{name_width}}    Goal   Start     End")
    print(f"  {'-' * name_width}  ------  ------  ------")
    for name, g, s, e in zip(security_types, goal_pct, start_pct, end_pct):
        print(f"  {name:<{name_width}}  {g:5.1f}%  {s:5.1f}%  {e:5.1f}%")

    for ira in iras:
        increase = ira.shares * ira.prices
        print()
        print(f"{ira.label} — cash: ${ira.cash:,.2f}")
        fund_width = max((len(f) for f in ira.funds if f and f != "N/A"), default=4)
        for fund, name, shares in zip(ira.funds, security_types, ira.shares):
            if shares > 0:
                share_label = "share" if shares == 1 else "shares"
                fund_str = f"{fund:<{fund_width}}" if fund and fund != "N/A" else " " * fund_width
                print(f"  {fund_str}  ({name:<{name_width}})  {int(shares):>4} {share_label}")
        print(f"  Cash remaining: ${ira.cash - np.sum(increase):,.2f}")

    print()
    print(f"Ideal cash addition: ${ideal_cash_allocation:,.2f}")
    print()


def get_proportions(arr: NDArray) -> NDArray:
    """Returns each element's share of the array total, rounded to 3 decimal places."""
    return np.round(arr / np.sum(arr), 3)


if __name__ == "__main__":
    balance_iras()
