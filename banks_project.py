import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from datetime import datetime
import sqlite3

# The global Variables

URL = "https://web.archive.org/web/20230908091635/https://en.wikipedia.org/wiki/List_of_largest_banks"

TABLE_ATTRIBUTES = ["Name", "MC_USD_Billion"]

CSV_PATH = "./exchange_rate.csv"

OUTPUT_CSV = "./Largest_banks_data.csv"

DB_NAME = "Banks.db"

TABLE_NAME = "Largest_banks"

LOG_FILE = "code_log.txt"

# The logging Function

def log_progress(message):

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(LOG_FILE, "a") as log:
        log.write(f"{timestamp} : {message}\n")

# The extraction function

def extract(url, table_attribs):

    html_text = requests.get(url).text

    soup = BeautifulSoup(html_text, "html.parser")

    bank_df = pd.DataFrame(columns=table_attribs)

    table_bodies = soup.find_all("tbody")

    rows = table_bodies[0].find_all("tr")

    for row in rows:

        columns = row.find_all("td")

        if len(columns) != 0:

            bank_name = columns[1].find_all("a")[1]["title"]

            market_cap = float(columns[2].contents[0][:-1])

            temp_df = pd.DataFrame(
                {
                    "Name": [bank_name],
                    "MC_USD_Billion": [market_cap]
                }
            )

            bank_df = pd.concat(
                [bank_df, temp_df],
                ignore_index=True
            )

    return bank_df

# Transform Function

def transform(df, csv_path):

    rates_df = pd.read_csv(csv_path)

    exchange_rates = (
        rates_df.set_index("Currency")
        .to_dict()["Rate"]
    )

    gbp_rate = float(exchange_rates["GBP"])
    eur_rate = float(exchange_rates["EUR"])
    inr_rate = float(exchange_rates["INR"])

    df["MC_GBP_Billion"] = [
        np.round(value * gbp_rate, 2)
        for value in df["MC_USD_Billion"]
    ]

    df["MC_EUR_Billion"] = [
        np.round(value * eur_rate, 2)
        for value in df["MC_USD_Billion"]
    ]

    df["MC_INR_Billion"] = [
        np.round(value * inr_rate, 2)
        for value in df["MC_USD_Billion"]
    ]

    return df

    print(df["MC_EUR_Billion"][4])

    log_progress("Data transformation complete. Initiating Loading process")

    load_to_csv(df, OUTPUT_CSV)

    log_progress("Data saved to CSV file")

# The function to save to CSV

def load_to_csv(df, output_path):

    df.to_csv(output_path, index=False)

# The function to save to Database

def load_to_db(df, sql_connection, table_name):

    df.to_sql(
        table_name,
        sql_connection,
        if_exists="replace",
        index=False
    )

# The function to run SQL Query

def run_query(query_statement, sql_connection):

    print("\nQUERY:")
    print(query_statement)

    result = pd.read_sql(
        query_statement,
        sql_connection
    )

    print(result)


# Main ETL Workflow

log_progress(
    "Preliminaries complete. Initiating ETL process"
)

# Extraction

banks_df = extract(URL, TABLE_ATTRIBUTES)

log_progress(
    "Data extraction complete. Initiating Transformation process"
)

# Transformation

banks_df = transform(
    banks_df,
    CSV_PATH
)

print(banks_df)

print("\n5th Bank Market Cap in EUR (Billion):")
print(banks_df["MC_EUR_Billion"][4])

log_progress(
    "Data transformation complete. Initiating Loading process"
)

# CSV Loading

load_to_csv(
    banks_df,
    OUTPUT_CSV
)

log_progress(
    "Data saved to CSV file"
)

# Database Connection

connection = sqlite3.connect(DB_NAME)

log_progress(
    "SQL Connection initiated"
)

# Database Loading

load_to_db(
    banks_df,
    connection,
    TABLE_NAME
)

log_progress(
    "Data loaded to Database as a table, Executing queries"
)

# Queries

run_query(
    "SELECT * FROM Largest_banks",
    connection
)

run_query(
    "SELECT AVG(MC_GBP_Billion) FROM Largest_banks",
    connection
)

run_query(
    "SELECT Name FROM Largest_banks LIMIT 5",
    connection
)

log_progress(
    "Process Complete"
)

# Close Connection

connection.close()

log_progress(
    "Server Connection closed"
)