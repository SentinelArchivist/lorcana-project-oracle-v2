Persona: Act as an expert principal software architect and data scientist. You are methodical, precise, and prioritize data integrity above all else.

Primary Objective: Execute the revised "Stage 1b" of Project Oracle. The original web scraping strategy has been abandoned due to anti-scraping measures. The new task is to parse a local, manually created text file containing metagame decklists, validate every single card against the master card dataset, and output a single, perfectly structured, and validated CSV file.

Context: We have two critical input files in the local directory:

lorcana_card_master_dataset.csv: The complete, validated set of all Lorcana cards (completed in Stage 1a).

2025.07.01-meta-decks.md: A new text file containing a list of "pillar" metagame decks.

Your task is to bridge the data from these two files.

Mandatory Requirements:

Programming Language & Libraries:

Use Python.

You must use the pandas library for data manipulation and validation.

You must use the re (regular expressions) library for robustly parsing the text file.

Input File Handling:

Your script must load and read two files: lorcana_card_master_dataset.csv and 2025.07.01-meta-decks.md.

The script must gracefully handle potential FileNotFoundError exceptions with a clear error message if either file is missing.

Parsing Logic for 2025.07.01-meta-decks.md:

You must process the file line by line.

A line starting with # signifies a new deck. Extract the deck name from this line. The deck name is the text that follows # [Set 8] .

A line formatted as Number<space>Card Name (e.g., 4 Cinderella - Ballroom Sensation) is a card entry. You must use regular expressions to reliably capture the quantity (the number) and the full card name (all text after the space).

Blank or empty lines must be ignored.

Data Structuring:

Initialize an empty list that will store your parsed data.

For each card entry you parse, create a temporary data structure (like a dictionary) containing three keys: DeckName, CardName, and Quantity.

The DeckName for a card should be the last deck name you encountered while parsing.

After parsing the entire file, convert this list of structures into a single pandas DataFrame.

Crucial — Non-Negotiable Data Validation:

This is the most critical step. The integrity of the output file must be guaranteed.

Load Master Card Data: Before parsing the decks, load lorcana_card_master_dataset.csv into a pandas DataFrame. Create a Python set from the Name column for high-performance lookups. This is our validation reference.

Strict Card Name Validation: For every single CardName you parse from the decklist file, you must check if that exact name exists in the validation set of master card names.

Halt on Error: If a parsed card name is NOT found in the master name set, the script's execution MUST STOP IMMEDIATELY. You must print a single, clear, and actionable error message to the console before halting.

Error Message Format: VALIDATION FAILED: Card '{CardName}' from deck '{DeckName}' not found in lorcana_card_master_dataset.csv. Please correct the name in 2025.07.01-meta-decks.md and rerun.

This strict failure condition ensures that no imperfect or erroneous data can be written to the output file.

Final Output & User Verification:

Programmatic Confirmation: If and only if all cards from all decks are successfully validated, the script should print a success summary to the console.

Success Message Format: VALIDATION SUCCESSFUL. Parsed {X} decks, creating a total of {Y} validated card entries. (where X is the number of decks and Y is the total number of rows).

File Creation: After printing the success message, save the final DataFrame to a single CSV file.

Filename: lorcana_metagame_decks.csv

Encoding: UTF-8

Index: Do not include the pandas DataFrame index in the final CSV file.

Simple User Verification Path:

The sole deliverable is the complete, runnable Python script that performs these actions.

To verify success, I (the user) will simply run your Python script.

The verification is a simple two-step process:

I will see the "VALIDATION SUCCESSFUL" message in my terminal.

I will find the lorcana_metagame_decks.csv file in the directory and open it, confident that it contains perfectly structured and validated data, ready for the next stage of the project.