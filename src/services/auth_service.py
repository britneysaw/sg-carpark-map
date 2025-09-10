import os
import json
import time
import requests
from dotenv import load_dotenv

# Load environment variables from config file
load_dotenv(dotenv_path='config/config.env')

# OneMap Authentication
EMAIL = os.getenv("ONEMAP_EMAIL")
PASSWORD = os.getenv("ONEMAP_PASSWORD")
TOKEN_URL = "https://www.onemap.gov.sg/api/auth/post/getToken"
TOKEN_CACHE_FILE = os.path.join("config", "token_cache.json")


def fetch_new_onemap_token():
    """Request a new token from OneMap API and cache it."""
    payload = {"email": EMAIL, "password": PASSWORD}
    try:
        response = requests.post(TOKEN_URL, json=payload)
        response.raise_for_status() # checks HTTP response status code
        data = response.json() # converts JSON response body into python dict
        access_token = data.get("access_token")
        expiry_timestamp = int(data.get("expiry_timestamp"))
        # Save token to cache
        with open(TOKEN_CACHE_FILE, "w") as f:
            json.dump({"access_token": access_token, "expiry_timestamp": expiry_timestamp}, f)
        return access_token
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print("Error fetching token:", str(e))
    return None


def get_onemap_token():
    """Return a valid cached OneMap token or request a new one if expired/missing."""
    try:
        with open(TOKEN_CACHE_FILE, "r") as f:
            data = json.load(f)
        # Check if token is still valid using expiry stamp
        if data["expiry_timestamp"] > int(time.time()):
            return data["access_token"]
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        pass  # No valid cache, request new token
    return fetch_new_onemap_token()


# LTA DataMall AccountKey Authentication
def get_account_key():
    """Retrieves LTA_DATAMALL_ACCOUNT_KEY from the config.env file."""
    account_key = os.getenv("LTA_DATAMALL_ACCOUNT_KEY")
    if not account_key:
        raise ValueError("LTA_DATAMALL_ACCOUNT_KEY not found in config.env file.")
    return account_key

# Verify that all authentication works
if __name__ == "__main__":
    token = get_onemap_token()
    print("OneMap Access Token:", token)
    try:
        key = get_account_key()
        print("Account Key:", key)
    except ValueError as e:
        print(f"Error: {e}")