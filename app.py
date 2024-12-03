from flask import Flask, jsonify, send_file
import os
import datetime
import pandas as pd

app = Flask(__name__)

# Path to the directory containing the CSV files (update this path as needed)
CSV_DIRECTORY = 'bet-ops/aggregated_csvs/output/best_player_props'

# Function to find the most recent CSV file and its date
def get_most_recent_csv():
    csv_files = [f for f in os.listdir(CSV_DIRECTORY) if f.endswith('.csv')]
    if not csv_files:
        return None, None

    # Extract date from filenames and find the most recent
    dates = []
    for file in csv_files:
        date_str = file.split('_')[-1].split('.')[0]  # Assumes format like 'icehockey_nhl_best_player_props_20241203.csv'
        try:
            date = datetime.datetime.strptime(date_str, '%Y%m%d')
            dates.append((date, file))
        except ValueError:
            continue  # Skip files with invalid date formats

    # Find the most recent date
    if not dates:
        return None, None

    most_recent_date, most_recent_file = max(dates, key=lambda x: x[0])
    return most_recent_date, most_recent_file

@app.route('/get-recent-csv', methods=['GET'])
def get_recent_csv():
    most_recent_date, most_recent_file = get_most_recent_csv()
    if not most_recent_file:
        return jsonify({'error': 'No CSV files found'}), 404

    file_path = os.path.join(CSV_DIRECTORY, most_recent_file)

    # Send the file content as JSON response
    df = pd.read_csv(file_path)
    data = df.to_dict(orient='records')

    return jsonify({
        'date': most_recent_date.strftime('%Y-%m-%d'),
        'data': data
    })

if __name__ == '__main__':
    app.run(debug=True)
