import re
import argparse

def update_date_in_html(sport, new_date):
    # Read the content of the index.html file
    with open('index.html', 'r', encoding='utf-8') as file:
        content = file.read()

    # Define the pattern to search for and the replacement
    pattern = rf'({sport}_best_player_props_)\d{{8}}(\.csv)'
    replacement = rf'\1{new_date}\2'

    # Update the date in the content
    updated_content = re.sub(pattern, replacement, content)

    # Write the updated content back to the index.html file
    with open('index.html', 'w', encoding='utf-8') as file:
        file.write(updated_content)

    print(f"Date updated successfully for {sport} in index.html")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update the date in the CSV URLs in index.html")
    parser.add_argument('sport', type=str, help="The sport to update (e.g., basketball_nba)")
    parser.add_argument('new_date', type=str, help="The new date to set (format: YYYYMMDD)")

    args = parser.parse_args()

    update_date_in_html(args.sport, args.new_date)