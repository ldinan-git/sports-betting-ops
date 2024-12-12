import argparse
import pandas as pd
import numpy as np
from datetime import datetime
from helper_functions import *
import os
import json

def get_project_root():
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Navigate back to the bet-ops directory
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
    return project_root

ROOT_DIR = get_project_root()

with open(os.path.join(ROOT_DIR, 'configuration/directories.json')) as f:
    directories = json.load(f)

def get_values_list(df, column_substring, bets_shown=100, sort='lowest'):
    """
    Return a list of the lowest (or highest) values from the columns of `df` that contain `column_substring`,
    filtered to only include rows where `values_populated` is greater than or equal to `values_populated`.

    Parameters
    ----------
    df : pandas.DataFrame
        The dataframe to retrieve the values from
    column_substring : str
        The substring to filter columns by
    count : int, optional
        The number of values to return (default is 100)
    sort : str, optional
        The direction to sort the differences in (default is 'lowest'). If 'lowest', returns the lowest values, if 'highest', returns the highest values, otherwise returns all values

    Returns
    -------
    list
        A list of the lowest (or highest) values
    """
    diff_cols = [col for col in df.columns if column_substring in col]
    all_diffs = df[diff_cols].values.flatten()

    if sort == 'lowest':
        diffs = np.sort(all_diffs)[:bets_shown]
    elif sort == 'highest':
        diffs = np.sort(all_diffs)[-bets_shown:]
    else:
        diffs = all_diffs
    
    return diffs, diff_cols

def get_best_player_props(df, sport, values_populated, bets_shown, date):
    diffs, diff_cols = get_values_list(df, 'diff', bets_shown=bets_shown, sort='lowest')
    df = df[df['values_populated'] >= values_populated]

    rows = []
    for diff in diffs:
        for col in diff_cols:
            row_idx = np.where(df[col].values == diff)
            if len(row_idx[0]) > 0:
                row = df.iloc[row_idx[0]][['game', 'market', 'description', 'name', 'point'] + [c for c in df.columns if '_price' in c] + ['avg_dejuiced_prob', f'{col.split("_")[0]}_decimal_odds']].values.tolist()[0]
                row.insert(0, col.split('_')[0])  # insert the value book in the first column
                rows.append(row)

    # Create the DataFrame with initial column order
    df = pd.DataFrame(rows, columns=['value_book', 'game', 'market', 'name', 'description', 'point'] + [c for c in df.columns if '_price' in c] + ['avg_dejuiced_prob', 'book_decimal_odds'])

    # Add the `value_book_price` column
    df['value_book_price'] = df.apply(lambda row: row[f"{row['value_book']}_price"] if f"{row['value_book']}_price" in df.columns else None, axis=1)

    # Calculate EV
    df['EV'] = calculate_ev(df['avg_dejuiced_prob'], df['book_decimal_odds']) - calculate_ev(df['avg_dejuiced_prob'], prob_to_decimal(df['avg_dejuiced_prob']))

    # Reorder columns to put `value_book_price` in the second column
    column_order = ['value_book', 'value_book_price', 'EV'] + [col for col in df.columns if col not in ['value_book', 'value_book_price', 'EV']]
    df = df[column_order]

    # Drop duplicates and save the CSV
    df = df.drop_duplicates()
    
    output_dir = os.path.join(ROOT_DIR, directories["best_player_props_output"], sport)
    df.to_csv(f'{output_dir}//{sport}_best_player_props_{date}.csv', index=False)


if __name__ == "__main__":
    # Create an argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--sport', help='The sport to retrieve player props for')
    parser.add_argument('--values_populated', help='The minimum values to include in best bets')
    parser.add_argument('--bets_shown', help='The number of unique best bets to return')
    parser.add_argument('--override_date', help='Calculate odds for date other than today')

    args = parser.parse_args()

    if args.override_date:
        date = args.override_date
    else:
        date = datetime.now().date().strftime("%Y%m%d")

    args.values_populated = int(args.values_populated) if args.values_populated else 0
    args.bets_shown = int(args.bets_shown) if args.bets_shown else 100

    file_dir = os.path.join(ROOT_DIR, directories["aggregated_csvs_output"], args.sport)
    agg_df = pd.read_csv(f'{file_dir}//{args.sport}_player_props_{date}.csv')
    agg_df = agg_df.loc[:, ~agg_df.columns.str.contains('williamhill')] 
    get_best_player_props(agg_df, args.sport, args.values_populated, args.bets_shown, date)