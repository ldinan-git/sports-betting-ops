import argparse
import pandas as pd
import numpy as np
from datetime import datetime
from helper_functions import *  
import json
import os

def get_project_root():
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Navigate back to the bet-ops directory
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
    return project_root

ROOT_DIR = get_project_root()

with open(os.path.join(ROOT_DIR, 'configuration/directories.json')) as f:
    directories = json.load(f)

def adjust_dejuice_icehockey_nhl_atgs(df):
    implied_prob_cols = [col for col in df.columns if '_implied_prob' in col and '_implied_prob_diff' not in col]
    dejuice_cols = [col for col in df.columns if '_dejuice' in col]

    for col in dejuice_cols:
        scaling_factor = 4.5
        df.loc[df['market'] == 'player_goal_scorer_anytime', col] *= scaling_factor
                
    return df

def consolidate_player_goals(df):
    # Iterate through the DataFrame
    for idx, row in df.iterrows():
        if row['market'] == 'player_goal_scorer_anytime' and row['name'] == 'Yes':
            # Find the corresponding player_goals row
            matching_row = df[(df['event_id'] == row['event_id']) &
                              (df['game'] == row['game']) &
                              (df['description'] == row['description']) &
                              (df['market'] == 'player_goals') &
                              (df['point'] == 0.5) &
                              (df['name'] == 'Over')]
            if not matching_row.empty:
                matching_row = matching_row.iloc[0]
                # Update the current row with values from the matching row if they are empty
                for col in df.columns:
                    if col not in ['event_id', 'game', 'description', 'market', 'point', 'name'] and pd.isna(row[col]):
                        df.at[idx, col] = matching_row[col]

    return df


if __name__ == "__main__":
    # Create an argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--sport', help='The sport to retrieve player props for')
    parser.add_argument('--override_date', help='Calculate odds for date other than today')

    args = parser.parse_args()

    if args.override_date:
        date = args.override_date
    else:
        date = datetime.now().date().strftime("%Y%m%d")

    file_path = os.path.join(ROOT_DIR, directories["aggregated_csvs_output"], args.sport)
    agg_df = pd.read_csv(f'{file_path}//{args.sport}_player_props_{date}.csv')
    
    if args.sport == 'icehockey_nhl':
        agg_df = consolidate_player_goals(agg_df)

    agg_df.to_csv(f'{file_path}//{args.sport}_player_props_{date}.csv', index=False)
    