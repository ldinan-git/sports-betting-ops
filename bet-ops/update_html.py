import argparse
import os

def update_date_in_html(sport, new_date):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    index_html_path = os.path.join(script_dir, '..', 'index.html')
    
    # Debugging: Print the path to the index.html file
    print(f"Updating file: {index_html_path}")
    
    with open(index_html_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Split the content on '.csv'
    parts = content.split('.')

    # Iterate over the parts and replace the date
    for i in range(len(parts)):
        if f"{sport}_best_player_props_" in parts[i]:
            print('found')
            parts[i] = parts[i][:-8] + new_date
            print(parts[i])
    
    # Join the parts back together
    updated_content = '.'.join(parts)

    print(updated_content)

    # Write the updated content back to the index.html file
    with open(index_html_path, 'w', encoding='utf-8') as file:
        file.write(updated_content)

    print(f"Date updated successfully for {sport} in index.html")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update the date in the CSV URLs in index.html")
    parser.add_argument('--sport', type=str, required=True, help="The sport to update (e.g., basketball_nba)")
    parser.add_argument('--new_date', type=str, required=True, help="The new date to set (format: YYYYMMDD)")

    args = parser.parse_args()

    update_date_in_html(args.sport, args.new_date)