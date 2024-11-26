import pandas as pd
import json
import numpy as np
from datetime import datetime
import argparse

# Define a function to calculate implied probability
def calculate_implied_probability(odds):
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)

# Define a function to convert American odds to decimal odds
def american_to_decimal(odds):
    if odds > 0:
        return odds / 100 + 1
    else:
        return 100 / abs(odds) + 1
    
# Define a function to calculate implied probability
def calculate_implied_probability(decimal_odds):
    return 1 / decimal_odds

# Define a function to calculate projected odds
def calculate_projected_odds(actual_odds, implied_probability):
    return (actual_odds * (1 - implied_probability)) / (1 - (implied_probability * (1 - (actual_odds / (actual_odds + 100)))))

# Define a function to calculate dejuice
def calculate_dejuice(row):
    market = row['market']
    description = row['description']
    bookmakers = [col for col in row.index if '_implied_prob' in col]
    dejuice_values = {}
    for bookmaker in bookmakers:
        total_odds = sum(new_df.loc[(new_df['market'] == market) & (new_df['description'] == description), bookmaker])
        dejuice = row[bookmaker] / total_odds
        dejuice_values[bookmaker.replace('_implied_prob', '_dejuice')] = dejuice
    return pd.Series(dejuice_values)

def calculate_ev(true_prob, decimal_odds):
    return (true_prob - decimal_odds) * (1 - true_prob)

if __name__ == '__main__':
    # Create an argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--sport', help='The sport to retrieve player props for')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Check if the --sport argument is provided
    if not args.sport:
        print("Please provide a sport using the --sport argument.")

    # Load the JSON data
    with open('../odds_api_responses/icehockey_nhl_Boston Bruins_Vancouver Canucks_player_props_20241126.json') as f:
        data = json.load(f)

    # Create a list to store the rows of the DataFrame
    rows = []

    bookmakers = []
    points = []

    for bookmaker in data['bookmakers']:
        bookmakers.append(bookmaker['key'])
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
                points.append(outcome.get('point', ''))

    # Create the DataFrame
    df = pd.DataFrame(rows)

    # Pivot the DataFrame to get one row for each market and description
    new_df = df.pivot_table(index=['market', 'description', 'name', 'point'], aggfunc='first').reset_index()

    # Apply the function to each bookmaker's odds
    for bookmaker in new_df.columns:
        if '_price' in bookmaker:
            new_df[f"{bookmaker.replace('_price', '_decimal_odds')}"] = new_df[bookmaker].apply(american_to_decimal)

    # Apply the function to each bookmaker's decimal odds
    for bookmaker in new_df.columns:
        if '_decimal_odds' in bookmaker:
            new_df[f"{bookmaker.replace('_decimal_odds', '_implied_prob')}"] = new_df[bookmaker].apply(calculate_implied_probability)

    # Apply the function to each row in the DataFrame
    dejuice_df = new_df.apply(calculate_dejuice, axis=1)

    print(dejuice_df.columns)

    # Add dejuice values to the original DataFrame
    new_df = pd.concat([new_df, dejuice_df], axis=1)

    implied_prob_cols = [col for col in new_df.columns if '_implied_prob' in col]
    for col in implied_prob_cols:
        other_implied_prob_cols = [c for c in implied_prob_cols if c != col]
        new_df[f"{col}_diff"] = new_df.apply(lambda row: row[col] - row[other_implied_prob_cols].mean(), axis=1)

    # dejuice_cols = [col for col in new_df.columns if '_dejuice' in col]
    # for col in dejuice_cols:
    #     new_df[f"{col}_EV"] = new_df.apply(lambda row: calculate_ev(row[col], row[col.replace('_dejuice', '_decimal_odds')]), axis=1)

    # Rename Columns for reordering
    for column in new_df.columns:
        # if 'point' in column:
        #     new_df = new_df.rename(columns={column: column.replace('point', 'index1_point')})
        if 'price' in column:
            new_df = new_df.rename(columns={column: column.replace('price', 'index2_price')})
        if 'decimal_odds' in column:
            new_df = new_df.rename(columns={column: column.replace('decimal_odds', 'index3_decimal_odds')})
        if 'implied_prob' in column:
            new_df = new_df.rename(columns={column: column.replace('implied_prob', 'index4_implied_prob')})
        if 'dejuice' in column:
            new_df = new_df.rename(columns={column: column.replace('dejuice', 'index5_dejuice')})
        if 'diff' in column:
            new_df = new_df.rename(columns={column: column.replace('diff', 'index6_diff')})
        # if 'EV' in column:
        #     new_df = new_df.rename(columns={column: column.replace('EV', 'index6_EV')})

    # Select columns in the desired order, sorted by prefix
    new_df = new_df[['market', 'description', 'name', 'point'] + 
                    sorted([col for col in new_df.columns if col not in ['market', 'description', 'name']], 
                        key=lambda x: (x.split('_')[0], x.split('_')[1:]))]
    
    for column in new_df.columns:
        # if 'point' in column:
        #     new_df = new_df.rename(columns={column: column.replace('index1_point', 'point')})
        if 'price' in column:
            new_df = new_df.rename(columns={column: column.replace('index2_price', 'price')})
        if 'decimal_odds' in column:
            new_df = new_df.rename(columns={column: column.replace('index3_decimal_odds', 'decimal_odds')})
        if 'implied_prob' in column:
            new_df = new_df.rename(columns={column: column.replace('index4_implied_prob', 'implied_prob')})
        if 'dejuice' in column:
            new_df = new_df.rename(columns={column: column.replace('index5_dejuice', 'dejuice')})
        if 'diff' in column:
            new_df = new_df.rename(columns={column: column.replace('index6_diff', 'diff')})
        # if 'EV' in column:
        #     new_df = new_df.rename(columns={column: column.replace('index6_EV', 'EV')})

    price_cols = [col for col in new_df.columns if '_price' in col]
    new_df['values_populated'] = new_df[price_cols].notnull().sum(axis=1)
    
    # Write to CSV
    new_df.to_csv('../aggregated_csvs/player_props_20241119-v2.csv', index=False)

    new_df_filtered = new_df[new_df['values_populated'] >= 4]
    diff_cols = [col for col in new_df.columns if '_diff' in col]
    all_diffs = new_df_filtered[diff_cols].values.flatten()
    top_5_diffs = np.sort(all_diffs)[:10]

    rows = []
    for diff in top_5_diffs:
        for col in diff_cols:
            row_idx = np.where(new_df[col].values == diff)
            if len(row_idx[0]) > 0:
                row = new_df.iloc[row_idx[0]][['market', 'description', 'name', 'point'] + [c for c in new_df.columns if '_price' in c]].values.tolist()[0]
                row.insert(0, col.split('_')[0])  # insert the column name at the beginning of the row
                rows.append(row)

    df = pd.DataFrame(rows, columns=['index', 'column_name', 'market', 'description', 'name', 'point'] + [c for c in new_df.columns if '_price' in c])

    
    df.to_csv(f'../aggregated_csvs/best_player_props_{str(datetime.now().date()).replace('-', '')}.csv', index=False)
        
        