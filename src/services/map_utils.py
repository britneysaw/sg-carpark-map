import requests
from src.services.auth_service import get_onemap_token

def geocode_onemap_address(search_val):
    """
    Geocodes an address using the OneMap API to get its latitude and longitude.
    
    Args:
        search_val (str): The address to geocode.

    Returns:
        tuple: A tuple containing (latitude, longitude) or (None, None) on failure.
    """
    url = "https://www.onemap.gov.sg/api/common/elastic/search"
    params = {
        "searchVal": search_val,
        "returnGeom": "Y",
        "getAddrDetails": "Y"
    }
    
    headers = {
        "Authorization": f"Bearer {get_onemap_token()}"
    }
    
    try:
        print(f"Geocoding address: '{search_val}' using OneMap API...")
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        results = response.json().get('results', [])
        if results:
            first_result = results[0]
            lat = float(first_result.get('LATITUDE'))
            lon = float(first_result.get('LONGITUDE'))
            print(f"Geocoding successful. Coordinates: ({lat}, {lon})")
            return (lat, lon)
        else:
            print(f"No geocoding results found for '{search_val}'.")
            return (None, None)
            
    except requests.exceptions.RequestException as e:
        print(f"Error geocoding address: {e}")
        return (None, None)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return (None, None)
    

def get_onemap_walking_distance(start_coords, end_coords):
    """
    Calculates the walking distance and duration between two points using the
    OneMap Routing API.
    
    Args:
        start_coords (tuple): (latitude, longitude) of the origin.
        end_coords (tuple): (latitude, longitude) of the destination.
        
    Returns:
        tuple: (distance_km, duration_minutes) or (None, None) on failure.
    """
    url = "https://www.onemap.gov.sg/api/public/routingsvc/route"
    
    headers = {
        "Authorization": get_onemap_token()
    }
    params = {
        "start": f"{start_coords[0]},{start_coords[1]}",
        "end": f"{end_coords[0]},{end_coords[1]}",
        "routeType": "walk"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'route_summary' in data:
            distance_meters = data['route_summary']['total_distance']
            duration_seconds = data['route_summary']['total_time']
            return (distance_meters / 1000, duration_seconds / 60)
        else:
            print("OneMap API returned no route. Check if the locations are walkable.")
            return (None, None)
            
    except requests.exceptions.RequestException as e:
        print(f"OneMap Routing API request failed: {e}")
        return (None, None)