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

if __name__ == "__main__":
    # Create an argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--sport', help='The sport to retrieve player props for')

    args = parser.parse_args()

    agg_df = pd.read_csv(f'..//output//aggregated_csvs//{args.sport}//{args.sport}_player_props_{datetime.now().date().strftime("%Y%m%d")}.csv')
    
    agg_df.to_csv(f'..//output//aggregated_csvs//{args.sport}//{args.sport}_player_props_{datetime.now().date().strftime("%Y%m%d")}.csv', index=False)
    