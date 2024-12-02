import argparse
import subprocess
from datetime import datetime
import json
import os

with open('configuration/directories.json') as f:
    directories = json.load(f)

AGGREGATED_CSVS_SCRIPT_LOC =  directories["aggregated_csvs_scripts"]
ODDS_API_RESPONSES_SCRIPT_LOC = directories["odds_api_responses_scripts"]
USER_INTERFACE_SCRIPT_LOC = directories["user_interface_scripts"]

def run_command(command):
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"Command failed: {command}")
        exit(result.returncode)

def branch_exists(branch_name):
    result = subprocess.run(f"git branch --list {branch_name}", shell=True, capture_output=True, text=True)
    return branch_name in result.stdout

def main():
    parser = argparse.ArgumentParser(description="Calculate player props.")
    parser.add_argument('--sport', required=True, help='The sport to retrieve player props for')
    parser.add_argument('--api_key', default="", help='API key for retrieving player props')
    parser.add_argument('--get_odds', default="false", help='Whether to get odds (true/false)')
    parser.add_argument('--override_date', default=datetime.now().strftime("%Y%m%d"), help='Date to override in YYYYMMDD format')
    parser.add_argument('--values_populated', default="4", help='Number of values populated')
    parser.add_argument('--bets_shown', default="100", help='Number of bets shown')

    args = parser.parse_args()
    file_substring = "player_props"

    # Step 1: Generate odds for a given day
    print("Getting player props...")
    if args.get_odds.lower() == "true":
        run_command(f"python {os.path.join(ODDS_API_RESPONSES_SCRIPT_LOC, 'get_player_props.py')} --sport {args.sport} --api_key {args.api_key}")

    print("Calculating odds CSV...")
    # Step 2: Create Aggregated CSV
    run_command(f"python {os.path.join(AGGREGATED_CSVS_SCRIPT_LOC, 'calculate_odds_csv.py')} --sport {args.sport} --override_date {args.override_date} --file_substring {file_substring}")

    # print("Adding custom functions to columns...")
    # # Step 3: Add Custom Functions to columns
    # run_command(f"python {os.path.join(AGGREGATED_CSVS_SCRIPT_LOC, 'custom_market_functions.py')} --sport {args.sport}")

    print("Getting best bets...")
    # Step 4: Data Analysis
    run_command(f"python {os.path.join(AGGREGATED_CSVS_SCRIPT_LOC, 'best_bets.py')} --sport {args.sport} --values_populated {args.values_populated} --bets_shown {args.bets_shown} --override_date {args.override_date}")

    # Step 5: Create or switch to the branch and push changes to GitHub
    branch_name = f"{args.override_date}_player_props"
    if branch_exists(branch_name):
        print(f"Branch '{branch_name}' already exists. Switching to the branch.")
        run_command(f"git checkout {branch_name}")
    else:
        print(f"Creating new branch '{branch_name}' and pushing changes to GitHub...")
        run_command(f"git checkout -b {branch_name}")

    # Always add, commit, and push changes
    run_command("git add .")
    run_command(f'git commit -m "Automated commit for branch {branch_name}"')
    run_command(f"git push origin {branch_name}")
    
    print("Spinning up web app...")
    # Step 6: Spin up the web app
    run_command(f"python {os.path.join(USER_INTERFACE_SCRIPT_LOC, 'app.py')} --sport {args.sport}")

if __name__ == "__main__":
    main()

# python calculate_player_props.py --sport "basketball_nba" --api_key "your_api_key" --get_odds "true" --override_date "20231015" --file_substring "substring" --values_populated "100" --bets_shown "10"