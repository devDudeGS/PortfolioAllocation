# import csv to read the data
import csv

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def analyze_data():
    all_data = get_data()
    all_data_df = clean_data(all_data)

    previous_months_to_analyze = 12 * 2
    #graph_budgeting_data(all_data_df, previous_months_to_analyze)


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


def graph_budgeting_data(data):
    # dates, headers = get_dates_and_headers(data)
    # print(headers, dates)

    # get column number for header with name 'budgeting_gas'
    budgeting_gas_column = get_column_number(data, 'budgeting_gas')
    budgeting_apps_column = get_column_number(data, 'budgeting_apps')

    # get data between budgeting_gas and budgeting_apps
    full_data = data[:, budgeting_gas_column:budgeting_apps_column]
    # full_data = [row[budgeting_gas_column:budgeting_apps_column] for row in data]

    # rotate data so that each row is a column
    full_data = np.rot90(full_data)

    # take the last 24 numbers in each column
    #data = [row[-24:] for row in full_data]

    # take the last 24 rows in each column that are not empty string
    recent_data = []
    for row in full_data:
        row = row[-24:]
        row = [element for element in row if element != '']
        recent_data.append(row)


    # get last 24 rows of data between budgeting_gas and budgeting_apps
    # data = data[-24:]
    # data = [row[budgeting_gas_column:budgeting_apps_column] for row in data]

    # convert data to float
    data = [[float(element) for element in row] for row in recent_data]
    # graph data using pandas
    df = pd.DataFrame(data, columns=['Gas', 'Groceries', 'Eating Out', 'Shopping', 'Living Expenses', 'Gifts', 'Travel',
                                     'Kids', 'Apps'])
    df.plot()


def get_column_number(data, param):
    # get column number in data for header with name 'param'
    headers = data[0]
    for i in range(len(headers)):
        if headers[i] == param:
            return i


if __name__ == "__main__":
    analyze_data()
