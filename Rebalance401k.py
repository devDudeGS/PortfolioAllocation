import csv
import numpy as np


def balance_401ks():
    security_types_total = 7

    all_data = get_data()
    goal_proportions, portfolio_breakdown, portfolio_total = get_input_vars(
        all_data, security_types_total)
    target_amounts = get_targets(goal_proportions, portfolio_total)
    new_portfolio_breakdown = get_new_portfolio_breakdown(
        portfolio_breakdown, target_amounts)
    create_allocation_percentages(new_portfolio_breakdown)


def get_data():
    """
    Data in the format:

    security_type,ideal_portfolio,ira_self,ira_spouse,401k_self,401k_spouse,ira_prices_self,ira_prices_spouse
    type_1,0.20,100,100,100,100,50,50
    type_2,0.15,100,100,100,0.00,50,50
    type_3,0.30,100,100,100,0.00,50,50
    etc,0.35,100,100,100,100,50,50
    """
    with open("data/RetirementData.csv", "r") as file:
        reader = csv.reader(file)
        data = list(reader)

    return np.array(data)


def get_input_vars(data, security_types_total):
    # 401k portfolio breakdown
    final_row_index = security_types_total + 1
    portfolio_breakdown = data[1:final_row_index, 4:6].astype(np.float)
    nonzero_rows = np.where(np.sum(portfolio_breakdown, axis=1) > 0)[0]
    portfolio_breakdown = portfolio_breakdown[nonzero_rows]  # type: ignore
    print()
    print("Portfolio breakdown: ")
    print(portfolio_breakdown)
    portfolio_acct_totals = np.sum(portfolio_breakdown, axis=0)
    print("Portfolio account totals: ")
    print(portfolio_acct_totals)
    portfolio_total = np.sum(portfolio_breakdown)
    print("Portfolio total: ")
    print(portfolio_total)
    print()

    # category proportions aiming for, normalized to 1.0
    goal_proportions = data[1:final_row_index, 1].astype(np.float)
    print("Goal proportions: ", goal_proportions)
    normalized_goal_proportions = np.round(goal_proportions[nonzero_rows] /
                                           np.sum(goal_proportions[nonzero_rows]), 2)
    print("Normalized goal proportions: ", normalized_goal_proportions)
    print()
    print()

    return normalized_goal_proportions, portfolio_breakdown, portfolio_total


def get_targets(goal_proportions, portfolio_total):
    # create target amounts, from total * proportions
    target_amounts = np.round(portfolio_total * goal_proportions, 2)
    print("Target amounts: ", target_amounts)
    print()
    print()

    return target_amounts


def get_new_portfolio_breakdown(portfolio_breakdown, target_amounts):
    """
    Adjusts the values in the portfolio_breakdown array so that the rows sum as close as possible
        to the corresponding value in the target_amounts array.
    Utilized GPT-4 to help generate this code.

    Parameters:
    portfolio_breakdown (numpy.ndarray): A 2D numpy array of the dollar amounts in the portfolio,
        where each row is an investment category and each column is a unique account.
    target_amounts (numpy.ndarray): A 1D numpy array of the target dollar amounts for each investment category.

    Returns:
    numpy.ndarray: A 2D numpy array that has the same shape as portfolio_breakdown,
        with the values adjusted so that the rows sum as close as possible to the corresponding value
        in the target_amounts array.

    Test Results:
    1. Column totals are equal!
    2. Target amounts are off :(
    3. All values are positive!
    """

    # Calculate the column totals of the portfolio_breakdown array
    col_totals = np.sum(portfolio_breakdown, axis=0)

    # Create a copy of the portfolio_breakdown array
    new_portfolio_breakdown = np.copy(portfolio_breakdown)

    # Loop over each column of the portfolio_breakdown array
    for i in range(portfolio_breakdown.shape[1]):
        # Calculate the row totals for the current column
        row_totals = np.sum(new_portfolio_breakdown[:, i])

        # Calculate the adjustment factor for the current column
        if row_totals > 0:
            adjustment_factor = target_amounts * \
                col_totals[i] / row_totals  # type: ignore
        else:
            adjustment_factor = np.zeros_like(target_amounts)

        # Adjust the values in the current column
        new_portfolio_breakdown[:, i] *= adjustment_factor / \
            np.sum(adjustment_factor)  # type: ignore

    # Verify that the row totals of the new_portfolio_breakdown array are as close as possible to the target amounts
    new_row_totals = np.sum(new_portfolio_breakdown, axis=1)
    row_adjustment_factors = np.minimum(
        target_amounts / new_row_totals, 1)  # type: ignore
    new_portfolio_breakdown *= row_adjustment_factors[:, np.newaxis]

    # Adjust the column totals of the new_portfolio_breakdown array to match the original column totals
    new_col_totals = np.sum(new_portfolio_breakdown, axis=0)
    col_adjustment_factors = col_totals / new_col_totals
    new_portfolio_breakdown *= col_adjustment_factors[np.newaxis, :]
    new_portfolio_breakdown = np.round(new_portfolio_breakdown, 2)

    # Verify that column totals stayed the same
    print("New portfolio breakdown: ")
    print(new_portfolio_breakdown)
    print()
    portfolio_acct_totals = np.sum(new_portfolio_breakdown, axis=0)
    print("New column totals: ")
    print(portfolio_acct_totals)
    print("vs")
    print("Original columns: ")
    print(np.sum(portfolio_breakdown, axis=0))
    print()

    # Verify that row totals are as close as possible to the target amounts
    new_portfolio_totals = np.sum(new_portfolio_breakdown, axis=1)
    print("New portfolio totals: ")
    print(new_portfolio_totals)
    print("vs")
    print("Target amounts: ")
    print(target_amounts)
    print()

    return new_portfolio_breakdown


def create_allocation_percentages(new_portfolio_breakdown):
    # Calculate the column totals
    column_totals = np.sum(new_portfolio_breakdown, axis=0)

    # Create the allocation_percentages array with the same shape as new_portfolio_breakdown
    allocation_percentages = np.zeros_like(new_portfolio_breakdown)

    # Replace the amounts in new_portfolio_breakdown with fractions of the column total
    for i in range(new_portfolio_breakdown.shape[1]):
        allocation_percentages[:,  # type: ignore
                               i] = new_portfolio_breakdown[:, i] / column_totals[i]  # type: ignore
    allocation_percentages = np.round(allocation_percentages, 2)
    print("Allocation percentages: ")
    print(allocation_percentages)
    column_sums = np.sum(allocation_percentages, axis=0)
    print(column_sums)
    print()


if __name__ == "__main__":
    balance_401ks()
