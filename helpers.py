import os
import json
import pandas as pd
from PIL import Image
import geopandas as gpd
import folium

# IMPORTANT: This file must NOT contain 'import streamlit as st'

Image.MAX_IMAGE_PIXELS = None

def to_nepali_num(number):
    """Converts an integer or string of digits to Nepali numerals."""
    nepali_digits = {'0': '०', '1': '१', '2': '२', '3': '३', '4': '४', '5': '५', '6': '६', '7': '७', '8': '८', '9': '९'}
    return "".join([nepali_digits[char] for char in str(number)])

def load_content(filepath="dashboard_content.json"):
    """Loads the main JSON content for the dashboard."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_geospatial_data(ward_number):
    """Loads shapefile and CSV data for a given ward."""
    if ward_number is None:
        return None, None
    shapefile_path = f"data/ward_{ward_number}.shp"
    csv_path = f"data/ward_{ward_number}_data.csv"
    if not os.path.exists(shapefile_path) or not os.path.exists(csv_path):
        return None, None
    try:
        gdf_ward = gpd.read_file(shapefile_path)
        df_points = pd.read_csv(csv_path)
        df_points.columns = [col.strip().title() for col in df_points.columns]
        df_points[['Latitude', 'Longitude']] = df_points[['Latitude', 'Longitude']].apply(pd.to_numeric, errors='coerce')
        df_points['Category'] = df_points['Category'].str.strip()
        df_points.dropna(subset=['Latitude', 'Longitude', 'Category'], inplace=True)
        return gdf_ward, df_points
    except Exception as e:
        print(f"ERROR: Could not load geospatial data for Ward {ward_number}. Details: {e}")
        return None, None

def create_folium_map(gdf_ward, df_points, selected_categories, txt):
    """Creates and returns a Folium map object."""
    if gdf_ward is None or gdf_ward.empty:
        return None
        
    gdf_ward_projected = gdf_ward.to_crs(epsg=3857)
    center_projected = gdf_ward_projected.geometry.centroid.iloc[0]
    map_center_point = gpd.GeoSeries([center_projected], crs="EPSG:3857").to_crs(epsg=4326).iloc[0]
    map_center = [map_center_point.y, map_center_point.x]
    
    m = folium.Map(location=map_center, zoom_start=15, tiles="OpenStreetMap")
    folium.GeoJson(gdf_ward, style_function=lambda f: {'fillColor': '#fde047', 'color': 'black', 'weight': 2, 'fillOpacity': 0.2}).add_to(m)
    
    if selected_categories and df_points is not None and not df_points.empty:
        filtered_df = df_points[df_points['Category'].isin(selected_categories)]
        colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue']
        color_map = {cat: colors[i % len(colors)] for i, cat in enumerate(df_points['Category'].unique())}
        for _, row in filtered_df.iterrows():
            cat_en = row['Category']
            display_cat = txt.get('map_categories', {}).get(cat_en, cat_en)
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=f"<b>{display_cat}</b>",
                tooltip=display_cat,
                icon=folium.Icon(color=color_map.get(cat_en, 'gray'), icon='info-sign')
            ).add_to(m)
    return m