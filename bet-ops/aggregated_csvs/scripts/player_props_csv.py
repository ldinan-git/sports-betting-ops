import pandas as pd
import json
import numpy as np
from datetime import datetime
import argparse
import os

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
    
def prob_to_decimal(prob):
    return 1 / prob
    
# Define a function to calculate implied probability
def calculate_implied_probability(decimal_odds):
    return 1 / decimal_odds

# Define a function to calculate projected odds
def calculate_projected_odds(actual_odds, implied_probability):
    return (actual_odds * (1 - implied_probability)) / (1 - (implied_probability * (1 - (actual_odds / (actual_odds + 100)))))

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
            denom = new_df.loc[(new_df['game'] == game) & (new_df['market'] == market) & (new_df['point'] == point), bookmaker].sum()
            dejuice = row[bookmaker] / denom
            dejuice_values[bookmaker.replace('_implied_prob', '_dejuice')] = dejuice

    return pd.Series(dejuice_values)

def calculate_ev(true_prob, implied_prob):
    return (true_prob - implied_prob) * (1 - true_prob)

def calculate_ev(true_prob, decimal_odds):
    return (true_prob * decimal_odds) - (1 - true_prob)

def get_files(sport):
    directory = f"C:\\Users\\ldinan\\Documents\\GitHub\\sports-betting-ops\\bet-ops\\odds_api_responses\\output\\{sport}\\player_props\\"
    files = os.listdir(directory)
    return files, directory

def update_dejuice_for_anytime_goalscorer(row):
    bookmakers = [col for col in row.index if '_dejuice' in col]
    for bookmaker in bookmakers:
        if 'goal_scorer_anytime' in row['market']:
            row[bookmaker] = 1 - ((1 - row[bookmaker]) ** 3.5)
    return row

def process_json(data):
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
    print("Columns Before Pivot: ", df.columns)
    # Pivot the DataFrame to get one row for each market and description
    new_df = df.pivot_table(index=['market', 'description', 'name', 'point'], aggfunc='first')
    print("Columns After Pivot: ", new_df.columns)
    new_df = new_df.reset_index()

    # Apply the function to each bookmaker's odds
    for bookmaker in new_df.columns:
        if '_price' in bookmaker:
            new_df[f"{bookmaker.replace('_price', '_decimal_odds')}"] = new_df[bookmaker].apply(american_to_decimal)

    # Apply the function to each bookmaker's decimal odds
    for bookmaker in new_df.columns:
        if '_decimal_odds' in bookmaker:
            new_df[f"{bookmaker.replace('_decimal_odds', '_implied_prob')}"] = new_df[bookmaker].apply(calculate_implied_probability)

    # Apply the function to each row in the DataFrame
    new_df['game'] = data['away_team'] + ' @ ' + data['home_team']
    new_df['event_id'] = data['id']
    dejuice_df = new_df.apply(calculate_dejuice, args=(new_df,), axis=1)

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
    new_df = new_df[['event_id','game', 'market', 'description', 'name', 'point'] + 
                    sorted([col for col in new_df.columns if col not in ['game','market', 'description', 'name']], 
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

    # agg_df = agg_df.apply(update_dejuice_for_anytime_goalscorer, axis=1)

    # Write to CSV
    agg_df.to_csv(f'C://Users//ldinan//Documents//GitHub//sports-betting-ops//bet-ops//aggregated_csvs//output//aggregated_csvs//{args.sport}//{args.sport}_player_props_{datetime.now().date().strftime("%Y%m%d")}', index=False)

    agg_df_filtered = agg_df[agg_df['values_populated'] >= 4]
    diff_cols = [col for col in agg_df_filtered.columns if '_diff' in col]
    all_diffs = agg_df_filtered[diff_cols].values.flatten()
    diffs = np.sort(all_diffs)[:50]

    rows = []
    for diff in diffs:
        for col in diff_cols:
            row_idx = np.where(agg_df_filtered[col].values == diff)
            if len(row_idx[0]) > 0:
                row = agg_df_filtered.iloc[row_idx[0]][['event_id', 'game', 'market', 'description', 'name', 'point'] + [c for c in agg_df_filtered.columns if '_price' in c] + ['avg_dejuiced_prob', f'{col.split('_')[0]}_decimal_odds']].values.tolist()[0]
                row.insert(0, col.split('_')[0])  # insert the value book in the first column
                rows.append(row)

    df = pd.DataFrame(rows, columns=['value_book', 'event_id', 'event_id_dummy', 'game', 'market', 'name', 'description', 'point', 'point_dummy'] + [c for c in agg_df_filtered.columns if '_price' in c] + ['avg_dejuiced_prob', 'book_decimal_odds'])
    df = df.drop(['point_dummy'], axis=1)
    df = df.drop(['event_id_dummy'], axis=1)
    # df['decimal_odds'] = agg_df[f'{df['value_book']}_decimal_odds']
    df['EV'] = calculate_ev(df['avg_dejuiced_prob'], df['book_decimal_odds']) - calculate_ev(df['avg_dejuiced_prob'], prob_to_decimal(df['avg_dejuiced_prob']))

    df.to_csv(f'../../aggregated_csvs/output/best_player_props/{args.sport}_best_player_props_{datetime.now().date().strftime("%Y%m%d")}', index=False)

        