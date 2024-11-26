import pandas as pd
import json

# Define a function to calculate implied probability
def calculate_implied_probability(odds):
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)

# Define a function to convert American odds to decimal odds
def american_to_decimal(odds):
    if odds > 0:
        return odds / 100 + 1
    else:
        return 100 / abs(odds) + 1
    
# Define a function to calculate implied probability
def calculate_implied_probability(decimal_odds):
    return 1 / decimal_odds

# Define a function to calculate projected odds
def calculate_projected_odds(actual_odds, implied_probability):
    return (actual_odds * (1 - implied_probability)) / (1 - (implied_probability * (1 - (actual_odds / (actual_odds + 100)))))

if __name__ == '__main__':
    # Load the JSON data
    with open('./odds_api_responses/nba_odds_player_props_2024-11-19.json') as f:
        data = json.load(f)

    # Create a list to store the rows of the DataFrame
    rows = []

    bookmakers = []
    points = []

    for bookmaker in data['bookmakers']:
        bookmakers.append(bookmaker['key'])
        for market in bookmaker['markets']:
            for outcome in market['outcomes']:
                row = {
                    'market': market['key'],
                    'description': outcome['description'],
                    'name': outcome['name'],
                    f"{bookmaker['key']}_price": outcome['price'],
                    f"{bookmaker['key']}_point": outcome.get('point', ''),
                    f"{bookmaker['key']}_name": outcome['name']
                }
                rows.append(row)
                points.append(outcome.get('point', ''))

    # Create the DataFrame
    df = pd.DataFrame(rows)

    # Pivot the DataFrame to get one row for each market and description
    new_df = df.pivot_table(index=['market', 'description', 'name'], aggfunc='first').reset_index()

    # Apply the function to each bookmaker's odds
    for bookmaker in new_df.columns:
        if '_price' in bookmaker:
            new_df[f"{bookmaker}_decimal_odds"] = new_df[bookmaker].apply(american_to_decimal)

    # Apply the function to each bookmaker's decimal odds
    for bookmaker in new_df.columns:
        if '_decimal_odds' in bookmaker:
            new_df[f"{bookmaker}_implied_probability"] = new_df[bookmaker].apply(calculate_implied_probability)

    # Reorder the columns of new_df
    new_df = new_df[['market', 'description', 'name'] + sorted([col for col in new_df.columns if col not in ['market', 'description', 'name']])]

    # Write to CSV
    new_df.to_csv('player_props_20241119.csv', index=False)