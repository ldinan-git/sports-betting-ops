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
    description = row.get('description', '')
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

def get_files(sport, date):
    player_props_directory = os.path.join("..", "..", "odds_api_responses", "player_props", "output", sport, "player_props")
    odds_directory = os.path.join("..", "..", "odds_api_responses", "game_odds", "output", sport, "odds")
    
    player_props_files = [os.path.join(player_props_directory, f) for f in os.listdir(player_props_directory) if os.path.isfile(os.path.join(player_props_directory, f)) and f.split('_')[-1].startswith(f'{date}')]
    odds_files = [os.path.join(odds_directory, f) for f in os.listdir(odds_directory) if os.path.isfile(os.path.join(odds_directory, f)) and f.split('_')[-1].startswith(f'{date}')]
    
    return player_props_files + odds_files


def get_rows_object(data):
    # Create a list to store the rows of the DataFrame
    rows = []

    for bookmaker in data['bookmakers']:
        for market in bookmaker['markets']:
            for outcome in market['outcomes']:
                row = {
                    'event_id': data['id'],
                    'game': data['away_team'] + ' @ ' + data['home_team'],
                    'market': market['key'],
                    'description': outcome.get('description', ''),
                    'name': outcome['name'],
                    'point': outcome.get('point', ''),
                    f"{bookmaker['key']}_price": outcome['price'],
                    # f"{bookmaker['key']}_point": outcome.get('point', ''),
                    f"{bookmaker['key']}_name": outcome['name']
                }
                rows.append(row)
    
    return rows

def get_rows_list(data):
    rows = []
    for obj in data:
        rows = get_rows_object(obj)
        rows.extend(rows)
    
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
    if type(data) == list:
        rows = get_rows_list(data)
    else:
        rows = get_rows_object(data)

    # Create the DataFrame
    df = pd.DataFrame(rows)
    df = df.drop([col for col in df.columns if col.startswith('betrivers_')], axis=1)
    
    # Pivot the DataFrame to get one row for each market and description
    new_df = df.pivot_table(index=['event_id', 'game', 'market', 'description', 'name', 'point'], aggfunc='first')
    new_df = new_df.reset_index()

    new_df = apply_function(new_df, '_price', '_decimal_odds', american_to_decimal)
    new_df = apply_function(new_df, '_decimal_odds', '_implied_prob', calculate_implied_probability)
    
    # Apply the function to each row in the DataFrame
    # new_df['game'] = data['away_team'] + ' @ ' + data['home_team']
    # new_df['event_id'] = data['id']

    new_df = add_dejuice(new_df)

    new_df = add_implied_prob_diff(new_df)

    return new_df

if __name__ == '__main__':
    # Create an argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--sport', help='The sport to retrieve player props for')
    parser.add_argument('--override_date', help='Calculate odds for date other than today')
    parser.add_argument('--file_substring', help='Filter files to only include those with this substring')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Check if the --sport argument is provided
    if not args.sport:
        print("Please provide a sport using the --sport argument.")
        exit(1)

    if args.override_date:
        date = args.override_date
    else:
        date = datetime.now().date().strftime("%Y%m%d")

    # if not provided, always return True for ''
    if args.file_substring:
        file_substring = args.file_substring
    else:
        file_substring = ''

    files = get_files(args.sport, date)
    print(files)
    columns = []

    dfs = []
    for file in files:
        print(f"Processing {file}")
        if args.sport in file and date in file and file_substring in file:
            # Load the JSON data
            with open(file, 'r') as f:
                data = json.load(f)
                df = process_json(data)
                if len(dfs) == 0:
                    dfs.append(df)
                # Add empty columns that don't exist to concatenate DataFrames
                else:
                    first_columns = set(dfs[0].columns)
                    second_columns = set(df.columns)

                    only_in_first = first_columns - second_columns
                    only_in_second = second_columns - first_columns

                    print("Columns only in the first file:", only_in_first)
                    print("Columns only in the second file:", only_in_second)

                    # Ensure columns are unique before reindexing
                    union_columns = list(first_columns.union(second_columns))

                    # Remove duplicate columns from the DataFrame
                    dfs = [df.loc[:, ~df.columns.duplicated()].reindex(columns=union_columns) for df in dfs]
                    df = df.loc[:, ~df.columns.duplicated()].reindex(columns=union_columns)

                    dfs.append(df)

    agg_df = pd.concat(dfs, ignore_index=True)

    agg_df = reorder_columns(agg_df)

    agg_df = agg_df.assign(avg_dejuiced_prob=agg_df.filter(like='_dejuice').mean(axis=1))

    # Write to CSV
    agg_df.to_csv(f'..//output//aggregated_csvs//{args.sport}//{args.sport}_player_props_{date}.csv', index=False)
        