import numpy as np


def get_allocations(starting_portfolio, ideal_allocation, cash_schwab, cash_vanguard, prices_schwab, prices_vanguard):
    # ideal cash
    ideal_cash_allocation = get_ideal_cash_allocation(starting_portfolio, ideal_allocation)

    # how much cash to allocate to each security
    cash_allocation_schwab = get_cash_allocation(starting_portfolio, ideal_allocation, cash_schwab, prices_schwab)
    cash_allocation_vanguard = get_cash_allocation(starting_portfolio, ideal_allocation, cash_vanguard, prices_vanguard)

    # how many shares to buy with cash
    shares_allocation_schwab = get_shares_allocation(starting_portfolio, ideal_allocation, cash_allocation_schwab, prices_schwab)
    shares_allocation_vanguard = get_shares_allocation(starting_portfolio, ideal_allocation, cash_allocation_vanguard, prices_vanguard)

    return shares_allocation_schwab, shares_allocation_vanguard, ideal_cash_allocation


def get_cash_allocation(portfolio, allocation, cash, prices):
    # amount of cash to reach ideal
    ideal_totals = allocation * (np.sum(portfolio) + cash)
    diff_totals = portfolio - ideal_totals

    # create array of securities to add to
    revised_totals = np.zeros(6)
    for i in range(len(diff_totals)):
        if diff_totals[i] < 0 and prices[i] != -1.00:
            revised_totals[i] = diff_totals[i] * -1
        else:
            revised_totals[i] = 0

    # determine biggest gaps
    proportion_totals = revised_totals / np.sum(revised_totals)

    return np.round(proportion_totals * cash, 2)


def get_shares_allocation(starting_portfolio, ideal_allocation, cash_allocation, prices):
    shares_total = np.zeros(6)

    while True:
        shares, remainder = np.divmod(cash_allocation, prices)
        if np.sum(shares) == 0:
            break
        else:
            cash_allocation = get_cash_allocation(starting_portfolio, ideal_allocation, np.sum(remainder), prices)
            shares_total += shares

    return shares_total


def get_proportions(arr):
    arr_total = np.sum(arr)
    proportions = np.zeros(len(arr))
    for i in range(len(arr)):
        proportions[i] = arr[i] / arr_total

    return np.round(proportions, 3)


def get_ideal_cash_allocation(portfolio, allocation):
    ideal_allocation_portfolio = allocation * np.sum(portfolio)
    portfolio_diff = portfolio - ideal_allocation_portfolio
    max_portfolio_value = portfolio[np.argmax(portfolio_diff)]
    max_allocation_value = allocation[np.argmax(portfolio_diff)]
    ideal_portfolio_total = max_portfolio_value / (max_allocation_value * 100) * 100

    return np.round(ideal_portfolio_total - np.sum(portfolio), 2)


def input_numbers():
    # percentages aiming for
    goal_proportions = np.array([0.18, 0.12, 0.15, 0.40, 0.075, 0.075])

    # current data
    starting_portfolio = np.array([1, 1, 1, 1, 1, 1])
    cash_schwab = 1
    cash_vanguard = 1
    prices_schwab = np.array([1, 1, 1, 1, 1, 1])
    prices_vanguard = np.array([1, 1, 1, 1, 1, 1])

    # output shares
    shares_schwab, shares_vanguard, ideal_cash_allocation = get_allocations(starting_portfolio, goal_proportions,
                                                                           cash_schwab, cash_vanguard, prices_schwab,
                                                                           prices_vanguard)
    increase_schwab = shares_schwab * prices_schwab
    increase_vanguard = shares_vanguard * prices_vanguard

    # print results
    print("Goal proportions:       ", goal_proportions)
    print("Starting proportions:   ", get_proportions(starting_portfolio))
    print("Ending proportions:     ", get_proportions(starting_portfolio + increase_schwab + increase_vanguard))
    print("Shares of Schwab:       ", shares_schwab)
    print("Schwab cash remaining:  ", round(cash_schwab - np.sum(increase_schwab), 2))
    print("Shares of Vanguard:     ", shares_vanguard)
    print("Vanguard cash remaining:", round(cash_vanguard - np.sum(increase_vanguard), 2))
    print("Ideal cash addition:    ", ideal_cash_allocation)


if __name__ == "__main__":
    input_numbers()
