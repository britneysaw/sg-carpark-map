# Singapore Carpark Availability Map

This project creates a map of carpark availability across Singapore, using data from LTA DataMall and the OneMap API.


## Features

- **Data Fetching:** Fetches carpark availability data from LTA DataMall.
- **Interactive Map:** Displays carparks on a map using the Folium library.
- **Togglable Layers:** Allows you to filter and view carparks by specific lot types (e.g., cars, motorcycles, heavy vehicles).
- **Location Search:** Finds the nearest carparks to a user-input destination address using the OneMap API.

## Directory
```
.  
├── LICENSE  
├── README.md  
├── sample_output # Sample output files for the carpark maps.
│   ├── carpark_map.html 
│   ├── nearest_carparks_map.html
├── config
│   ├── config.env # Contains API keys.
│   └── token_cache.json # Auto-generated file to cache OneMap access tokens.
├── data
│   └── carpark_data.csv
├── requirements.txt
└── src
    ├── api
    │   └── fetch_data.py # Script to fetch data from LTA DataMall.
    ├── map
    │   ├── create_map.py # Script to create map.
    │   └── find_nearest.py # Script to find nearest carparks and display them on a map.
    └── services
        ├── auth_service.py # Handles authentication for OneMap and LTA APIs.
        └── map_utils.py # Geocoding and routing utilities.
```

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/britneysaw/sg-carpark-map.git
    cd sg-carpark-map
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure API Keys:**
    -   Obtain your API keys from [LTA DataMall](https://datamall.lta.gov.sg/content/datamall/en.html) and [OneMap](https://www.onemap.gov.sg/apidocs/).
    -   Create a `config/config.env` file and add your credentials in the following format:
        ```env
        LTA_DATAMALL_ACCOUNT_KEY=your_lta_datamall_api_key
        ONEMAP_EMAIL=your_onemap_email
        ONEMAP_PASSWORD=your_onemap_password
        ```

## Usage
Ensure that you are in your project root directory.

1. **Fetch the data**  
    Download carpark data from LTA and save it as a CSV (repeat when you need updated data).
    ```bash
    python -m src.api.fetch_data
    ```

2. **Choose a workflow**  
    **A) Explore the Carpark Map**  
    Generates an interactive map of all carparks with togglable layers and a heatmap.  
    ```bash
    python -m src.map.create_map
    ```
    The generated map will be saved as `carpark_map.html` in your project's root directory.

    **B) Find Nearest Carparks**  
    Uses geocoding to find carparks closest to a given address.  
    ```bash
    python -m src.map.find_nearest
    ```
    The script will prompt for an address and number of carparks to find.  
    The generated map will be saved as `nearest_carparks_map.html` in your project's root directory.

Open the saved html files in your web browser to view the maps.

## Data & API Attribution
This project uses data and services from **LTA DataMall** and **OneMap**, made available under the terms of the Singapore Open Data Licence version 1.0.