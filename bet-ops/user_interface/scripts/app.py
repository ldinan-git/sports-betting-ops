from flask import Flask, render_template
import pandas as pd
import os
import argparse
from datetime import datetime

app = Flask(__name__)

# Set up argument parser
parser = argparse.ArgumentParser(description="Run the Flask app to display CSV data.")
parser.add_argument('--sport', required=True, help='The sport to retrieve player props for')
parser.add_argument('--date', default=datetime.now().date().strftime("%Y%m%d"), help='The date for the data in YYYYMMDD format (default is today)')

# Parse the arguments
args = parser.parse_args()

# Get the sport and date parameters from the command-line arguments
SPORT = args.sport
DATE = args.date

# Base directory for your CSV files
BASE_DIR = os.path.join("..", "..", "aggregated_csvs", "output")

@app.route("/")
def index():
    # Construct paths to the CSV files
    csv1_path = os.path.join(BASE_DIR, "aggregated_csvs", SPORT, f"{SPORT}_player_props_{DATE}.csv")
    csv2_path = os.path.join(BASE_DIR, "best_player_props", SPORT, f"{SPORT}_best_player_props_{DATE}.csv")
    
    # Check if the files exist
    if not os.path.exists(csv1_path) or not os.path.exists(csv2_path):
        return f"CSV files for sport '{SPORT}' not found.", 404
    
    # Load the CSVs into pandas DataFrames
    csv1_data = pd.read_csv(csv1_path)
    csv2_data = pd.read_csv(csv2_path)

    csv1_data = csv1_data.round(2)
    csv2_data = csv2_data.round(2)

    # Pass the data to the template for display
    return render_template('index.html', tables=[csv1_data.to_html(classes='table table-striped', index=False),
                                                 csv2_data.to_html(classes='table table-striped', index=False)],
                           titles=['Odds Data', 'Best Bets'])
if __name__ == "__main__":
    print(f"Starting Flask server for sport '{SPORT}'...")
    app.run(debug=True)
