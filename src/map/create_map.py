import folium
from folium.plugins import MarkerCluster, HeatMap
import pandas as pd
import os

# Config
DATA_FILE = "data/carpark_data.csv"
OUTPUT_FILE = "carpark_map.html"

def load_data(filepath):
    """
    Loads carpark data from a CSV file into a pandas DataFrame.
    """
    if not os.path.exists(filepath):
        print(f"Error: The data file '{filepath}' was not found.")
        print("Please run 'python -m src.api.fetch_data' first to generate the data.")
        return None
    try:
        df = pd.read_csv(filepath)
        print(f"Successfully loaded {len(df)} records from '{filepath}'.")
        return df
    except Exception as e:
        print(f"Error loading data from '{filepath}': {e}")
        return None

def create_carpark_map(carpark_df):
    """
    Creates a Folium map showing carpark availability, with layers for different lot types.
    
    Args:
        carpark_df (pd.DataFrame): DataFrame containing carpark data.
    
    Returns:
        folium.Map: The generated Folium map object.
    """
    # Data pre-processing: consolidate data by CarParkID
    consolidated_df = carpark_df.groupby('CarParkID').agg({
        'Development': 'first',
        'latitude': 'first',
        'longitude': 'first',
        'LotType': lambda x: list(x),
        'AvailableLots': lambda x: list(x)
    }).reset_index()

    m = folium.Map(location=[1.3521, 103.8198], zoom_start=12)

    # Define FeatureGroups and MarkerClusters for each lot type
    car_group = folium.FeatureGroup(name="Car Lots").add_to(m)
    car_cluster = MarkerCluster().add_to(car_group)

    heavy_vehicle_group = folium.FeatureGroup(name="Heavy Vehicle Lots").add_to(m)
    heavy_vehicle_cluster = MarkerCluster().add_to(heavy_vehicle_group)
    
    motorcycle_group = folium.FeatureGroup(name="Motorcycle Lots").add_to(m)
    motorcycle_cluster = MarkerCluster().add_to(motorcycle_group)
    
    other_group = folium.FeatureGroup(name="Other Lots").add_to(m)
    other_cluster = MarkerCluster().add_to(other_group)

    # Add markers for each carpark using the consolidated DataFrame
    for index, row in consolidated_df.iterrows():
        try:
            lot_types = row['LotType']
            available_lots_list = row['AvailableLots']
            
            # Availability colour logic (based on car lots if available)
            if 'C' in lot_types:
                car_lots_index = lot_types.index('C')
                availability_target = available_lots_list[car_lots_index]
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


def main():
    """
    Main function to load data and create the map.
    """
    print("Loading carpark data from CSV...")
    carpark_df = load_data(DATA_FILE)
    
    if carpark_df is not None:
        print("Creating the interactive map...")
        folium_map = create_carpark_map(carpark_df)
        
        folium_map.save(OUTPUT_FILE)
        print(f"Map saved successfully as '{OUTPUT_FILE}'.")
        print("Open this file in your browser to view the map.")
    else:
        print("Map generation aborted due to data loading failure.")

if __name__ == "__main__":
    main()