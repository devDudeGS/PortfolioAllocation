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


def crunch_numbers(starting_portfolio, cash_schwab, cash_vanguard, prices_schwab, prices_vanguard):
    ideal_allocation = np.array([0.18, 0.12, 0.15, 0.40, 0.075, 0.075])
    print("ideal allocation")
    print(ideal_allocation)

    current_total = np.sum(starting_portfolio)
    current_allocation = np.array([starting_portfolio[0]/current_total, starting_portfolio[1]/current_total,
                                   starting_portfolio[2]/current_total, starting_portfolio[3]/current_total,
                                   starting_portfolio[4]/current_total, starting_portfolio[5]/current_total])
    print("current allocation")
    print(current_allocation)

    cash = cash_schwab + cash_vanguard
    print("total cash")
    print(cash)

    print("current totals")
    print(starting_portfolio)

    ideal_totals = ideal_allocation * (current_total + cash)
    print("ideal totals")
    print(ideal_totals)

    total_diff = starting_portfolio - ideal_totals
    print("total diffs")
    print(total_diff)

    revised_totals = np.zeros(6)

    for i in range(len(total_diff)):
        if total_diff[i] < 0:
            revised_totals[i] = total_diff[i] / -1
        else:
            revised_totals[i] = 0

    print("revised total")
    print(revised_totals)

    totals_schwab = np.zeros(6)
    totals_vanguard = np.zeros(6)

    for i in range(len(revised_totals)):
        if prices_schwab[i] == -1.00:
            totals_schwab[i] = 0
            totals_vanguard[i] = revised_totals[i]
            continue
        if prices_vanguard[i] == -1.00:
            totals_schwab[i] = revised_totals[i]
            totals_vanguard[i] = 0
            continue
        totals_schwab[i] = revised_totals[i]
        totals_vanguard[i] = revised_totals[i]

    totals_proportion_schwab = totals_schwab / np.sum(totals_schwab)
    totals_proportion_vanguard = totals_vanguard / np.sum(totals_vanguard)

    #totals_proportion = revised_totals / np.sum(revised_totals)
    print("totals proportion")
    print(totals_proportion_schwab)
    print(totals_proportion_vanguard)
    cash_proportion_schwab = totals_proportion_schwab * cash_schwab
    cash_proportion_vanguard = totals_proportion_vanguard * cash_vanguard
    print(cash_proportion_schwab)
    print(cash_proportion_vanguard)
    print(sum(cash_proportion_schwab) + sum(cash_proportion_vanguard))

    shares_schwab = np.zeros(6)
    shares_vanguard = np.zeros(6)
    remainder_schwab = np.zeros(6)
    remainder_vanguard = np.zeros(6)

    # for i in range(len(cash_proportion)):
    #     if cash_proportion[i] > 0:
    #         if prices_schwab[i] == -1.00:
    #             shares, remainder = divmod(cash_proportion[i], prices_vanguard[i])
    #             shares_vanguard[i] = shares
    #             remainder_vanguard[i] = remainder
    #             shares_schwab[i] = 0
    #             remainder_schwab[i] = 0
    #             continue
    #         if prices_vanguard[i] == -1.00:
    #             shares, remainder = divmod(cash_proportion[i], prices_schwab[i])
    #             shares_schwab[i] = shares
    #             remainder_schwab[i] = remainder
    #             shares_vanguard[i] = 0
    #             remainder_vanguard[i] = 0
    #             continue
    #         half = cash_proportion[i] / 2
    #         shares, remainder = divmod(half, prices_schwab[i])
    #         shares_schwab[i] = shares
    #         remainder_schwab[i] = remainder
    #         shares, remainder = divmod(half, prices_vanguard[i])
    #         shares_vanguard[i] = shares
    #         remainder_vanguard[i] = remainder
    #     else:
    #         shares_schwab[i] = 0
    #         shares_vanguard[i] = 0
    #         remainder_schwab[i] = 0
    #         remainder_vanguard[i] = 0

    print("shares schwab")
    print(shares_schwab)
    print("shares vanguard")
    print(shares_vanguard)

    print("remainder schwab")
    print(remainder_schwab)
    print("remainder vanguard")
    print(remainder_vanguard)

    print("total remainder")
    remainder_total = sum(remainder_vanguard) + sum(remainder_schwab)
    print(remainder_total)

    #final_totals = (shares_schwab * prices_schwab) + (shares_vanguard * prices_vanguard) + current_total
    print(shares_schwab * prices_schwab)
    print("final total")
    #print(final_totals)

    # allocation_diff = current_allocation - ideal_allocation
    # print(allocation_diff)
    #
    # need_additions = []
    #
    # for i in range(len(allocation_diff)):
    #     if allocation_diff[i] < 0:
    #         need_additions.append(allocation_diff[i] * -100)
    #     else:
    #         need_additions.append(0)
    #
    # print(need_additions)

    return shares_schwab, shares_vanguard


def input_numbers():
    starting_portfolio = np.array([20707.55, 7907.71, 10619.15, 20903.02, 3339.06, 3382.69])
    cash_schwab = 1572.49
    cash_vanguard = 1863.56
    prices_schwab = np.array([72.15, 37.67, 54.45, 165.25, 16.53, 17.90])
    prices_vanguard = np.array([153.71, 37.67, 54.54, 165.25, -1.00, 119.00])

    shares_schwab, shares_vanguard = crunch_numbers(starting_portfolio, cash_schwab, cash_vanguard, prices_schwab, prices_vanguard)

    # output how many shares of each
    # [0. 0. 0. 1. 7. 2.]
    # [ 0.  0.  0.  1. -0.  0.]


if __name__ == "__main__":
    input_numbers()
