from flask import Flask, render_template
import pandas as pd
import os
import argparse
from datetime import datetime
import json

def get_project_root():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
    return project_root

ROOT_DIR = get_project_root()

with open(os.path.join(ROOT_DIR, 'configuration/directories.json')) as f:
    directories = json.load(f)

app = Flask(__name__)

# Set up argument parser
parser = argparse.ArgumentParser(description="Run the Flask app to display CSV data.")
parser.add_argument('--sport', required=True, help='The sport to retrieve player props for')
parser.add_argument('--date', default=datetime.now().date().strftime("%Y%m%d"), help='The date for the data in YYYYMMDD format (default is today)')

args = parser.parse_args()
SPORT = args.sport
DATE = args.date

@app.route("/")
def index():
    csv1_path = os.path.join(ROOT_DIR, directories["aggregated_csvs_output"], SPORT, f"{SPORT}_player_props_{DATE}.csv")
    csv2_path = os.path.join(ROOT_DIR, directories["best_player_props_output"], SPORT, f"{SPORT}_best_player_props_{DATE}.csv")
    
    if not os.path.exists(csv1_path) or not os.path.exists(csv2_path):
        return f"Error: CSV files not found | {csv1_path} and {csv2_path}"
    
    csv1_data = pd.read_csv(csv1_path)
    csv2_data = pd.read_csv(csv2_path)

    columns_to_keep = ['game', 'market', 'description', 'name', 'point']
    columns_to_keep += [col for col in csv1_data.columns if '_price' in col or '_implied_prob_diff' in col or '_dejuice' in col]

    csv1_data = csv1_data[columns_to_keep].round(3)
    csv2_data = csv2_data.round(3)

    return render_template(
        'index.html',
        tables=[
            csv1_data.to_html(index=False, table_id="table1", classes="table table-striped table-bordered"),
            csv2_data.to_html(index=False, table_id="table2", classes="table table-striped table-bordered")
        ],
        titles=['Odds Data', 'Best Bets']
    )

if __name__ == "__main__":
    print(f"Starting Flask server for sport '{SPORT}'...")
    app.run(debug=True)
