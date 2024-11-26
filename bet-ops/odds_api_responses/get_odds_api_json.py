import os
import requests
import json
from datetime import datetime

output_dir = '.'

def sports_endpoint():
    # API endpoint and your API key
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    api_key = ""

    # Define parameters to get all NHL games, including player props, for today
    params = {
        "apiKey": api_key,                 # Your API key
        "regions": "us",                   # Only get sportsbooks available in the US
        "markets": "h2h,totals,spreads",  # Include player props
        "oddsFormat": "american",          # Odds in American format
        "dateFormat": "iso",               # Date format in ISO 8601
    }

    # Save JSON to the current directory
    output_dir = "."  # Current directory
    os.makedirs(output_dir, exist_ok=True)  # Ensure the directory exists (not strictly needed here)

    # Make the API request
    response = requests.get(url, params=params)

    # Check if the response is successful
    if response.status_code == 200:
        data = response.json()  # Parse JSON response
        
        # Construct file path in the current directory
        file_path = os.path.join(output_dir, f"nba_odds_{datetime.now().date()}.json")
        
        # Save the response to the file
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
        print(f"Data saved to {file_path}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def events_endpoint():
    # get events
    api_key = ""
    
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/events"

    # Define parameters to get all NHL games, including player props, for today
    params = {
        "apiKey": api_key,
        "dateFormat": "iso",

    }

    # Make the API request
    response = requests.get(url, params=params)

    output_dir = '.'

    # Check if the response is successful
    if response.status_code == 200:
        data = response.json()  # Parse JSON response

        print(data)
        
        # Construct file path in the current directory
        file_path = os.path.join(output_dir, f"events_{datetime.now().date()}.json")
        
        # Save the response to the file
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
        print(f"Data saved to {file_path}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

    event = response.json()[0]

    event_id = event['id']
    sport_key = event['sport_key']

    # API endpoint and your API key
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/events/{event_id}/odds"
    print(url)
    # Define parameters to get all NHL games, including player props, for today
    params = {
        "apiKey": api_key,                 # Your API key
        "regions": "us",                   # Only get sportsbooks available in the US
        "markets": "player_points,player_assists,player_rebounds,player_steals,player_blocks,player_triple_double",  # Include player props
        "oddsFormat": "american",          # Odds in American format
        "dateFormat": "iso",               # Date format in ISO 8601
    }

    # Save JSON to the current directory
    output_dir = "."  # Current directory
    os.makedirs(output_dir, exist_ok=True)  # Ensure the directory exists (not strictly needed here)

    # Make the API request
    response = requests.get(url, params=params)

    # Check if the response is successful
    if response.status_code == 200:
        data = response.json()  # Parse JSON response
        
        # Construct file path in the current directory
        file_path = os.path.join(output_dir, f"nba_odds_player_props_{datetime.now().date()}.json")
        
        # Save the response to the file
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
        print(f"Data saved to {file_path}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

events_endpoint()

