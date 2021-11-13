import numpy as np


def get_totals(retirement_total, portfolio_breakdown):
    print("retirement total: ", retirement_total)

    # 3. Add totals together, and calculate proportion of each to sum total
    portfolio_total = np.sum(portfolio_breakdown)
    print("portfolio total: ", portfolio_total)

    # in proportion to portfolio total, NOT retirement total
    portfolio_proportions = get_proportions(portfolio_breakdown)

    # 4. Find % of sum total to retirement total
    portfolio_proportion_of_total = round(portfolio_total / retirement_total, 3)

    return portfolio_total, portfolio_proportions, portfolio_proportion_of_total


def adjust_goal_proportions(goal_proportions, portfolio_proportion_of_total, retirement_total):
    # 5. Compare sum total % to goal proportion total % (for 401k categories)
    goal_proportions_total = np.round(np.sum(goal_proportions), 3)

    # 6. Adjust goal proportion to match actual proportion ideal
    new_goal_proportions = portfolio_proportion_of_total / goal_proportions_total * goal_proportions

    # 7. Use actual proportion ideal to calculate ideal $$ totals for each (use for later comparison)
    expected_finals = np.round(new_goal_proportions * retirement_total, 2)
    print("Expected numbers by category:       ", expected_finals)
    print("Expected total:   ", np.round(np.sum(expected_finals), 2))

    return goal_proportions_total, new_goal_proportions, expected_finals


# TODO: this function needs work
def get_absolute_proportions(portfolio_proportions, new_goal_proportions, all_acct_cats, expected_finals,
                             retirement_total, portfolio_total, portfolio_breakdown):
    # 8. Find absolute % for each category / account
    # i.e. acct allocation % * cat allocation % = absolute %
    # or acct allocation / all acct allocations (100% - non-participating accts) * cat allocation = absolute %

    all_acct_absolute = []
    # NEW VERSION!
    print("Total in 401ks: ", portfolio_total)
    for i in range(len(all_acct_cats)):
        leftover_acct = portfolio_breakdown[i]
        print("Total in this portfolio across all cats: ", leftover_acct)
        this_acct_allocation = portfolio_proportions[i]
        print("Accounts for 401k%: ", this_acct_allocation)
        this_acct_absolutes = np.zeros(len(all_acct_cats[i]))
        adjusted_allocation_arr = np.zeros(len(all_acct_cats[i]))
        leftover_cats = np.zeros(len(all_acct_cats[i]))
        if i < len(all_acct_cats) - 1:
            for j in range(len(all_acct_cats[i])):
                expected_cat = expected_finals[j]
                print("Total in this cat across all portfolios: ", expected_cat)
                all_acct_allocations = 100
                missing_acct_flag = False
                for m in range(len(all_acct_cats[i])):
                    if i == m:
                        continue
                    elif all_acct_cats[m][j] == 0:
                        all_acct_allocations -= (portfolio_proportions[m] * 100)
                        missing_acct_flag = True
                if missing_acct_flag:
                    all_acct_allocations /= 100
                    leftover_acct -= (this_acct_allocation / all_acct_allocations * expected_cat)
                else:
                    leftover_cats[j] = expected_cat
                    all_acct_allocations = 1
                adjusted_allocation_arr[j] = all_acct_allocations
            # TODO: handle accounts where some cats are 0
            for j in range(len(adjusted_allocation_arr)):
                expected_cat = expected_finals[j]
                adjusted_allocation = this_acct_allocation / adjusted_allocation_arr[j]
                acct_cat_total = 0
                if adjusted_allocation == this_acct_allocation:
                    leftover_cats_proportions = get_proportions(leftover_cats)
                    acct_cat_total = leftover_cats_proportions[j] * np.sum(leftover_acct) * all_acct_cats[i][j]
                else:
                    acct_cat_total = expected_cat * adjusted_allocation * all_acct_cats[i][j]
                this_acct_absolutes[j] = acct_cat_total
        else:
            for j in range(len(all_acct_cats[i])):
                expected_cat = expected_finals[j]
                if all_acct_cats[i][j] != 0:
                    current_cat_total = 0
                    for acct in all_acct_absolute:
                        acct_total = acct[j] / 100 * retirement_total
                        current_cat_total += acct_total
                    this_acct_absolutes[j] = expected_cat - current_cat_total
                else:
                    this_acct_absolutes[j] = 0
        print("account sum: ", np.sum(this_acct_absolutes))
        this_acct_absolutes = this_acct_absolutes / retirement_total * 100
        all_acct_absolute.append(this_acct_absolutes)

    # OLD VERSION!
    # for i in range(len(all_acct_cats)):
    #     this_acct_absolutes = np.zeros(len(all_acct_cats[i]))
    #     for j in range(len(all_acct_cats[i])):
    #         this_acct_allocation = portfolio_proportions[i]
    #         all_acct_allocations = 100
    #         for m in range(len(all_acct_cats)):
    #             if i == m:
    #                 continue
    #             elif all_acct_cats[m][j] == 0:
    #                 all_acct_allocations -= (portfolio_proportions[m] * 100)
    #         all_acct_allocations /= 100
    #         this_acct_absolutes[j] = round((this_acct_allocation * 100) / all_acct_allocations * new_goal_proportions[j] * all_acct_cats[i][j], 3)
    #     all_acct_absolute.append(this_acct_absolutes)

    all_absolute_sum = 0
    for acct in all_acct_absolute:
        all_absolute_sum += np.sum(acct)
    print("All absolute %s add up to:       ", all_absolute_sum)

    return all_acct_absolute


def get_relative_proportions(all_acct_absolute):
    # 9. Output: relative % for each category / account
    # i.e. absolute cat/acct % / absolute acct total % = relative %
    # Use this to update existing percentages in accts, but for future stick to ideal in spreadsheet

    all_acct_relative = []
    for i in range(len(all_acct_absolute)):
        this_acct_relatives = np.zeros(len(all_acct_absolute[i]))
        for j in range(len(all_acct_absolute[i])):
            absolute_cat_per_acct = all_acct_absolute[i][j]
            absolute_acct_total = np.sum(all_acct_absolute[i])
            #print(absolute_cat_per_acct)
            #print(absolute_acct_total)
            this_acct_relatives[j] = round(absolute_cat_per_acct / absolute_acct_total, 3)
        print(np.sum(this_acct_relatives))
        all_acct_relative.append(this_acct_relatives)

    return all_acct_relative


def get_proportions(arr):
    arr_total = np.sum(arr)
    proportions = np.zeros(len(arr))
    for i in range(len(arr)):
        proportions[i] = arr[i] / arr_total

    return np.round(proportions, 3)


def input_numbers():
    # percentages aiming for
    goal_proportions = np.array([0.18, 0.08, 0.04, 0.15])

    # 1. Input: total of all $$ in all retirement accounts
    retirement_total = 100

    # 2. Input: current $$ totals in each 401k account
    # principal_total = 1
    # betterment_total = 1
    # empower_total = 1
    # prudential_total = 1
    # OR
    portfolio_breakdown = np.array([5, 5, 5, 5])

    portfolio_total, portfolio_proportions, portfolio_proportion_of_total = get_totals(retirement_total,
                                                                                       portfolio_breakdown)

    goal_proportions_total, new_goal_proportions, expected_finals = adjust_goal_proportions(goal_proportions,
                                                                           portfolio_proportion_of_total,
                                                                           retirement_total)

    # category participation
    principal_cats = np.array([1, 1, 1, 1])
    betterment_cats = np.array([1, 1, 1, 1])
    empower_cats = np.array([1, 1, 1, 1])
    prudential_cats = np.array([1, 0, 0, 1])
    all_acct_cats = [principal_cats, betterment_cats, empower_cats, prudential_cats]

    all_acct_absolute = get_absolute_proportions(portfolio_proportions, new_goal_proportions, all_acct_cats,
                                                 expected_finals, retirement_total, portfolio_total, portfolio_breakdown)
    for i in range(len(all_acct_absolute)):
        decimal_percentages = all_acct_absolute[i]/100
        print(decimal_percentages)
        acct_total = retirement_total * decimal_percentages
        print(acct_total)
        print(np.sum(acct_total))

    all_acct_relative = get_relative_proportions(all_acct_absolute)

    # check work
    cat_1_total = 0
    cat_2_total = 0
    cat_3_total = 0
    cat_4_total = 0
    for i in range(len(all_acct_relative)):
        print("account proportions: ", all_acct_relative[i])
        acct_sums = all_acct_relative[i] * portfolio_breakdown[i]
        cat_1_total += acct_sums[0]
        cat_2_total += acct_sums[1]
        cat_3_total += acct_sums[2]
        cat_4_total += acct_sums[3]

    print(cat_1_total)
    print(cat_2_total)
    print(cat_3_total)
    print(cat_4_total)

    # # percentages aiming for
    # goal_proportions = np.array([0.18, 0.08, 0.04, 0.15, 0.40, 0.075, 0.075])
    #
    # # current data
    # starting_portfolio = np.array([1, 1, 1, 1, 1, 1])
    # cash_schwab = 1
    # cash_vanguard = 1
    # prices_schwab = np.array([1, 1, 1, 1, 1, 1])
    # prices_vanguard = np.array([1, 1, 1, 1, 1, 1])
    #
    # # output shares
    # shares_schwab, shares_vanguard, ideal_cash_allocation = get_allocations(starting_portfolio, goal_proportions,
    #                                                                        cash_schwab, cash_vanguard, prices_schwab,
    #                                                                        prices_vanguard)
    # increase_schwab = shares_schwab * prices_schwab
    # increase_vanguard = shares_vanguard * prices_vanguard
    #
    # # print results
    # print("Goal proportions:       ", goal_proportions)
    # print("Starting proportions:   ", get_proportions(starting_portfolio))
    # print("Ending proportions:     ", get_proportions(starting_portfolio + increase_schwab + increase_vanguard))
    # print("Shares of Schwab:       ", shares_schwab)
    # print("Schwab cash remaining:  ", round(cash_schwab - np.sum(increase_schwab), 2))
    # print("Shares of Vanguard:     ", shares_vanguard)
    # print("Vanguard cash remaining:", round(cash_vanguard - np.sum(increase_vanguard), 2))
    # print("Ideal cash addition:    ", ideal_cash_allocation)


if __name__ == "__main__":
    input_numbers()
