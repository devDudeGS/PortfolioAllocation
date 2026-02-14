import csv
import numpy as np


def balance_iras():
    asset_classes_total = 7

    all_data_np = get_data()
    starting_portfolio, goal_proportions, cash_ira_self, cash_ira_spouse, prices_ira_self, prices_ira_spouse = get_params(
        all_data_np, asset_classes_total)

    ideal_cash_allocation = get_ideal_cash_allocation(
        starting_portfolio, goal_proportions)

    # Allocate G's IRA first against the starting portfolio
    cash_allocation_ira_self = get_cash_allocation(
        starting_portfolio, goal_proportions, cash_ira_self, prices_ira_self, asset_classes_total)
    shares_allocation_ira_self = get_shares_allocation(
        starting_portfolio, goal_proportions, cash_allocation_ira_self, prices_ira_self, asset_classes_total)

    # Update portfolio to reflect G's purchases before allocating J's IRA
    updated_portfolio = starting_portfolio + shares_allocation_ira_self * prices_ira_self

    # Allocate J's IRA against the updated portfolio so gaps aren't double-filled
    cash_allocation_ira_spouse = get_cash_allocation(
        updated_portfolio, goal_proportions, cash_ira_spouse, prices_ira_spouse, asset_classes_total)
    shares_allocation_ira_spouse = get_shares_allocation(
        updated_portfolio, goal_proportions, cash_allocation_ira_spouse, prices_ira_spouse, asset_classes_total)

    print_results(shares_allocation_ira_self, shares_allocation_ira_spouse, prices_ira_self, prices_ira_spouse,
                  cash_ira_self, cash_ira_spouse, starting_portfolio, goal_proportions, ideal_cash_allocation)


def get_data():
    with open("data/RetirementData.csv", "r") as file:
        reader = csv.reader(file)
        data = list(reader)

    return np.array(data)


def get_params(all_data_np, asset_classes_total):
    final_row_index = asset_classes_total + 1
    goal_proportions = all_data_np[1:final_row_index, 1].astype(np.float)

    starting_portfolio = np.zeros(asset_classes_total)
    for i in range(0, asset_classes_total):
        asset_class = all_data_np[i + 1, 2:6].astype(np.float)
        starting_portfolio[i] = np.round(np.sum(asset_class), 2)

    cash_ira_self = float(all_data_np[final_row_index][2])
    cash_ira_spouse = float(all_data_np[final_row_index][3])

    prices_ira_self = all_data_np[1:final_row_index, 6].astype(np.float)
    prices_ira_spouse = all_data_np[1:final_row_index, 7].astype(np.float)

    return starting_portfolio, goal_proportions, cash_ira_self, cash_ira_spouse, prices_ira_self, prices_ira_spouse


def get_ideal_cash_allocation(portfolio, allocation):
    """
    Finds the ideal cash amount to make the portfolio match the allocation goals
    """

    ideal_allocation_portfolio = allocation * np.sum(portfolio)
    portfolio_diff = portfolio - ideal_allocation_portfolio
    max_portfolio_value = portfolio[np.argmax(portfolio_diff)]
    max_allocation_value = allocation[np.argmax(portfolio_diff)]
    ideal_portfolio_total = max_portfolio_value / \
        (max_allocation_value * 100) * 100

    ideal_cash_allocation = np.round(
        ideal_portfolio_total - np.sum(portfolio), 2)

    return ideal_cash_allocation


def get_cash_allocation(portfolio, allocation, cash, prices, asset_classes_total):
    # amount of cash to reach ideal
    ideal_totals = allocation * (np.sum(portfolio) + cash)
    diff_totals = portfolio - ideal_totals

    # create array of securities to add to
    revised_totals = np.zeros(asset_classes_total)
    for i in range(len(diff_totals)):
        if diff_totals[i] < 0 and prices[i] != -1.00:
            revised_totals[i] = diff_totals[i] * -1
        else:
            revised_totals[i] = 0

    # determine biggest gaps
    proportion_totals = revised_totals / np.sum(revised_totals)

    return np.round(proportion_totals * cash, 2)



def get_shares_allocation(starting_portfolio, ideal_allocation, cash_allocation, prices, asset_classes_total):
    shares_total = np.zeros(asset_classes_total)

    while True:
        shares, remainder = np.divmod(cash_allocation, prices)  # type: ignore
        if np.sum(shares) == 0:
            break
        else:
            cash_allocation = get_cash_allocation(
                starting_portfolio, ideal_allocation, np.sum(remainder), prices, asset_classes_total)
            shares_total += shares

    return shares_total


def print_results(shares_ira_self, shares_ira_spouse, prices_ira_self, prices_ira_spouse, cash_ira_self, cash_ira_spouse, starting_portfolio, goal_proportions, ideal_cash_allocation):
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


def get_proportions(arr):
    arr_total = np.sum(arr)
    proportions = np.zeros(len(arr))
    for i in range(len(arr)):
        proportions[i] = arr[i] / arr_total

    return np.round(proportions, 3)


if __name__ == "__main__":
    balance_iras()
