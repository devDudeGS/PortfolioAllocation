import numpy as np


def get_allocations(starting_portfolio, ideal_allocation, cash_schwab, cash_vanguard, prices_schwab, prices_vanguard):
    # how much cash to allocate to each security
    cash_allocation_schwab = get_cash_allocation(starting_portfolio, ideal_allocation, cash_schwab, prices_schwab)
    cash_allocation_vanguard = get_cash_allocation(starting_portfolio, ideal_allocation, cash_vanguard, prices_vanguard)

    # how many shares to buy with cash
    shares_allocation_schwab = get_shares_allocation(cash_allocation_schwab, prices_schwab)
    shares_allocation_vanguard = get_shares_allocation(cash_allocation_vanguard, prices_vanguard)

    return shares_allocation_schwab, shares_allocation_vanguard


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


def get_shares_allocation(cash_allocation, prices):
    shares, remainder = np.divmod(cash_allocation, prices)

    return shares


def get_proportions(arr):
    arr_total = np.sum(arr)
    proportions = np.zeros(len(arr))
    for i in range(len(arr)):
        proportions[i] = arr[i] / arr_total

    return np.round(proportions, 3)


def input_numbers():
    # percentages aiming for
    goal_proportions = np.array([0.18, 0.12, 0.15, 0.40, 0.075, 0.075])

    # current data
    starting_portfolio = np.array([20707.55, 7907.71, 10619.15, 20903.02, 3339.06, 3382.69])
    cash_schwab = 1572.49 / 3
    cash_vanguard = 1863.56 / 3
    prices_schwab = np.array([72.15, 37.67, 54.45, 165.25, 16.53, 17.90])
    prices_vanguard = np.array([153.71, 37.67, 54.54, 165.25, -1.00, 119.00])

    # output shares
    shares_schwab, shares_vanguard = get_allocations(starting_portfolio, goal_proportions,
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


if __name__ == "__main__":
    input_numbers()
