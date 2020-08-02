"""
My idea was to start by finding all the current percentages that are under the ideal percentages and record that
difference. I could probably sort by biggest to smallest percentage difference and then add cash until hitting the
number, then go on to the next.

Just made my first trade following an algorithm. lol Put in my current portfolio allocations, cash to trade with, and
the prices and fees of each asset for our IRAs. It spits out the number of shares to buy of each asset for each IRA for
this week. By next week I'm going to update it to save the remainder to a CSV file, to check for and use as available
cash to purchase assets in future weeks.
"""

# import statements
import numpy as np


def crunch_numbers(starting_portfolio, cash, prices_schwab, prices_vanguard):
    ideal_allocation = np.array([0.18, 0.12, 0.15, 0.40, 0.075, 0.075])
    print(ideal_allocation)

    current_total = np.sum(starting_portfolio)
    current_allocation = np.array([starting_portfolio[0]/current_total, starting_portfolio[1]/current_total,
                                   starting_portfolio[2]/current_total, starting_portfolio[3]/current_total,
                                   starting_portfolio[4]/current_total, starting_portfolio[5]/current_total])
    print(current_allocation)

    print(cash)

    allocation_diff = current_allocation - ideal_allocation
    print(allocation_diff)

    need_additions = []

    for i in range(len(allocation_diff)):
        if allocation_diff[i] < 0:
            need_additions.append(allocation_diff[i] * -100)
        else:
            need_additions.append(0)

    print(need_additions)

    shares_schwab = []
    shares_vanguard = []

    return shares_schwab, shares_vanguard


def input_numbers():
    starting_portfolio = np.array([20707.55, 7907.71, 10619.15, 20903.02, 3339.06, 3382.69])
    cash = 1572.49 + 1863.56
    prices_schwab = np.array([72.15, 37.67, 54.45, 165.25, 16.53, 17.90])
    prices_vanguard = np.array([153.71, 37.67, 54.54, 165.25, -1.00, 119.00])

    shares_schwab, shares_vanguard = crunch_numbers(starting_portfolio, cash, prices_schwab, prices_vanguard)

    # output how many shares of each
    # [0. 0. 0. 1. 7. 2.]
    # [ 0.  0.  0.  1. -0.  0.]


if __name__ == "__main__":
    input_numbers()
