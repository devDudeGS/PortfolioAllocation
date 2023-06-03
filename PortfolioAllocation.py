import csv
import numpy as np


# SCRIPT IS WIP
def get_allocations(starting_portfolio, ideal_allocation, cash_ira_g, cash_ira_j, prices_ira_g, prices_ira_j):
    # ideal cash
    ideal_cash_allocation = get_ideal_cash_allocation(
        starting_portfolio, ideal_allocation)

    # how much cash to allocate to each security
    cash_allocation_ira_g = get_cash_allocation(
        starting_portfolio, ideal_allocation, cash_ira_g, prices_ira_g)
    cash_allocation_ira_j = get_cash_allocation(
        starting_portfolio, ideal_allocation, cash_ira_j, prices_ira_j)

    # how many shares to buy with cash
    shares_allocation_ira_g = get_shares_allocation(
        starting_portfolio, ideal_allocation, cash_allocation_ira_g, prices_ira_g)
    shares_allocation_ira_j = get_shares_allocation(
        starting_portfolio, ideal_allocation, cash_allocation_ira_j, prices_ira_j)

    return shares_allocation_ira_g, shares_allocation_ira_j, ideal_cash_allocation


def get_cash_allocation(portfolio, allocation, cash, prices):
    # amount of cash to reach ideal
    ideal_totals = allocation * (np.sum(portfolio) + cash)
    diff_totals = portfolio - ideal_totals

    # create array of securities to add to
    revised_totals = np.zeros(7)
    for i in range(len(diff_totals)):
        if diff_totals[i] < 0 and prices[i] != -1.00:
            revised_totals[i] = diff_totals[i] * -1
        else:
            revised_totals[i] = 0

    # determine biggest gaps
    proportion_totals = revised_totals / np.sum(revised_totals)

    return np.round(proportion_totals * cash, 2)


def get_shares_allocation(starting_portfolio, ideal_allocation, cash_allocation, prices):
    shares_total = np.zeros(7)

    while True:
        shares, remainder = np.divmod(cash_allocation, prices)
        if np.sum(shares) == 0:
            break
        else:
            cash_allocation = get_cash_allocation(
                starting_portfolio, ideal_allocation, np.sum(remainder), prices)
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
    ideal_portfolio_total = max_portfolio_value / \
        (max_allocation_value * 100) * 100

    return np.round(ideal_portfolio_total - np.sum(portfolio), 2)


def input_numbers(all_data_np):
    # percentages aiming for
    goal_proportions = all_data_np[1:8, 1]
    goal_proportions = goal_proportions.astype(np.float)

    # current data
    security_type_1 = all_data_np[1, 2:6]
    security_type_1 = security_type_1.astype(np.float)
    security_type_1_sum = np.round(np.sum(security_type_1), 2)
    security_type_2 = all_data_np[2, 2:6]
    security_type_2 = security_type_2.astype(np.float)
    security_type_2_sum = np.round(np.sum(security_type_2), 2)
    security_type_3 = all_data_np[3, 2:6]
    security_type_3 = security_type_3.astype(np.float)
    security_type_3_sum = np.round(np.sum(security_type_3), 2)
    security_type_4 = all_data_np[4, 2:6]
    security_type_4 = security_type_4.astype(np.float)
    security_type_4_sum = np.round(np.sum(security_type_4), 2)
    security_type_5 = all_data_np[5, 2:6]
    security_type_5 = security_type_5.astype(np.float)
    security_type_5_sum = np.round(np.sum(security_type_5), 2)
    security_type_6 = all_data_np[6, 2:6]
    security_type_6 = security_type_6.astype(np.float)
    security_type_6_sum = np.round(np.sum(security_type_6), 2)
    security_type_7 = all_data_np[7, 2:6]
    security_type_7 = security_type_7.astype(np.float)
    security_type_7_sum = np.round(np.sum(security_type_7), 2)
    starting_portfolio = np.array([security_type_1_sum, security_type_2_sum, security_type_3_sum, security_type_4_sum,
                                   security_type_5_sum, security_type_6_sum, security_type_7_sum])

    cash_ira_g = float(all_data_np[8][2])
    cash_ira_j = float(all_data_np[8][3])

    ira_prices_g = all_data_np[1:8, 6]
    ira_prices_g = ira_prices_g.astype(np.float)
    ira_prices_j = all_data_np[1:8, 7]
    ira_prices_j = ira_prices_j.astype(np.float)

    # output shares
    shares_ira_g, shares_ira_j, ideal_cash_allocation = get_allocations(starting_portfolio, goal_proportions,
                                                                        cash_ira_g, cash_ira_j, ira_prices_g,
                                                                        ira_prices_j)
    increase_ira_g = shares_ira_g * ira_prices_g
    increase_ira_j = shares_ira_j * ira_prices_j

    # print results
    print("Goal proportions:       ", goal_proportions)
    print("Starting proportions:   ", get_proportions(starting_portfolio))
    print("Ending proportions:     ", get_proportions(
        starting_portfolio + increase_ira_g + increase_ira_j))
    print("G's IRA cash start:      ", round(cash_ira_g, 2))
    print("Shares of G's IRA:       ", shares_ira_g)
    print("G's IRA cash remaining:  ", round(
        cash_ira_g - np.sum(increase_ira_g), 2))
    print("J's IRA cash start:    ", round(cash_ira_j, 2))
    print("Shares of J's IRA:     ", shares_ira_j)
    print("J's IRA cash remaining:", round(
        cash_ira_j - np.sum(increase_ira_j), 2))
    print("Ideal cash addition:    ", ideal_cash_allocation)


def get_data():
    with open("data/RetirementData.csv", "r") as file:
        reader = csv.reader(file)
        data = list(reader)

    return np.array(data)


def balance_iras():
    all_data_np = get_data()
    input_numbers(all_data_np)


if __name__ == "__main__":
    balance_iras()
