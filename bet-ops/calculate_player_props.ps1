param(
    [string]$sport,
    [string]$api_key = "",
    [string]$get_odds = "false", # Protect against too many requests
    [string]$override_date = $(Get-Date -Format "yyyyMMdd"), # Default to today's date if not provided
    [string]$file_substring = "",
    [string]$values_populated = "100",
    [string]$bets_shown = "100"
)

# Step 1: Generate odds for a given day
# Use sport = 'basketball_nba', 'icehockey_nhl', 'americanfootball_nfl', 'baseball_mlb'
if ($get_odds.ToLower() -eq "true") {
    python get_player_props.py --sport $sport --api_key $api_key
}

# Step 2: Create Aggregated CSV
# Default Date is today - add --override_date to override in YYYYMMDD format (ex. 202041202)
python calculate_odds_csv.py --sport $sport --file_substring $file_substring

# Step 3: Add Helper Functions to the columns
# custom_market_functions.py is empty for now
python custom_market_functions.py --sport $sport

# Step 4: Data Analysis
# returns the best player props for the day
python best_bets.py --sport $sport --values_populated $values_populated --bets_shown $bets_shown

# Step 5: Spin up the web app
python app.py --sport $sport