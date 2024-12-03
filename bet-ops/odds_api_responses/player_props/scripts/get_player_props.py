import os
import requests
import json
from datetime import datetime
import pytz
import argparse

# DEFAULT_API_KEY = "54179d2c087ee252467b2620fb5bb27b"
# DEFAULT_API_KEY = "1af942a5b7e7b90454f211cb6a697184"

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
    
    # Construct file path in the current directory
    file_path = os.path.join(output_dir, f"{file_name}_{str(datetime.now().date()).replace('-', '')}.json")
    
    # Save the response to the file
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)
    print(f"Data saved to {file_path}")

def invoke_request(url, params, file_name, output=False, output_dir=None):
    response = requests.get(url, params=params)

    print(f"Response Headers: {response.headers}")

    if output:
        output_dir = output_dir or DEFAULT_OUTPUT_DIR
        output_response(response, output_dir, file_name)
    return response

def sports_endpoint(api_key, output=True):
    # API endpoint and your API key
    url = config["sports"]["url"]
    file_name = config["sports"]["prefix"]

    # Define parameters to get all NHL games, including player props, for today
    params = {
        "apiKey": api_key,
        "dateFormat": "iso",
    }

    if output:
        output_dir = output_dir = os.path.join(ROOT_DIR, directories['odds_api_responses_output'], 'sports')

    # Make the API request
    sports = invoke_request(url, params, file_name, output=True, output_dir=output_dir)
    return sports.json()

def events_endpoint(sport, api_key, output=False):
    # get events
    url = config["events"]["url"].replace("{sport_key}", sport)
    file_name = config["events"]["prefix"].replace("{sport_key}", sport)

    # Define parameters to get all NHL games, including player props, for today
    params = {
        "apiKey": api_key,
        "dateFormat": "iso",
    }

    output_dir = os.path.join(ROOT_DIR, directories['odds_api_responses_output'], sport, 'player_props')

    # Make the API request
    events = invoke_request(url, params=params, file_name=file_name, output=output)

    return events.json()

def player_props_endpoint(sport, events, api_key, count):
    i = 0
    for event in events:
        # for region in config["player_props"][sport].get("regions", "us"):
        i += 1
        if i > count:
            continue
        # get player props
        url = config["player_props"][sport]["url"].replace("{sport_key}", sport).replace("{event_id}", event["id"])
        file_name = config["player_props"][sport]["prefix"].replace("{sport_key}", sport).replace("{home_team}", event["home_team"]).replace("{away_team}", event["away_team"]) 

        # Define parameters to get all NHL games, including player props, for today
        params = {
            "apiKey": api_key,
            "regions": ",".join(config["player_props"][sport].get("regions", "us")),  # default to US
            "markets": ",".join(config["player_props"][sport]["markets"]),  # default to US
            "dateFormat": "iso",
            "oddsFormat": "american"
        }

        print("Params: ", params)
        print("URL: ", url)

        print("Events: ", event["id"])
        print("Regions: ", config["player_props"][sport].get("regions", "us"))

        output_dir = os.path.join(ROOT_DIR, directories['odds_api_responses_output'], sport, 'player_props')

        # Make the API request
        invoke_request(url, params=params, file_name=file_name, output=True, output_dir=output_dir)

def get_player_props(sport, api_key):
    # Validate sport
    print(sport)
    sports = sports_endpoint(api_key)
    
    flag = False
    for s in sports:
        if s["key"] == sport:
            flag = True
    if not flag:
        print("Sport not found")
        return

    # Get Events for sport
    events = events_endpoint(sport, api_key)
    events = add_events_date(events)
    output_dir = os.path.join(ROOT_DIR, directories['odds_api_responses_output'], sport, 'events')
    file_name = config["events"]["prefix"].replace("{sport_key}", sport)
    
    output_response(events, output_dir, file_name, json_flag=True)

    # Get Player Props
    player_props_endpoint(sport, events, api_key, count=300)

def add_events_date(events):
    for event in events:
        # event['commence_time'] ="2024-12-25T17:00:00Z"
        utc_time = datetime.strptime(event['commence_time'], '%Y-%m-%dT%H:%M:%SZ')
        utc_time = utc_time.replace(tzinfo=pytz.UTC)
        eastern = pytz.timezone('US/Eastern')
        est_time = utc_time.astimezone(eastern)
        est_date = est_time.strftime('%Y%m%d')

        event['date'] = est_date

    e = []
    for event in events:
        if event['date'] == datetime.now().strftime('%Y%m%d'):
            e.append(event)
    
    return e

# Outputs JSON responses to odds_api_responses/output
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

    get_player_props(sport=args.sport, api_key=args.api_key)
