import argparse
import pandas as pd
import numpy as np
from datetime import datetime
from helper_functions import *  
import json

def adjust_dejuice_icehockey_nhl_atgs(df):
    implied_prob_cols = [col for col in df.columns if '_implied_prob' in col and '_implied_prob_diff' not in col]
    dejuice_cols = [col for col in df.columns if '_dejuice' in col]

    for col in dejuice_cols:
        scaling_factor = 4.5
        df.loc[df['market'] == 'player_goal_scorer_anytime', col] *= scaling_factor
                
    return df

def consolidate_player_goals(df):
    # Identify rows to consolidate
    goals_mask = (df['market'] == 'player_goals') & (df['point'] == 0.5)
    anytime_mask = (df['market'] == 'player_goal_scorer_anytime') & (df['point'] == '')

    # Merge the two sets of rows
    merged_df = df[goals_mask].merge(df[anytime_mask], on=['event_id', 'game', 'description'], suffixes=('_goals', '_anytime'))

    # Update the anytime rows with values from the goals rows if they are empty
    for col in df.columns:
        if col not in ['event_id', 'game', 'description', 'market', 'point']:
            merged_df[col + '_anytime'] = merged_df[col + '_anytime'].combine_first(merged_df[col + '_goals'])

    # Drop the goals columns and rename the anytime columns
    merged_df = merged_df[[col for col in merged_df.columns if '_anytime' in col or col in ['event_id', 'game', 'description']]]
    merged_df.columns = [col.replace('_anytime', '') for col in merged_df.columns]

    # Combine the updated anytime rows with the original DataFrame, excluding the original anytime rows
    df = pd.concat([df[~anytime_mask], merged_df], ignore_index=True)

    return df


if __name__ == "__main__":
    # Create an argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--sport', help='The sport to retrieve player props for')

    args = parser.parse_args()

    agg_df = pd.read_csv(f'..//output//aggregated_csvs//{args.sport}//{args.sport}_player_props_{datetime.now().date().strftime("%Y%m%d")}.csv')
    
    if args.sport == 'icehockey_nhl':
        agg_df = consolidate_player_goals(agg_df)

    agg_df.to_csv(f'..//output//aggregated_csvs//{args.sport}//{args.sport}_player_props_{datetime.now().date().strftime("%Y%m%d")}.csv', index=False)
    