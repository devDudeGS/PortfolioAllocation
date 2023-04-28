import csv

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
        print("account breakdown $$: ", np.round(this_acct_absolutes, 2))
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


def input_numbers(all_data_np):
    # percentages aiming for
    goal_proportions = all_data_np[1:5, 1]
    goal_proportions = goal_proportions.astype(np.float)

    # 1. Input: total of all $$ in all retirement accounts
    retirement_total = all_data_np[1:9, 2:6]
    retirement_total = retirement_total.astype(np.float)
    retirement_total = np.round(np.sum(retirement_total), 2)

    # 2. Input: current $$ totals in each 401k account
    # g_401k_total = 1
    # j_401k_total = 1
    # old_401k_1_total = 1
    # old_401k_2_total = 1
    # OR
    portfolio_all_cats = all_data_np[1:5, 4:6]
    portfolio_all_cats = portfolio_all_cats.astype(np.float)
    portfolio_breakdown = np.sum(portfolio_all_cats, axis=0)

    # TEMP while 4 accounts
    zeros = np.ones(2)
    portfolio_breakdown = np.concatenate((portfolio_breakdown, zeros), axis=0)
    #portfolio_breakdown = np.array([6881.98, 30607.49, 9924.33, 12626.70])

    portfolio_total, portfolio_proportions, portfolio_proportion_of_total = get_totals(retirement_total,
                                                                                       portfolio_breakdown)

    goal_proportions_total, new_goal_proportions, expected_finals = adjust_goal_proportions(goal_proportions,
                                                                           portfolio_proportion_of_total,
                                                                           retirement_total)

    # category participation
    # Create an array of zeros with the same number of columns as the input array
    output_arrays = np.zeros_like(portfolio_all_cats)

    # Create separate arrays for each column of values
    for i in range(portfolio_all_cats.shape[1]):
        output_arrays[:, i] = np.where(portfolio_all_cats[:, i] > 0, 1, 0)
    #output_arrays = np.reshape(output_arrays, (2, 4))
    col1, col2 = np.split(output_arrays, 2, axis=1)

    # g_401k_cats = np.array([1, 1, 1, 1])
    # j_401k_cats = np.array([1, 0, 0, 1])
    g_401k_cats = col1.flatten()
    j_401k_cats = col2.flatten()
    # old_401k_1_cats = np.array([1, 1, 1, 1])
    # old_401k_2_cats = np.array([1, 1, 1, 1])
    old_401k_1_cats = np.ones(4)
    old_401k_2_cats = np.ones(4)
    all_acct_cats = [g_401k_cats, j_401k_cats, old_401k_1_cats, old_401k_2_cats]

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


def get_data():
    with open("data/RetirementData.csv", "r") as file:
        reader = csv.reader(file)
        data = list(reader)

    return np.array(data)


def balance_401ks():
    all_data_np = get_data()
    input_numbers(all_data_np)


if __name__ == "__main__":
    balance_401ks()
