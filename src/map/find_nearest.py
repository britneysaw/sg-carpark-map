import pandas as pd
import folium
import os
import time
from geopy.distance import geodesic
from src.services.map_utils import geocode_onemap_address, get_onemap_walking_distance
from src.api.fetch_data import fetch_and_save_carpark_availability
from src.services.auth_service import get_account_key
from folium.plugins import MarkerCluster, HeatMap

# Config
CARPARK_DATA_FILE = "data/carpark_data.csv"
OUTPUT_FILE = "nearest_carparks_map.html"
LTA_API_URL = "https://datamall2.mytransport.sg/ltaodataservice/CarParkAvailabilityv2"


def create_nearest_carpark_map(carpark_df, destination_coords, destination_address, nearest_df):
    """
    Creates a Folium map showing the destination and the nearest carparks,
    with additional layers for different lot types and a heatmap.

    Args:
        carpark_df (pd.DataFrame): DataFrame containing all carpark data.
        destination_coords (tuple): A tuple (latitude, longitude) of the destination.
        destination_address (str): The address string of the destination.
        nearest_df (pd.DataFrame): DataFrame of the N nearest carparks to highlight.
    
    Returns:
        folium.Map: The generated Folium map object.
    """
    # Data pre-processing: consolidate data by CarParkID
    consolidated_carpark_df = carpark_df.groupby('CarParkID').agg({
        'Development': 'first',
        'latitude': 'first',
        'longitude': 'first',
        'LotType': lambda x: list(x),
        'AvailableLots': lambda x: list(x)
    }).reset_index()

    m = folium.Map(location=destination_coords, zoom_start=14)

    # Add destination marker
    folium.Marker(
        location=destination_coords,
        popup=folium.Popup(f"Your Destination: {destination_address}", parse_html=True),
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(m)

    # Define FeatureGroups and MarkerClusters for each lot type
    car_group = folium.FeatureGroup(name="Car Lots", show=False).add_to(m)
    car_cluster = MarkerCluster().add_to(car_group)

    heavy_vehicle_group = folium.FeatureGroup(name="Heavy Vehicle Lots", show=False).add_to(m)
    heavy_vehicle_cluster = MarkerCluster().add_to(heavy_vehicle_group)
    
    motorcycle_group = folium.FeatureGroup(name="Motorcycle Lots", show=False).add_to(m)
    motorcycle_cluster = MarkerCluster().add_to(motorcycle_group)
    
    other_group = folium.FeatureGroup(name="Other Lots", show=False).add_to(m)
    other_cluster = MarkerCluster().add_to(other_group)

    # Define nearest carparks layer
    nearest_group = folium.FeatureGroup(name="Nearest Carparks").add_to(m)
    nearest_carpark_ids = nearest_df['CarParkID'].unique()

    # Add markers for each carpark using the consolidated DataFrame
    for index, row in consolidated_carpark_df.iterrows():
        try:
            lot_types = row['LotType']
            available_lots_list = row['AvailableLots']
            is_nearest = row['CarParkID'] in nearest_carpark_ids

            # Availability colour logic (based on car lots if available)
            if 'C' in lot_types:
                availability_target = available_lots_list[lot_types.index('C')]
            else:
                availability_target = sum(available_lots_list)
            
            if availability_target > 50:
                availability_color = "green"
            elif availability_target > 10:
                availability_color = "orange"
            else:
                availability_color = "red"
            
            # Icon logic (use 'square-parking' for mixed parking lots, otherwise specific vehicle icon)
            if len(lot_types) > 1:
                icon_to_use = folium.Icon(color=availability_color, icon='square-parking', prefix='fa')
            elif 'C' in lot_types:
                icon_to_use = folium.Icon(color=availability_color, icon='car', prefix='fa')
            elif 'H' in lot_types:
                icon_to_use = folium.Icon(color=availability_color, icon='truck', prefix='fa')
            elif 'Y' in lot_types:
                icon_to_use = folium.Icon(color=availability_color, icon='motorcycle', prefix='fa')
            else:
                icon_to_use = folium.Icon(color=availability_color, icon='question', prefix='fa')
            
            # Prepare the consolidated popup HTML
            popup_html = f"<b>Carpark ID:</b> {row['CarParkID']}<br><b>Address:</b> {row['Development']}<br>"
            for i, lot_type in enumerate(lot_types):
                popup_html += f"<b>Lot Type ({lot_type}):</b> {available_lots_list[i]} lots<br>"
            
            # Add a marker for each cluster
            if 'C' in lot_types:
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=row['CarParkID'],
                    icon=icon_to_use
                ).add_to(car_cluster)
            
            if 'H' in lot_types:
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=row['CarParkID'],
                    icon=icon_to_use
                ).add_to(heavy_vehicle_cluster)
            
            if 'Y' in lot_types:
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=row['CarParkID'],
                    icon=icon_to_use
                ).add_to(motorcycle_cluster)
            
            if not any(lt in lot_types for lt in ['C', 'H', 'Y']):
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=row['CarParkID'],
                    icon=icon_to_use
                ).add_to(other_cluster)

            # Add additional info if it is a nearest carpark by walking
            if is_nearest:
                nearest_row = nearest_df.loc[nearest_df['CarParkID'] == row['CarParkID']].iloc[0]
                popup_html += f"<b>Geodesic Distance:</b> {nearest_row.get('geodesic_distance', 'N/A'):.2f} km<br>"
                popup_html += f"<b>Walking Distance:</b> {nearest_row.get('distance_km', 'N/A'):.2f} km<br>"
                popup_html += f"<b>Walking Duration:</b> {nearest_row.get('duration_minutes', 'N/A'):.0f} min"
                
                # Highlight the nearest carparks with a Circle
                folium.Circle(
                    location=[row['latitude'], row['longitude']],
                    radius=50,
                    color="darkblue",
                    fill=True,
                    fill_color="darkblue",
                    fill_opacity=0.3
                ).add_to(nearest_group)
                
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=row['CarParkID'],
                    icon=icon_to_use
                ).add_to(nearest_group)
        
        except (KeyError, ValueError, TypeError) as e:
            print(f"Skipping row {index} due to missing or invalid data: {e}")
            continue

    # Add a heatmap layer
    heat_data = [[row['latitude'], row['longitude']] for _, row in carpark_df.iterrows()]
    HeatMap(heat_data, radius=15, blur=10, name="Heatmap", show=False).add_to(m)
    
    # Add layer control to toggle layers
    folium.LayerControl().add_to(m)

    # Add custom legend box
    legend_html = """
        <div style="position: fixed; bottom: 20px; right: 10px; z-index:9999; font-size:12px;
                    background-color:white; padding:10px; border-radius:5px; border: 2px solid grey;">
          <b>Carpark Availability</b><br>
          <i style="background:green; width:10px; height:10px; display:inline-block; border-radius:50%;"></i> > 50 lots available<br>
          <i style="background:orange; width:10px; height:10px; display:inline-block; border-radius:50%;"></i> 10-50 lots available<br>
          <i style="background:red; width:10px; height:10px; display:inline-block; border-radius:50%;"></i> < 10 lots available<br>
          <i style="font-size:10px; color:grey;">Colour based on Car lots, before other lot types.<br>(Colour is static and does not change with layers.)</i>
        </div>
        """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m


def find_nearest_carparks(carpark_df, destination_coords, n=10):
    """
    Finds the N nearest carparks based on walking distance.
    
    This function uses a two-stage approach for efficiency:
    1. A fast filter using geodesic (straight-line) distance to find a small pool of candidates.
    2. A more accurate calculation using the OneMap Routing API to find the walking distance
       for each candidate.

    Args:
        carpark_df (pd.DataFrame): DataFrame containing all carpark data.
        destination_coords (tuple): A tuple (latitude, longitude) of the destination.
        n (int): The number of nearest carparks to find and return.

    Returns:
        pd.DataFrame: A DataFrame of the N nearest carparks, sorted by walking distance.
    """
    # Stage 1: Fast filter using geodesic distance
    print("Stage 1: Using geodesic distance to find top 30 candidates...")
    carpark_df['geodesic_distance'] = carpark_df.apply(
        lambda row: geodesic(destination_coords, (row['latitude'], row['longitude'])).kilometers, axis=1
    )
    candidates_df = carpark_df.sort_values('geodesic_distance').head(30) # can be changed to include more candidates
    
    # Stage 2: Calculation using OneMap Routing API
    print("\nStage 2: Calculating walking distance for candidates...")
    results_df = pd.DataFrame(columns=['CarParkID', 'Development', 'latitude', 'longitude', 'distance_km', 'duration_minutes', 'AvailableLots', 'geodesic_distance'])

    candidate_data = candidates_df.to_dict('records')
    
    for i, carpark in enumerate(candidate_data):
        print(f"[{i+1}/{len(candidate_data)}] Calculating route for {carpark['CarParkID']}...")
        end_coords = (carpark['latitude'], carpark['longitude'])
        
        walking_distance, duration_minutes = get_onemap_walking_distance(destination_coords, end_coords)
        
        if walking_distance is not None:
            carpark['distance_km'] = walking_distance
            carpark['duration_minutes'] = duration_minutes
            results_df.loc[len(results_df)] = carpark
        
        time.sleep(0.1)

    nearest_df = results_df.sort_values('distance_km').head(n)
    
    print(f"\nFound top {n} nearest carparks based on walking distance:")
    print(nearest_df[['CarParkID', 'Development', 'geodesic_distance', 'distance_km', 'duration_minutes', 'AvailableLots']])
    
    return nearest_df


def main():
    """
    Main function to find nearest carpark and create map.
    """
    destination = input("Enter a destination address in Singapore (e.g., 'Raffles Place'): ")
    if not destination:
        print("No destination entered. Exiting.")
        return
    
    destination_coords = geocode_onemap_address(destination)
    if not destination_coords[0] or not destination_coords[1]:
        print("Could not geocode the destination. Exiting.")
        return

    if not os.path.exists(CARPARK_DATA_FILE):
        print("Carpark data not found. Fetching now...")
        try:
            account_key = get_account_key()
            fetch_and_save_carpark_availability(LTA_API_URL, account_key, CARPARK_DATA_FILE)
        except ValueError as e:
            print(f"Error: {e}. Cannot proceed.")
            return

    num_carparks_input = input("How many nearest carparks to find? (Enter a number less than 30, default is 10): ")
    try:
        num_carparks = int(num_carparks_input) if num_carparks_input else 10
        if num_carparks < 1:
            print("Invalid number. Defaulting to 10.")
            num_carparks = 10
    except ValueError:
        print("Invalid input. Defaulting to 10.")
        num_carparks = 10

    carpark_df = pd.read_csv(CARPARK_DATA_FILE)
    carpark_df.dropna(subset=['latitude', 'longitude'], inplace=True)
    
    nearest_df = find_nearest_carparks(carpark_df, destination_coords, n=num_carparks)

    if not nearest_df.empty:
        print("\nGenerating map with nearest carparks...")
        folium_map = create_nearest_carpark_map(carpark_df, destination_coords, destination, nearest_df)
        folium_map.save(OUTPUT_FILE)
        print(f"Map saved to '{OUTPUT_FILE}'. Open this file in your browser to view the map.")
    else:
        print("No nearest carparks could be determined. Map not generated.")

if __name__ == "__main__":
    main()