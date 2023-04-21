# import csv to read the data
import csv

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def analyze_data():
    all_data = get_data()
    all_data_df = clean_data(all_data)

    previous_months_to_analyze = 12 * 2
    graph_data(all_data_df, previous_months_to_analyze)


def get_data():
    with open("data/BudgetingData.csv", "r") as file:
        reader = csv.reader(file)
        data = list(reader)

    return data


def clean_data(data):
    data = np.array(data)

    # find and remove empty rows
    empty_rows = np.where(data[:, 0] == "")[0]
    if empty_rows.size > 0:
        data = data[:empty_rows[0]]

    dates, headers = get_dates_and_headers(data)

    # remove dates and headers
    data = np.delete(data, 0, axis=0)
    data = np.delete(data, 0, axis=1)

    # Convert the array to a Pandas dataframe
    df = pd.DataFrame(data)

    # Convert numeric strings to float64 type
    df = df.apply(pd.to_numeric, errors='ignore')

    # Set the column headers and index to the dataframe
    df.columns = headers
    df.index = pd.to_datetime(dates)

    return df


def get_dates_and_headers(data):
    dates = data[1:, 0]
    dates = pd.to_datetime(dates).values.astype('datetime64[D]')
    print("Dates: " + str(dates))
    print()
    months = len(dates)
    years = months / 12
    print("Total number of months: " + str(months))
    print("Total number of years: " + str(years))
    print()

    headers = data[0, 1:]
    print("Headers: " + str(headers))
    print()

    return dates, headers


def graph_data(data, previous_months_to_analyze):
    graph_budgeting_data(data, previous_months_to_analyze)
    graph_salary_data(data)
    graph_monthly_income_data(data)


def plot_and_save(column_1, column_2, data, file_name, previous_months_to_analyze, title, x_label, y_label):
    # Select columns between two headers during time period
    df = data.loc[:, column_1:column_2]
    if previous_months_to_analyze > 0:
        df = df.tail(previous_months_to_analyze)

    # Create a line plot of the data
    plt.close('all')
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.grid()
    plt.plot(df)
    plt.legend(df.columns, loc="best")
    plt.xticks(rotation=45)

    # save the graph
    plt.savefig("graphs/" + file_name)


def graph_budgeting_data(data, previous_months_to_analyze):
    column_1 = 'budgeting_gas'
    column_2 = 'budgeting_kids'
    title = 'Budgeting Data'
    x_label = 'Month'
    y_label = 'Spent'
    file_name = 'BudgetingData.png'

    plot_and_save(column_1, column_2, data, file_name, previous_months_to_analyze,
                  title, x_label, y_label)


def graph_salary_data(data):
    column_1 = 'annual_gross_pay_g'
    column_2 = 'annual_gross_pay_j'
    title = 'Salary Data'
    x_label = 'Time'
    y_label = 'Annual Salary'
    file_name = 'SalaryData.png'

    plot_and_save(column_1, column_2, data, file_name, 0,
                  title, x_label, y_label)


def graph_monthly_income_data(data):
    column_1 = 'income_total'
    column_2 = 'income_total'
    title = 'Monthly Income Data'
    x_label = 'Time'
    y_label = 'Earnings'
    file_name = 'MonthlyIncomeData.png'

    plot_and_save(column_1, column_2, data, file_name, 0,
                  title, x_label, y_label)


if __name__ == "__main__":
    analyze_data()
