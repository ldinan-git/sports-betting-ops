import os
import requests
import json
from datetime import datetime
import pytz
import argparse

DEFAULT_OUTPUT_DIR = '../output'

def get_project_root():
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Navigate back to the bet-ops directory
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..', '..'))
    return project_root

ROOT_DIR = get_project_root()

with open(os.path.join(ROOT_DIR, 'configuration/api_parameters.json')) as f:
    config = json.load(f)

with open(os.path.join(ROOT_DIR, 'configuration/directories.json')) as f:
    directories = json.load(f)

def output_response(response, output_dir, file_name, json_flag=False):
    if not json_flag:
        data = response.json()  # Parse JSON response
    else:
        data = response

    print(data)

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Construct file path in the current directory
    file_path = os.path.join(output_dir, f"{file_name}_{str(datetime.now().date()).replace('-', '')}.json")
    
    # Save the response to the file
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)
    print(f"Data saved to {file_path}")

def invoke_request(url, params, file_name, output=False, output_dir=None):
    response = requests.get(url, params=params)
    print("URL: ", url)
    print(f"Response Headers: {response.headers}")

    if output:
        output_dir = output_dir or DEFAULT_OUTPUT_DIR
        output_response(response, output_dir, file_name)
    return response

def sports_endpoint(api_key):
    # API endpoint and your API key
    url = config["sports"]["url"]
    file_name = config["sports"]["prefix"]

    # Define parameters to get all NHL games, including player props, for today
    params = {
        "apiKey": api_key,
        "dateFormat": "iso",
    }

    output_dir = DEFAULT_OUTPUT_DIR + '/sports/'

    # Make the API request
    sports = invoke_request(url, params, file_name, output=True, output_dir=output_dir)
    return sports.json()

def odds_endpoint(sport, api_key):
    # API endpoint and your API key
    url = config["odds"]["url"].replace("{sport_key}", sport)
    print("URL: ", url)
    print("Config: ", config["odds"]["url"])
    file_name = config["odds"]["prefix"].replace("{sport_key}", sport)

    # Define parameters to get all NHL games, including player props, for today
    params = {
        "apiKey": api_key,                 
        "regions": ",".join(config["odds"].get("regions", "us")),  # default to US
        "markets": ",".join(config["odds"].get("markets", "h2h,totals,spreads")),  # default markets for odds
        "oddsFormat": "american",          
        "dateFormat": "iso",           
    }

    # output_dir = DEFAULT_OUTPUT_DIR + f'/{sport}/odds/'
    output_dir = os.path.join(ROOT_DIR, directories['odds_api_responses_output'], sport, 'player_props')

    # Make the API request
    invoke_request(url, params, file_name, output=True, output_dir=output_dir)


def get_game_odds(sport, api_key):
    # Validate sport
    sports = sports_endpoint(api_key)
    
    flag = False
    for s in sports:
        if s["key"] == sport:
            flag = True
    if not flag:
        print("Sport not found")
        return
    
    # Get Player Props
    odds_endpoint(sport, api_key)

if __name__ == '__main__':
    # Create an argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--sport', help='The sport to retrieve player props for')
    parser.add_argument('--api_key', help='API Key to use for requests')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Check if the --sport argument is provided
    if not args.sport:
        print("Please provide a sport using the --sport argument.")

    if not args.api_key:
        print("Please provide an API Key using the --api_key argument.")

    get_game_odds(sport=args.sport, api_key=args.api_key)
