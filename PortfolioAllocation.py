import numpy as np


def get_allocations(starting_portfolio, ideal_allocation, cash_schwab, cash_vanguard, prices_schwab, prices_vanguard):
    cash_allocation_schwab = get_cash_allocation(starting_portfolio, ideal_allocation, cash_schwab, prices_schwab)
    cash_allocation_vanguard = get_cash_allocation(starting_portfolio, ideal_allocation, cash_vanguard, prices_vanguard)

    shares_allocation_schwab = get_shares_allocation(cash_allocation_schwab, prices_schwab)
    shares_allocation_vanguard = get_shares_allocation(cash_allocation_vanguard, prices_vanguard)

    return shares_allocation_schwab, shares_allocation_vanguard


def get_cash_allocation(portfolio, allocation, cash, prices):
    ideal_totals = allocation * (np.sum(portfolio) + cash)
    diff_totals = portfolio - ideal_totals

    revised_totals = np.zeros(6)

    for i in range(len(diff_totals)):
        if diff_totals[i] < 0 and prices[i] != -1.00:
            revised_totals[i] = diff_totals[i] * -1
        else:
            revised_totals[i] = 0

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
    cash_schwab = 1572.49
    cash_vanguard = 1863.56
    prices_schwab = np.array([72.15, 37.67, 54.45, 165.25, 16.53, 17.90])
    prices_vanguard = np.array([153.71, 37.67, 54.54, 165.25, -1.00, 119.00])


    print("ideal allocation")
    print(goal_proportions)
    print("original allocation")
    current_proportions = get_proportions(starting_portfolio)
    print(current_proportions)

    shares_allocation_schwab, shares_allocation_vanguard = get_allocations(starting_portfolio, goal_proportions, cash_schwab, cash_vanguard, prices_schwab, prices_vanguard)
    print(shares_allocation_schwab)
    print(shares_allocation_vanguard)

    increase_schwab = shares_allocation_schwab * prices_schwab
    increase_vanguard = shares_allocation_vanguard * prices_vanguard

    print("new allocation")
    new_proportions = get_proportions(increase_schwab + increase_vanguard + starting_portfolio)
    print(new_proportions)

    print("schwab cash left")
    print(cash_schwab - np.sum(shares_allocation_schwab * prices_schwab))

    print("vanguard cash left")
    print(cash_vanguard - np.sum(shares_allocation_vanguard * prices_vanguard))

    # output how many shares of each
    # [0. 0. 0. 1. 7. 2.]
    # [ 0.  0.  0.  1. -0.  0.]


if __name__ == "__main__":
    input_numbers()
