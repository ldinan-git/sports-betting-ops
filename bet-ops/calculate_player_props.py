import argparse
import subprocess
from datetime import datetime
import json
import os

with open('configuration/directories.json') as f:
    directories = json.load(f)

AGGREGATED_CSVS_SCRIPT_LOC =  directories["aggregated_csvs_scripts"]
PLAYER_PROPS_RESPONSES_SCRIPT_LOC = directories["player_props_responses_scripts"]
GAME_ODDS_RESPONSES_SCRIPT_LOC = directories["game_odds_responses_scripts"]
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
    parser.add_argument('--get_player_props', default="false", help='Whether to get odds (true/false)')
    parser.add_argument('--override_date', default=datetime.now().strftime("%Y%m%d"), help='Date to override in YYYYMMDD format')
    parser.add_argument('--values_populated', default="4", help='Number of values populated')
    parser.add_argument('--bets_shown', default="100", help='Number of bets shown')
    parser.add_argument('--update_html', default="false", help='Number of bets shown')
    parser.add_argument('--get_odds', default="false", help='Number of bets shown')


    args = parser.parse_args()
    if args.get_player_props.lower() == "true":
        file_substring = "player_props"
    else:
        file_substring = "odds"

    # Step 1: Generate odds for a given day
    if args.get_player_props.lower() == "true":
        print("Getting player props...")
        run_command(f"python {os.path.join(PLAYER_PROPS_RESPONSES_SCRIPT_LOC, 'get_player_props.py')} --sport {args.sport} --api_key {args.api_key}")

    if args.get_odds.lower() == "true":
        print("Getting odds...")
        run_command(f"python {os.path.join(GAME_ODDS_RESPONSES_SCRIPT_LOC, 'get_game_odds.py')} --sport {args.sport} --api_key {args.api_key}")


    print("Calculating odds CSV...")
    # Step 2: Create Aggregated CSV
    run_command(f"python {os.path.join(AGGREGATED_CSVS_SCRIPT_LOC, 'calculate_odds_csv.py')} --sport {args.sport} --override_date {args.override_date} --file_substring {file_substring}")

    # print("Adding custom functions to columns...")
    # Step 3: Add Custom Functions to columns
    run_command(f"python {os.path.join(AGGREGATED_CSVS_SCRIPT_LOC, 'custom_market_functions.py')} --sport {args.sport} --override_date {args.override_date}")

    print("Getting best bets...")
    # Step 4: Data Analysis
    run_command(f"python {os.path.join(AGGREGATED_CSVS_SCRIPT_LOC, 'best_bets.py')} --sport {args.sport} --values_populated {args.values_populated} --bets_shown {args.bets_shown} --override_date {args.override_date}")

    # Step 5: Create or switch to the branch and push changes to GitHub
    # branch_name = f"{args.sport}_player_props_{args.override_date}"
    # if branch_exists(branch_name):
    #     print(f"Branch '{branch_name}' already exists. Switching to the branch.")
    #     run_command(f"git checkout {branch_name}")
    # else:
    #     print(f"Creating new branch '{branch_name}' and pushing changes to GitHub...")
    #     run_command(f"git checkout -b {branch_name}")

    # Step 5: Update index.html
    if args.update_html.lower() == "true":
        print("Updating index.html...")
        run_command(f"python update_html.py --sport {args.sport} --new_date {args.override_date}")

    print("Changing directory to the parent directory...")
    os.chdir('..')

    # Step 6: Commit to main
    print("Committing changes to main...")
    run_command("git checkout main")
    run_command("git pull origin main")
    run_command("git add .")
    run_command(f'git commit -m "Automated commit for {args.sport} on {args.override_date}"')
    run_command("git push origin main")

    # Step 7: Create a backup branch, commit changes, and push to GitHub
    # backup_branch_name = "main_backup"
    # print(f"Creating backup branch '{backup_branch_name}' and pushing changes to GitHub...")
    # run_command(f"git checkout -b {backup_branch_name}")
    # run_command("git add .")
    # run_command(f'git commit -m "Backup commit for {args.sport} on {args.override_date}"')
    # run_command(f"git push origin {backup_branch_name}")

    # Step 6: Merge the new branch back into main
    # print(f"Merging branch '{branch_name}' back into 'main'...")
    # run_command("git checkout main")
    # run_command(f"git merge {branch_name}")
    # run_command("git push origin main")

    print("Spinning up local web app...")
    # Step 8: Spin up the web app
    run_command(f"python {os.path.join(USER_INTERFACE_SCRIPT_LOC, 'app.py')} --sport {args.sport}")

if __name__ == "__main__":
    main()

# python calculate_player_props.py --sport "basketball_nba" --api_key "your_api_key" --get_odds "true" --override_date "20231015" --file_substring "substring" --values_populated "100" --bets_shown "10"