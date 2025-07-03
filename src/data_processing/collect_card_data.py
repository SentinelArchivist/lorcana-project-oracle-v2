import requests
import pandas as pd
import json
from src.data_processing.ability_parser import parse_abilities
from src.data_processing.ability_transformer import transform_abilities
import os

def fetch_lorcana_data(output_path: str = 'data/processed/lorcana_card_master_dataset.csv') -> pd.DataFrame:
    """
    Fetches the complete Disney Lorcana card database from lorcana-api.com,
    processes it into a pandas DataFrame, saves it, and returns the DataFrame.

    Args:
        output_path: The path to save the resulting CSV file.

    Returns:
        A pandas DataFrame containing the processed card data.

    Raises:
        RuntimeError: If the API request fails, the response is not valid JSON,
                      or the data format is unexpected.
    """
    api_url = "https://api.lorcana-api.com/cards/all"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        cards_data = response.json()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"API request failed: {e}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError("Failed to decode JSON from response.") from e

    if not isinstance(cards_data, list):
        raise RuntimeError("API response is not in the expected list format.")

    # The API response includes unwanted columns like 'Image' and 'Artist'.
    # We also want to flatten the 'Classifications' list.
    df = pd.DataFrame(cards_data)
    
    # Drop columns that are not needed for the simulation engine
    cols_to_drop = ['Image', 'Artist', 'Flavor']
    df = df.drop(columns=[col for col in cols_to_drop if col in df.columns])

    # The 'Classifications' field is a list; we only care about the first element.
    if 'Classifications' in df.columns:
        df['Classification'] = df['Classifications'].apply(lambda x: x[0] if isinstance(x, list) and x else None)
        df = df.drop(columns=['Classifications'])

    # --- Ability Parsing & Transformation ---
    # If 'Abilities' column exists, parse it, then transform it into the canonical schema.
    if 'Abilities' in df.columns:
        # Fill NaN with empty strings to prevent errors in the parser.
        df['Abilities'] = df['Abilities'].fillna('')

        # Step 1: Parse raw ability strings into structured Python objects.
        parsed_abilities = df['Abilities'].apply(parse_abilities)

        # Step 2: Transform the parsed abilities into the canonical schema.
        schema_abilities = parsed_abilities.apply(transform_abilities)

        # Step 3: Store the results as JSON strings in new columns.
        df['parsed_abilities'] = parsed_abilities.apply(json.dumps)
        df['schema_abilities'] = schema_abilities.apply(json.dumps)

        # Drop the original raw 'Abilities' column as it is now redundant.
        df = df.drop(columns=['Abilities'])

    # Ensure the output directory exists before saving the file.
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)

    try:
        df.to_csv(output_path, index=False, encoding='utf-8')
    except IOError as e:
        raise RuntimeError(f"Failed to save DataFrame to CSV at {output_path}: {e}") from e

    return df

if __name__ == "__main__":
    print("Starting card data fetch...")
    try:
        processed_df = fetch_lorcana_data()
        print(f"Successfully fetched and processed {len(processed_df)} cards.")
        print(f"Master dataset saved to 'data/processed/lorcana_card_master_dataset.csv'.")
    except RuntimeError as e:
        print(f"An error occurred: {e}")

