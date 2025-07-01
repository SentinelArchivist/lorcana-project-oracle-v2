Persona: Act as an expert principal software architect and data scientist with extensive experience in game theory, trading card game (TCG) analytics, and machine learning. Your goal is to create a comprehensive and actionable development specification for a sophisticated, personal-use application. The user is a passionate TCG player but is not a professional programmer, so all explanations must be clear, concise, and use analogies where possible.

Objective: Execute the foundational data acquisition task for "Project Oracle," as detailed in Stage 1 of the development specification. Your sole task is to produce a master dataset of all Disney Lorcana cards.

Mandatory Requirements:

Programming Language & Libraries: Use Python. You must use the requests library for the API call and the pandas library for data manipulation.

Data Source: You must use the lorcana-api.com public API. Specifically, you will make a single GET request to the /cards/all endpoint to retrieve the complete card database in a single JSON object. Do not use any other data source or method.

Data Processing & Structuring:

Parse the JSON response from the API.

Create a pandas DataFrame to hold the card data.

For every card object returned by the API, create one row in the DataFrame.

Column Mapping:

Every top-level field for a card in the API's JSON response (e.g., Name, Cost, Inkable, Strength, Willpower, Lore, Color, Type, Rarity, Set_Name, Artist, Image, etc.) must be converted into its own column in the DataFrame. The column name must exactly match the API's key for that field.

Crucial - Handling Abilities: Create a specific column named Abilities_JSON. For each card, the value in this column must be the raw, unaltered text of the "Abilities" field from the API's JSON response. This field often contains a JSON array as a string; your task is to ensure this entire string is cleanly placed into the Abilities_JSON column for that row. This preserves the complex, nested ability data in a machine-readable format for later stages. Do not attempt to parse or flatten the abilities into separate columns.

Verification and Integrity Check:

After creating the DataFrame, programmatically verify that the total number of rows in the DataFrame is equal to the total number of cards you received from the API.

Confirm that all data has been ingested correctly and without truncation.

Final Output:

Your final deliverable is a single CSV file.

The file must be named lorcana_card_master_dataset.csv.

The file must be encoded in UTF-8.

The script should save this file to the local directory upon successful completion.

Execute this task. Your final response should be only the complete, runnable Python script that performs these actions.