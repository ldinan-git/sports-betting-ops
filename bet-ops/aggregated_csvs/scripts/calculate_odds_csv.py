import pandas as pd
import json
import numpy as np
from datetime import datetime
import argparse
import os
from helper_functions import *

# Define a function to calculate dejuice
def calculate_dejuice(row, new_df):
    game = row['game']
    market = row['market']
    description = row['description']
    point = row['point']
    bookmakers = [col for col in row.index if '_implied_prob' in col]
    dejuice_values = {}
    for bookmaker in bookmakers:
        denom = new_df.loc[(new_df['game'] == game) & (new_df['market'] == market) & (new_df['description'] == description) & (new_df['point'] == point), bookmaker].sum()
        dejuice = row[bookmaker] / denom
        dejuice_values[bookmaker.replace('_implied_prob', '_dejuice')] = dejuice
        if dejuice == 1:
            # denom = new_df.loc[(new_df['game'] == game) & (new_df['market'] == market) & (new_df['point'] == point), bookmaker].sum()
            denom = 1.15 # assume 15% vig for one way markets
            dejuice = row[bookmaker] / denom
            dejuice_values[bookmaker.replace('_implied_prob', '_dejuice')] = dejuice

    return pd.Series(dejuice_values)

def get_files(sport):
    directory = f"C:\\Users\\ldinan\\Documents\\GitHub\\sports-betting-ops\\bet-ops\\odds_api_responses\\output\\{sport}\\player_props\\"
    files = os.listdir(directory)
    return files, directory


def get_rows(data):
    # Create a list to store the rows of the DataFrame
    rows = []

    for bookmaker in data['bookmakers']:
        for market in bookmaker['markets']:
            for outcome in market['outcomes']:
                row = {
                    'market': market['key'],
                    'description': outcome['description'],
                    'name': outcome['name'],
                    'point': outcome.get('point', ''),
                    f"{bookmaker['key']}_price": outcome['price'],
                    # f"{bookmaker['key']}_point": outcome.get('point', ''),
                    f"{bookmaker['key']}_name": outcome['name']
                }
                rows.append(row)
    
    return rows

def apply_function(df, old_col,new_col, function):
    # Apply the function to each bookmaker's odds
    for bookmaker in df.columns:
        if old_col in bookmaker:
            df[f"{bookmaker.replace(old_col, new_col)}"] = df[bookmaker].apply(function)

    return df

def add_dejuice(df):
    dejuice_df = df.apply(calculate_dejuice, args=(df,), axis=1)

    # Add dejuice values to the original DataFrame
    new_df = pd.concat([df, dejuice_df], axis=1)

    return new_df

def add_implied_prob_diff(df):
    implied_prob_cols = [col for col in df.columns if '_implied_prob' in col]
    for col in implied_prob_cols:
        other_implied_prob_cols = [c for c in implied_prob_cols if c != col]
        df[f"{col}_diff"] = df.apply(lambda row: row[col] - row[other_implied_prob_cols].mean(), axis=1)
    
    return df

def reorder_columns(df):
    # Rename Columns for reordering
    for column in df.columns:
        # if 'point' in column:
        #     new_df = new_df.rename(columns={column: column.replace('point', 'index1_point')})
        if 'price' in column:
            df = df.rename(columns={column: column.replace('price', 'index2_price')})
        if 'decimal_odds' in column:
            df = df.rename(columns={column: column.replace('decimal_odds', 'index3_decimal_odds')})
        if 'implied_prob' in column:
            df = df.rename(columns={column: column.replace('implied_prob', 'index4_implied_prob')})
        if 'dejuice' in column:
            df = df.rename(columns={column: column.replace('dejuice', 'index5_dejuice')})
        if 'diff' in column:
            df = df.rename(columns={column: column.replace('diff', 'index6_diff')})
        # if 'EV' in column:
        #     new_df = new_df.rename(columns={column: column.replace('EV', 'index6_EV')})

    # Select columns in the desired order, sorted by prefix
    df = df[['event_id','game', 'market', 'description', 'name', 'point'] + 
                    sorted([col for col in df.columns if col not in ['game','market', 'description', 'name']], 
                        key=lambda x: (x.split('_')[0], x.split('_')[1:]))]
    
    for column in df.columns:
        # if 'point' in column:
        #     new_df = new_df.rename(columns={column: column.replace('index1_point', 'point')})
        if 'price' in column:
            df = df.rename(columns={column: column.replace('index2_price', 'price')})
        if 'decimal_odds' in column:
            df = df.rename(columns={column: column.replace('index3_decimal_odds', 'decimal_odds')})
        if 'implied_prob' in column:
            df = df.rename(columns={column: column.replace('index4_implied_prob', 'implied_prob')})
        if 'dejuice' in column:
            df = df.rename(columns={column: column.replace('index5_dejuice', 'dejuice')})
        if 'diff' in column:
            df = df.rename(columns={column: column.replace('index6_diff', 'diff')})
        # if 'EV' in column:
        #     new_df = new_df.rename(columns={column: column.replace('index6_EV', 'EV')})

    price_cols = [col for col in df.columns if '_price' in col]
    df['values_populated'] = df[price_cols].notnull().sum(axis=1)

    return df

def process_json(data):
    # Create a list to store the rows of the DataFrame
    rows = get_rows(data)

    # Create the DataFrame
    df = pd.DataFrame(rows)
    
    # Pivot the DataFrame to get one row for each market and description
    new_df = df.pivot_table(index=['market', 'description', 'name', 'point'], aggfunc='first')
    new_df = new_df.reset_index()

    new_df = apply_function(new_df, '_price', '_decimal_odds', american_to_decimal)
    new_df = apply_function(new_df, '_decimal_odds', '_implied_prob', calculate_implied_probability)
    
    # Apply the function to each row in the DataFrame
    new_df['game'] = data['away_team'] + ' @ ' + data['home_team']
    new_df['event_id'] = data['id']

    new_df = add_dejuice(new_df)

    new_df = add_implied_prob_diff(new_df)

    new_df = reorder_columns(new_df)

    return new_df

if __name__ == '__main__':
    # Create an argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--sport', help='The sport to retrieve player props for')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Check if the --sport argument is provided
    if not args.sport:
        print("Please provide a sport using the --sport argument.")

    files, directory = get_files(args.sport)
    columns = []

    dfs = []
    file_num = 0
    for file in files:
        if not file.split('_')[-1].startswith(f'{datetime.now().date().strftime("%Y%m%d")}'):
            continue
        file_num += 1
        print(f"Processing {file}")
        if file.startswith(args.sport):
            # Load the JSON data
            with open(f'{directory}{file}', 'r') as f:
                data = json.load(f)
                df = process_json(data)
                if file_num == 1:
                    columns = ",".join(df.columns)
                else:
                    if ",".join(df.columns) != columns:
                        print(f"Columns don't match for {file}")
                        print(f"Columns in {file}: {', '.join(df.columns)}")
                        print(f"Columns in first file: {columns}")
                        # df = df.reindex(columns=columns.split(','))
                        # dfs.append(df)
                    else:
                        dfs.append(df)

    agg_df = pd.concat(dfs, ignore_index=True)

    agg_df = agg_df.assign(avg_dejuiced_prob=agg_df.filter(like='_dejuice').mean(axis=1))

    # Write to CSV
    agg_df.to_csv(f'..//output//aggregated_csvs//{args.sport}//{args.sport}_player_props_{datetime.now().date().strftime("%Y%m%d")}.csv', index=False)
        