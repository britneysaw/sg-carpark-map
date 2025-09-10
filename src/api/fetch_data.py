import requests
import pandas as pd
import os
from src.services.auth_service import get_account_key

def fetch_and_save_carpark_availability(url, account_key, output_filepath):
    """
    Fetches all records from the LTA carpark availability API using pagination with the $skip parameter
    and saves the consolidated data to a CSV file.
    
    Parameters:
        url (str): The base URL of the API endpoint.
        account_key (str): API account key.
        output_filepath (str): The file path to save the CSV.

    """
    print("Fetching all carpark records from LTA Datamall...")
    
    master_df = pd.DataFrame()
    skip = 0
    records_per_call = 500

    while True:
        try:
            params = {'$skip': skip}
            headers = {'AccountKey': account_key}
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data_dict = response.json()
            records_df = pd.DataFrame(data_dict['value'])
            
            if records_df.empty:
                print(f"No more records. Total records retrieved: {master_df.shape[0]}")
                break
            
            master_df = pd.concat([master_df, records_df], ignore_index=True)
            print(f"Fetched {records_df.shape[0]} records. Total records retrieved: {master_df.shape[0]}")
            
            if records_df.shape[0] < records_per_call:
                break
            
            skip += records_per_call

        except requests.exceptions.RequestException as e:
            print(f"Error during API call: {e}")
            return
    
    if master_df is not None and not master_df.empty:
        # Split the 'Location' column into lat and long
        master_df[['latitude', 'longitude']] = master_df['Location'].str.split(' ', expand=True)
        master_df['latitude'] = pd.to_numeric(master_df['latitude'], errors='coerce')
        master_df['longitude'] = pd.to_numeric(master_df['longitude'], errors='coerce')
        master_df.dropna(subset=['latitude', 'longitude'], inplace=True)
        
        # Save to CSV
        data_dir = os.path.dirname(output_filepath)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        master_df.to_csv(output_filepath, index=False)
        print("\nSuccessfully fetched, cleaned, and saved all data!")
        print(f"Carpark data saved to '{output_filepath}'")
    else:
        print("Carpark data is empty, nothing to save.")

# --- Usage ---
if __name__ == "__main__":
    LTA_API_URL = "https://datamall2.mytransport.sg/ltaodataservice/CarParkAvailabilityv2"
    OUTPUT_FILEPATH = "data/carpark_data.csv"
    
    try:
        account_key = get_account_key()
        fetch_and_save_carpark_availability(LTA_API_URL, account_key, OUTPUT_FILEPATH)
    except ValueError as e:
        print(f"Error: {e}. Please make sure your LTA_DATAMALL_ACCOUNT_KEY is set in the config.env file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")