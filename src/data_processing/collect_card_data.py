import requests
import pandas as pd
import json

def fetch_lorcana_data():
    """
    Fetches the complete Disney Lorcana card database from the lorcana-api.com,
    processes it into a pandas DataFrame, and saves it as a CSV file.
    """
    api_url = "https://api.lorcana-api.com/cards/all"
    output_filename = 'data/processed/lorcana_card_master_dataset.csv'

    print(f"Requesting data from {api_url}...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        print(f"Error: API request failed: {e}")
        return

    print("Data received. Processing JSON response...")
    try:
        # The API returns a list of card objects
        cards_data = response.json()
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON from response.")
        return

    if not isinstance(cards_data, list):
        print("Error: API response is not in the expected format (a list of cards).")
        return

    total_cards_from_api = len(cards_data)
    print(f"Successfully parsed {total_cards_from_api} cards from the API.")

    processed_cards = []
    for card in cards_data:
        # Per instructions, store the raw JSON/string of the 'Abilities' field
        # The key in the API is 'Abilities' and we will create 'Abilities_JSON'
        if 'Abilities' in card:
            card['Abilities_JSON'] = json.dumps(card['Abilities'])
        else:
            card['Abilities_JSON'] = None
        processed_cards.append(card)

    print("Creating pandas DataFrame...")
    df = pd.DataFrame(processed_cards)

    # Verification Step
    print("Verifying data integrity...")
    if len(df) == total_cards_from_api:
        print(f"Verification successful: DataFrame contains {len(df)} rows, matching the {total_cards_from_api} cards from the API.")
    else:
        print(f"Error: Verification failed. DataFrame has {len(df)} rows, but API returned {total_cards_from_api} cards.")
        return

    # Ensure all required columns exist, even if some cards don't have them
    # The DataFrame constructor handles this well, creating NaNs for missing values.

    print(f"Saving data to {output_filename}...")
    try:
        df.to_csv(output_filename, index=False, encoding='utf-8')
        print("Script completed successfully.")
        print(f"Master dataset saved as '{output_filename}'.")
    except Exception as e:
        print(f"Error: Failed to save DataFrame to CSV: {e}")

if __name__ == "__main__":
    fetch_lorcana_data()
