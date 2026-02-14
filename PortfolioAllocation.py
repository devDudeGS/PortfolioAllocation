import csv
import numpy as np
from numpy.typing import NDArray

DATA_FILE = "data/RetirementData.csv"
ASSET_CLASS_COUNT = 7


def balance_iras() -> None:
    """Orchestrates IRA allocation for two account holders and prints results."""
    all_data_np = get_data()
    starting_portfolio, goal_proportions, cash_ira_self, cash_ira_spouse, prices_ira_self, prices_ira_spouse = get_params(
        all_data_np, ASSET_CLASS_COUNT)

    ideal_cash_allocation = get_ideal_cash_allocation(
        starting_portfolio, goal_proportions)

    # Allocate G's IRA first against the starting portfolio
    cash_allocation_ira_self = get_cash_allocation(
        starting_portfolio, goal_proportions, cash_ira_self, prices_ira_self)
    shares_allocation_ira_self = get_shares_allocation(
        starting_portfolio, goal_proportions, cash_allocation_ira_self, prices_ira_self)

    # Update portfolio to reflect G's purchases before allocating J's IRA
    updated_portfolio = starting_portfolio + shares_allocation_ira_self * prices_ira_self

    # Allocate J's IRA against the updated portfolio so gaps aren't double-filled
    cash_allocation_ira_spouse = get_cash_allocation(
        updated_portfolio, goal_proportions, cash_ira_spouse, prices_ira_spouse)
    shares_allocation_ira_spouse = get_shares_allocation(
        updated_portfolio, goal_proportions, cash_allocation_ira_spouse, prices_ira_spouse)

    print_results(shares_allocation_ira_self, shares_allocation_ira_spouse, prices_ira_self, prices_ira_spouse,
                  cash_ira_self, cash_ira_spouse, starting_portfolio, goal_proportions, ideal_cash_allocation)


def get_data() -> NDArray:
    """Reads the retirement CSV and returns its contents as a numpy array."""
    with open(DATA_FILE, "r") as file:
        reader = csv.reader(file)
        data = list(reader)

    return np.array(data)


def get_params(
    all_data_np: NDArray, asset_classes_total: int
) -> tuple[NDArray, NDArray, float, float, NDArray, NDArray]:
    """Extracts portfolio parameters from raw CSV data.

    Returns starting portfolio values, goal proportions, available cash for
    each IRA, and current share prices for each IRA.
    """
    final_row_index = asset_classes_total + 1
    goal_proportions = all_data_np[1:final_row_index, 1].astype(float)

    starting_portfolio = np.round(
        all_data_np[1:final_row_index, 2:6].astype(float).sum(axis=1), 2
    )

    cash_ira_self = float(all_data_np[final_row_index][2])
    cash_ira_spouse = float(all_data_np[final_row_index][3])

    prices_ira_self = all_data_np[1:final_row_index, 6].astype(float)
    prices_ira_spouse = all_data_np[1:final_row_index, 7].astype(float)

    return starting_portfolio, goal_proportions, cash_ira_self, cash_ira_spouse, prices_ira_self, prices_ira_spouse


def get_ideal_cash_allocation(portfolio: NDArray, allocation: NDArray) -> float:
    """Returns the cash needed to bring the portfolio exactly in line with target allocation.

    Finds the most over-allocated asset class and calculates how much total cash
    would be needed to make every other class proportionally match it.
    """

    ideal_allocation_portfolio = allocation * np.sum(portfolio)
    portfolio_diff = portfolio - ideal_allocation_portfolio
    most_over_index = np.argmax(portfolio_diff)
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
    shares_total = np.zeros_like(prices)
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
    shares_ira_self: NDArray,
    shares_ira_spouse: NDArray,
    prices_ira_self: NDArray,
    prices_ira_spouse: NDArray,
    cash_ira_self: float,
    cash_ira_spouse: float,
    starting_portfolio: NDArray,
    goal_proportions: NDArray,
    ideal_cash_allocation: float,
) -> None:
    """Prints a summary of the allocation results for both IRAs."""
    increase_ira_self = shares_ira_self * prices_ira_self
    increase_ira_spouse = shares_ira_spouse * prices_ira_spouse

    print()
    print("Goal proportions:       ", goal_proportions)
    print("Starting proportions:   ", get_proportions(starting_portfolio))
    print("Ending proportions:     ", get_proportions(
        starting_portfolio + increase_ira_self + increase_ira_spouse))
    print()
    print("G's IRA cash start:      ", round(cash_ira_self, 2))
    print("Shares of G's IRA:       ", shares_ira_self)
    print("G's IRA cash remaining:  ", round(
        cash_ira_self - np.sum(increase_ira_self), 2))
    print()
    print("J's IRA cash start:    ", round(cash_ira_spouse, 2))
    print("Shares of J's IRA:     ", shares_ira_spouse)
    print("J's IRA cash remaining:", round(
        cash_ira_spouse - np.sum(increase_ira_spouse), 2))
    print()
    print("Ideal cash addition:    ", ideal_cash_allocation)
    print()


def get_proportions(arr: NDArray) -> NDArray:
    """Returns each element's share of the array total, rounded to 3 decimal places."""
    return np.round(arr / np.sum(arr), 3)


if __name__ == "__main__":
    balance_iras()
