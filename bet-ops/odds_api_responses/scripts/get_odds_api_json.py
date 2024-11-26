import os
import requests
import json
from datetime import datetime, timedelta
import pytz

DEFAULT_OUTPUT_DIR = '../output'
DEFAULT_API_KEY = "54179d2c087ee252467b2620fb5bb27b"
with open('../../configuration/api_parameters.json') as f:
    config = json.load(f)

def output_response(response, output_dir, file_name):
    # Check if the response is successful
    if response.status_code == 200:
        data = response.json()  # Parse JSON response

        print(data)
        
        # Construct file path in the current directory
        file_path = os.path.join(output_dir, f"{file_name}_{str(datetime.now().date()).replace('-', '')}.json")
        
        # Save the response to the file
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
        print(f"Data saved to {file_path}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def invoke_request(url, params, file_name, output=False, output_dir=None):
    response = requests.get(url, params=params)

    if output:
        output_dir = output_dir or DEFAULT_OUTPUT_DIR
        output_response(response, output_dir, file_name)
    return response

def sports_endpoint():
    # API endpoint and your API key
    url = config["sports"]["url"]
    api_key = ""
    file_name = config["sports"]["prefix"]

    # Define parameters to get all NHL games, including player props, for today
    params = {
        "apiKey": api_key or DEFAULT_API_KEY,
        "dateFormat": "iso",
    }

    output_dir = DEFAULT_OUTPUT_DIR + '/sports/'

    # Make the API request
    sports = invoke_request(url, params, file_name, output=True, output_dir=output_dir)
    return sports.json()

def events_endpoint(sport):
    # get events
    url = config["events"]["url"].replace("{sport_key}", sport)
    api_key = ""
    file_name = config["events"]["prefix"].replace("{sport_key}", sport)

    # Define parameters to get all NHL games, including player props, for today
    params = {
        "apiKey": api_key or DEFAULT_API_KEY,
        "dateFormat": "iso",
    }

    output_dir = DEFAULT_OUTPUT_DIR + f'/{sport}/events/'
    # Make the API request
    events = invoke_request(url, params=params, file_name=file_name, output=True, output_dir=output_dir)

    return events.json()

def odds_endpoint(sport):
    # API endpoint and your API key
    url = config["odds"]["url"]
    api_key = ""
    file_name = config["odds"]["prefix"].replace("{sport_key}", sport)

    # Define parameters to get all NHL games, including player props, for today
    params = {
        "apiKey": api_key or DEFAULT_API_KEY,                 
        "regions": ",".join(config["odds"].get("regions", "us")),  # default to US
        "markets": ",".join(config["odds"].get("markets", "h2h,totals,spreads")),  # default markets for odds
        "oddsFormat": "american",          
        "dateFormat": "iso",           
    }

    output_dir = DEFAULT_OUTPUT_DIR + f'/{sport}/odds/'

    # Make the API request
    invoke_request(url, params, file_name, output=True, output_dir=output_dir)

def player_props_endpoint(sport, events):
    event = events[1]
    # get player props
    url = config["player_props"][sport]["url"].replace("{sport_key}", sport).replace("{event_id}", event["id"])
    api_key = ""
    file_name = config["player_props"][sport]["prefix"].replace("{sport_key}", sport).replace("{home_team}", event["home_team"]).replace("{away_team}", event["away_team"])

    # Define parameters to get all NHL games, including player props, for today
    params = {
        "apiKey": api_key or DEFAULT_API_KEY,
        "regions": ",".join(config["player_props"][sport].get("regions", "us")),  # default to US
        "markets": ",".join(config["player_props"][sport]["markets"]),  # default to US
        "dateFormat": "iso",
        "oddsFormat": "american"
    }

    print("Params: ", params)
    print("URL: ", url)

    print("Events[3]: ", events[3]["id"])

    output_dir = DEFAULT_OUTPUT_DIR + f'/{sport}/player_props/'

    # Make the API request
    # invoke_request(url, params=params, file_name=file_name, output=True, output_dir=output_dir)

def get_player_props(sport):
    # Validate sport
    print(sport)
    sports = sports_endpoint()
    
    flag = False
    for s in sports:
        if s["key"] == sport:
            flag = True
    if not flag:
        print("Sport not found")
        return

    # Get Events for sport
    events = events_endpoint(sport)
    events = add_events_date(events)
    output_dir = DEFAULT_OUTPUT_DIR + f'/{sport}/events_updated/'
    file_name = config["events"]["prefix"].replace("{sport_key}", sport)
    # Construct file path in the current directory
    file_path = os.path.join(output_dir, f"{file_name}_{str(datetime.now().date()).replace('-', '')}.json")
    
    # Save the response to the file
    with open(file_path, "w") as file:
        json.dump(events, file, indent=4)

    print(events)

    # Get Player Props
    player_props_endpoint(sport, events)

def add_events_date(events):
    for event in events:
        # event['commence_time'] ="2024-12-25T17:00:00Z"
        utc_time = datetime.strptime(event['commence_time'], '%Y-%m-%dT%H:%M:%SZ')
        utc_time = utc_time.replace(tzinfo=pytz.UTC)
        eastern = pytz.timezone('US/Eastern')
        est_time = utc_time.astimezone(eastern)
        est_date = est_time.strftime('%Y%m%d')

        event['date'] = est_date

get_player_props("icehockey_nhl")

