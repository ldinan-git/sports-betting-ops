import os
import requests
import json
from datetime import datetime
import pandas as pd

REQUEST_FLAG = True
# types = ["h2h", "totals", "spreads", "alternate_spreads", "alternate_totals", "team_totals", "player_points", "player_assists", "player_shots_on_goal"]
# types = ["h2h", "totals", "spreads", "alternate_spreads", "alternate_totals", "team_totals"]

def invoke_request_nba(types=[]):
    # API endpoint and your API key
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    api_key = ""

    types = ["h2h", "totals", "spreads"]

    # Define parameters to get all nba games, including player props, for today
    params = {
        "apiKey": api_key,                 # Your API key
        "regions": "us",                   # Only get sportsbooks available in the US
        "markets": ["h2h", "totals", "spreads", "alternate_spreads", "alternate_totals", "team_totals", "player_points", "player_assists", "player_shots_on_goal"],
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
        file_path = os.path.join(output_dir, f"nba_odds_{datetime.now().date().strftime('%Y%m%d')}.json")
        
        # Save the response to the file
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
        print(f"Data saved to {file_path}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def load_data_from_file(file_name):
    try:
        with open(file_name, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"File {file_name} not found.")
        return None

def load_request_data():
    if REQUEST_FLAG:
        data = invoke_request_nba()
    else:
        file_name = f"nba_odds_{datetime.now().date().strftime('%Y%m%d')}.json"
        data = load_data_from_file(file_name)
    
    # Now you can use the data variable
    if data is not None:
        print("Data loaded successfully.")
    else:
        print("Failed to load data.")

    return data

# Function to calculate implied probability from odds
def implied_probability(odds):
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)

# Function to calculate "de-juiced" probabilities to remove the bookmaker's juice
def dejuiced_probabilities(odds1, odds2):
    prob1 = implied_probability(odds1)
    prob2 = implied_probability(odds2)
    
    # Adjust probabilities to remove juice
    total_prob = prob1 + prob2
    return prob1 / total_prob, prob2 / total_prob

data = load_request_data()

# Initialize an empty list to store the data for the DataFrame
rows = []

# Loop through the events
for event in data:
    event_id = event['id']
    sport_title = event['sport_title']
    home_team = event['home_team']
    away_team = event['away_team']
    commence_time = event['commence_time']
    
    # Loop through each bookmaker for this event
    for bookmaker in event['bookmakers']:
        bookmaker_name = bookmaker['title']
        last_update = bookmaker['last_update']
        
        # Loop through each market in this bookmaker
        for market in bookmaker['markets']:
            market_key = market['key']
            market_last_update = market['last_update']
            
            # Loop through each outcome in the market
            for outcome in market['outcomes']:
                outcome_name = outcome['name']
                price = outcome['price']
                point = outcome.get('point', None)  # Some markets have 'point' values (e.g., spreads)
                
                # Calculate implied probability
                implied_prob = implied_probability(price)
                
                # Check for a second outcome in case of a two-outcome market like H2H
                if market_key == "h2h" and len(market['outcomes']) == 2:
                    outcome_2 = market['outcomes'][1]
                    price_2 = outcome_2['price']
                    implied_prob_2 = implied_probability(price_2)
                    
                    # Calculate de-juiced probabilities
                    dejuiced_prob_1, dejuiced_prob_2 = dejuiced_probabilities(price, price_2)
                    
                    # Append the data for the first outcome
                    row = {
                        'event_id': event_id,
                        'sport_title': sport_title,
                        'home_team': home_team,
                        'away_team': away_team,
                        'commence_time': commence_time,
                        'bookmaker': bookmaker_name,
                        'market': market_key,
                        'outcome': outcome_name,
                        'odds': price,
                        'implied_prob': implied_prob,
                        'dejuiced_prob': dejuiced_prob_1
                    }
                    rows.append(row)
                    
                    # Append the data for the second outcome
                    row_2 = {
                        'event_id': event_id,
                        'sport_title': sport_title,
                        'home_team': home_team,
                        'away_team': away_team,
                        'commence_time': commence_time,
                        'bookmaker': bookmaker_name,
                        'market': market_key,
                        'outcome': outcome_2['name'],
                        'odds': price_2,
                        'implied_prob': implied_prob_2,
                        'dejuiced_prob': dejuiced_prob_2
                    }
                    rows.append(row_2)
                
                else:
                    # For markets with a single outcome (like Totals or Spreads)
                    row = {
                        'event_id': event_id,
                        'sport_title': sport_title,
                        'home_team': home_team,
                        'away_team': away_team,
                        'commence_time': commence_time,
                        'bookmaker': bookmaker_name,
                        'market': market_key,
                        'outcome': outcome_name,
                        'odds': price,
                        'implied_prob': implied_prob,
                        'dejuiced_prob': implied_prob  # No adjustment needed for single outcomes
                    }
                    rows.append(row)

# Create the DataFrame
df = pd.DataFrame(rows)

# Pivot the DataFrame to get one column per bookmaker's implied_prob
pivot_df = df.pivot_table(
    index=['event_id', 'sport_title', 'home_team', 'away_team', 'commence_time', 'market', 'outcome'],
    columns='bookmaker',
    values='odds',
    aggfunc='first'
)

# Flatten the multi-level columns (if applicable)
if isinstance(pivot_df.columns, pd.MultiIndex):
    pivot_df.columns = [col[0] for col in pivot_df.columns]

# Reset the index to make the DataFrame easier to view
pivot_df = pivot_df.reset_index()

# Handle missing values
pivot_df = pivot_df.fillna('No Data')  # You can adjust how you handle missing data (e.g., replace with 'No Data' or another placeholder)

# Display the first few rows
print(pivot_df.head())

# Optionally, save to CSV
pivot_df.to_csv(f"nba_odds_aggregated_{datetime.now().date().strftime('%Y%m%d')}.csv", index=False)