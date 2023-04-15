# import csv to read the data
import csv

def get_data():
    # read the data from the csv file
    with open("data/BudgetingData.csv", "r") as file:
        reader = csv.reader(file)
        data = list(reader)

    # return the data
    return data

def analyze_data():
    # get the data
    data = get_data()

    # get the headers
    headers = data[0]

    # get the data
    data = data[1:]

    # get the total number of rows
    rows = len(data)

    # get the total number of columns
    columns = len(headers)

    # print the total number of rows and columns
    print("Total number of rows: " + str(rows))
    print("Total number of columns: " + str(columns))

    # print the headers
    print("Headers: " + str(headers))

    # print the first row
    print("First row: " + str(data[0]))

    # print the last row
    print("Last row: " + str(data[-1]))

    # print the data type of the first element in the first row
    print("Data type of first element in first row: " + str(type(data[0][0])))

    # print the data type of the first element in the last row
    print("Data type of first element in last row: " + str(type(data[-1][0])))

    # print the data type of the last element in the first row
    print("Data type of last element in first row: " + str(type(data[0][-1])))

    # print the data type of the last element in the last row
    print("Data type of last element in last row: " + str(type(data[-1][-1])))

    # print the data type of the first element in the first column
    print("Data type of first element in first column: " + str(type(data[0][0])))

    # print the data type of the first element in the last column
    print("Data type of first element in last column: " + str(type(data[0][-1])))

    # print the data type of the last element in the first column
    print("Data type of last element in first column: " + str(type(data[-1][0])))

    # print the data type of the last element in the last column
    print("Data type of last element in last column: " + str(type(data[-1][-1])))

    # print the data type of the first element in the first row
    #print("Data type of first element

if __name__ == "__main__":
    analyze_data()
