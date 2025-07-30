import streamlit as st
import os
import json
import pandas as pd
from PIL import Image
import altair as alt

# Geospatial libraries
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from shapely.geometry import Polygon

# This disables the decompression bomb check and allows large images to be processed.
Image.MAX_IMAGE_PIXELS = None

# --- NEW: Helper function to convert numbers to Nepali numerals ---
def to_nepali_num(number):
    nepali_digits = {'0': '०', '1': '१', '2': '२', '3': '३', '4': '४', '5': '५', '6': '६', '7': '७', '8': '८', '9': '९'}
    return "".join([nepali_digits[char] for char in str(number)])

# --- UPDATED: Comprehensive Language Translation Dictionary with new changes ---
TEXT = {
    'en': {
        'dashboard_title': "Municipal Ward Dashboard",
        'dashboard_subtitle': "A unified platform for ward-level statistics and social mapping.",
        'controls_header': "Dashboard Controls",
        'select_ward': "Select a Ward",
        'choose_ward': "Choose a ward...",
        'map_layers': "Map Layers",
        'select_points': "Select points to display on map:",
        'choose_options': "Choose options",
        'dashboard_info': "Select a ward to view its profile, interactive map, and key infographics.",
        'welcome_message': "## Welcome! Please select a ward from the sidebar to begin.",
        'ward_profile_title': "Profile of Ward {ward}",
        'social_map_header': "", # <-- REMOVED TITLE
        'geodata_error': "Geospatial data for Ward {ward} could not be loaded.",
        'profile_summary_header': "Ward Profile Summary",
        'no_sector_data': "No sector-specific information is available for this sector.",
        'infographics_header': "📊 Social Mapping",
        'caption_unavailable': "No description available.",
        'image_not_found': "Image not found at path: {path}",
        'selected_points_header': "Total Counts for Selected Points",
    },
    'ne': {
        'dashboard_title': "नगरपालिका वार्ड ड्यासबोर्ड",
        'dashboard_subtitle': "वार्ड-स्तरीय तथ्याङ्क र सामाजिक नक्साङ्कनको लागि एक एकीकृत प्लेटफर्म।",
        'controls_header': "ड्यासबोर्ड नियन्त्रणहरू",
        'select_ward': "वडा छान्नुहोस्",
        'choose_ward': "एउटा वडा छान्नुहोस्...",
        'map_layers': "नक्सा तहहरू",
        'select_points': "नक्सामा देखाउन अंकहरू चयन गर्नुहोस्:",
        'choose_options': "विकल्पहरू छान्नुहोस्",
        'dashboard_info': "प्रोफाइल, अन्तरक्रियात्मक नक्सा, र मुख्य इन्फोग्राफिक्स हेर्नको लागि साइडबारबाट एउटा वडा छान्नुहोस्।",
        'welcome_message': "## स्वागत छ! कृपया सुरु गर्न साइडबारबाट एउटा वडा छान्नुहोस्।",
        'ward_profile_title': "वडा {ward} को प्रोफाइल",
        'social_map_header': "", # <-- REMOVED TITLE
        'geodata_error': "वडा {ward} को लागि भौगोलिक डाटा लोड गर्न सकिएन।",
        'profile_summary_header': "नगरपालिकाको साखा महासखा", # <-- UPDATED TITLE
        'no_sector_data': "यस क्षेत्रका लागि कुनै क्षेत्र-विशेष जानकारी उपलब्ध छैन।",
        'infographics_header': "📊 सामाजिक नक्साङ्कन", # <-- UPDATED TITLE
        'caption_unavailable': "कुनै विवरण उपलब्ध छैन।",
        'image_not_found': "पथमा छवि फेला परेन: {path}",
        'selected_points_header': "चयन गरिएका अंकहरूको कुल गणना",
        'sectors': {
            'Health': 'स्वास्थ्य', 'Education': 'शिक्षा', 'Agriculture': 'कृषि',
            'Environment': 'वातावरण', 'Infrastructure': 'पूर्वाधार', 'Women & Child': 'महिला र बालबालिका',
            'Disaster': 'विपद्', 'Economic Development': 'आर्थिक विकास', 'Urban Development': 'शहरी विकास',
            'Civil Registration': 'नागरिक दर्ता', 'Planning & Monitoring': 'योजना र अनुगमन'
        },
        'map_categories': {
            'Animal Farm': 'पशु फार्म',
            'Apartments/Housing': 'अपार्टमेन्ट/आवास',
            'Bank': 'बैंक',
            'Blue spaces (rivers, lakes, pond)': 'नीलो क्षेत्र (नदी, ताल, पोखरी)',
            'Bridge': 'पुल',
            'Business': 'व्यापार',
            'Construction Sites': 'निर्माण स्थल',
            'Dumping Sites': 'फोहोर फाल्ने ठाउँ',
            'Educational Institute': 'शैक्षिक संस्थान',
            'Farm for crops': 'खेती फार्म',
            'Government Health Facility': 'सरकारी स्वास्थ्य सुविधा',
            'Government office': 'सरकारी कार्यालय',
            'Green Space': 'हरियो क्षेत्र',
            'Industry/Factory': 'उद्योग/कारखाना',
            'Liquor Shops': 'रक्सी पसल',
            'Mart (eg. BigMart, KKMart, Salesberry)': 'मार्ट (उदाहरण: बिग मार्ट, केके मार्ट)',
            'Meat Shops': 'मासु पसल',
            'NGO/INGOs/Private Office': 'गैर-सरकारी/निजी कार्यालय',
            'Open Space': 'खुला ठाउँ',
            'Petrol Pump': 'पेट्रोल पम्प',
            'Pharmacy/Private Clinic/NGO Clinic': 'फार्मेसी/निजी क्लिनिक',
            'Police Station': 'प्रहरी चौकी',
            'Private Hospital/NGO Hospital': 'निजी अस्पताल',
            'Public Transporation Stand': 'सार्वजनिक यातायात स्ट्यान्ड',
            'Public Water Sources (Tap water, Well, Dhunge dhara, tube wellPub)': 'सार्वजनिक पानीको स्रोत',
            'Recreation Center': 'मनोरन्जन केन्द्र',
            'Rehabilitation center': 'पुनर्स्थापना केन्द्र',
            'Religious Place': 'धार्मिक स्थल',
            'Residential': 'आवासीय',
            'Residential Institution': 'आवासीय संस्था',
            'Risk Zone (Man hole, open wires, accident prone areas': 'जोखिम क्षेत्र (म्यानहोल, खुला तार)',
            'Slum areas': 'सुकुम्बासी क्षेत्र'
        }
    }
}

# --- 1. INITIAL PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Ward Information Dashboard", page_icon="🗺️")

# --- 2. DATA LOADING & CACHING ---
@st.cache_data
def load_content(filepath="dashboard_content.json"):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

@st.cache_data
def load_geospatial_data(ward_number):
    shapefile_path, csv_path = f"data/ward_{ward_number}.shp", f"data/ward_{ward_number}_data.csv"
    if not os.path.exists(shapefile_path) or not os.path.exists(csv_path): return None, None
    try:
        gdf_ward, df_points = gpd.read_file(shapefile_path), pd.read_csv(csv_path)
        df_points.columns = [col.strip().title() for col in df_points.columns]
        for col in ['Latitude', 'Longitude']: df_points[col] = pd.to_numeric(df_points[col], errors='coerce')
        df_points['Category'] = df_points['Category'].str.strip()
        df_points.dropna(subset=['Latitude', 'Longitude', 'Category'], inplace=True)
        return gdf_ward, df_points
    except Exception as e:
        st.error(f"Error loading geospatial data for Ward {ward_number}: {e}")
        return None, None

# --- 3. HELPER & LAYOUT FUNCTIONS ---
def display_infographics(images, txt):
    if not images: return
    st.markdown("---")
    st.subheader(txt['infographics_header'])
    
    lang = st.session_state.lang

    for item in images:
        if os.path.exists(item["path"]):
            image = Image.open(item["path"])
            
            caption_data = item.get('caption', {})
            caption_text = caption_data.get(lang, txt['caption_unavailable'])
            
            manual_width = item.get("width")
            
            if manual_width:
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.image(image, width=manual_width, caption=f"*{caption_text}*")
            else:
                st.image(image, use_container_width=True, caption=f"*{caption_text}*")

            st.markdown("---")
        else:
            st.warning(txt['image_not_found'].format(path=item['path']))

# --- REWRITTEN FUNCTION: SIMPLIFIED SECTOR CONTENT ---
def display_sector_content(sector_data, txt):
    """
    This function is intentionally left blank. As per the user's request,
    no text or content should be displayed within the sector tabs.
    """
    pass # Does nothing

def create_folium_map(gdf_ward, df_points, selected_categories, txt):
    # --- FIX 1: CHECK IF THE GEODATAFRAME IS EMPTY ---
    # If it's empty, we can't calculate a center, so return an empty map or None.
    if gdf_ward.empty:
        # You could return a default map of a wider area, or None
        # Returning None is fine since your calling code already handles this.
        st.warning("The shapefile for this ward is empty and cannot be displayed on the map.")
        return None 

    # --- FIX 2: RE-PROJECT TO A PROJECTED CRS BEFORE CALCULATING CENTROID ---
    # This fixes the UserWarning and gives a more accurate center.
    # We use a common projected CRS (EPSG:3857) for calculations.
    gdf_ward_projected = gdf_ward.to_crs(epsg=3857)
    center_projected = gdf_ward_projected.geometry.centroid.iloc[0]
    
    # Now, convert the calculated center point back to the original CRS (lat/lon) for Folium
    map_center_point = gpd.GeoSeries([center_projected], crs="EPSG:3857").to_crs(epsg=4326).iloc[0]
    map_center = [map_center_point.y, map_center_point.x]

    # The rest of your function remains the same
    m = folium.Map(location=map_center, zoom_start=15, tiles="OpenStreetMap")
    folium.GeoJson(gdf_ward, style_function=lambda f: {'fillColor': '#fde047', 'color': 'black', 'weight': 2, 'fillOpacity': 0.2}).add_to(m)
    
    if selected_categories and not df_points.empty:
        filtered_df = df_points[df_points['Category'].isin(selected_categories)]
        colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue']
        unique_categories = df_points['Category'].unique()
        color_map = {cat: colors[i % len(colors)] for i, cat in enumerate(unique_categories)}
        
        cat_translations = txt.get('map_categories', {})
        
        for _, row in filtered_df.iterrows():
            category_en = row['Category']
            display_category = cat_translations.get(category_en, category_en)
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=f"<b>{display_category}</b>",
                tooltip=display_category,
                icon=folium.Icon(color=color_map.get(category_en, 'gray'), icon='info-sign')
            ).add_to(m)
    return m

# --- 4. SESSION STATE & INITIALIZATION ---
if 'lang' not in st.session_state:
    st.session_state.lang = 'en'

# --- 5. MAIN APP LOGIC ---
WARD_CONTENT = load_content()
ward_options = list(WARD_CONTENT.keys())
ALL_SECTORS = ['Health', 'Education', 'Agriculture', 'Environment', 'Infrastructure', 'Women & Child', 'Disaster', 'Economic Development', 'Urban Development', 'Civil Registration', 'Planning & Monitoring']

# --- SIDEBAR (moved up for language selection to apply globally) ---
with st.sidebar:
    st.header(TEXT['en']['controls_header'] + " / " + TEXT['ne']['controls_header'])
    selected_lang = st.radio("Language / भाषा", ['en', 'ne'], format_func=lambda x: "English" if x == 'en' else "नेपाली", horizontal=True)
    if selected_lang != st.session_state.lang:
        st.session_state.lang = selected_lang
        st.rerun()

txt = TEXT[st.session_state.lang]

# --- TOP HEADER SECTION (Logos) ---
# --- TOP HEADER SECTION (Logos) ---
# Swapped column order and adjusted ratios to give title more space
header_cols = st.columns([3, 1]) 

# Place the title and subtitle in the first (left) wider column
with header_cols[0]:
    st.title(txt['dashboard_title'])
    st.markdown(txt['dashboard_subtitle'])

# Place the logos in the second (right) narrower column
with header_cols[1]:
    # This creates 3 sub-columns inside the right column to space out the logos
    logo_cols = st.columns(3)
    for i, logo_path in enumerate(["assets/municipality_logo.jpg", "assets/herd_logo.jpg", "assets/kioch_logo.jpg"]):
        if os.path.exists(logo_path): 
            logo_cols[i].image(logo_path, width=100 if i != 1 else 120) # Note: The width here is relative to the sub-column

st.markdown("---")

# --- 6. SIDEBAR NAVIGATION (Continued) ---
with st.sidebar:
    def format_ward_options(ward):
        if st.session_state.lang == 'ne':
            return f"{txt['select_ward']} {to_nepali_num(ward)}"
        return f"Ward {ward}"
    
    selected_ward = st.selectbox(txt['select_ward'], options=ward_options, index=None, placeholder=txt['choose_ward'], format_func=format_ward_options)
    
    selected_map_categories = []
    if selected_ward:
        gdf_ward, df_points = load_geospatial_data(selected_ward)
        if df_points is not None and not df_points.empty:
            with st.expander(txt['map_layers'], expanded=True):
                available_categories = sorted(df_points['Category'].unique())
                
                def format_category_labels(cat):
                    return txt.get('map_categories', {}).get(cat, cat)

                selected_map_categories = st.multiselect(
                    txt['select_points'],
                    options=available_categories,
                    placeholder=txt['choose_options'],
                    format_func=format_category_labels
                )
    st.markdown("---")
    st.info(txt['dashboard_info'])

# --- 7. MAIN PANEL DISPLAY ---
if not selected_ward:
    st.info(txt['welcome_message'])
else:
    content = WARD_CONTENT.get(selected_ward, {})
    gdf_ward, df_points = load_geospatial_data(selected_ward)
    
    display_ward = to_nepali_num(selected_ward) if st.session_state.lang == 'ne' else selected_ward
    st.header(txt['ward_profile_title'].format(ward=display_ward))
    
    st.markdown("---")
    col1, col2 = st.columns([3, 2])
    with col1:
        # The subheader that was here has been removed by setting the text to ""
        st.subheader(txt['social_map_header']) 
        if gdf_ward is None:
            st.error(txt['geodata_error'].format(ward=display_ward))
        else:
            folium_map = create_folium_map(gdf_ward, df_points, selected_map_categories, txt)
            st_folium(folium_map, width='100%', height=500, returned_objects=[])

            if selected_map_categories:
                st.markdown(f"#### {txt['selected_points_header']}")
                summary_df = df_points[df_points['Category'].isin(selected_map_categories)]
                category_counts = summary_df['Category'].value_counts()
                metric_cols = st.columns(min(len(category_counts), 4))
                
                cat_translations = txt.get('map_categories', {})
                
                for i, (cat_en, count) in enumerate(category_counts.items()):
                    with metric_cols[i % 4]:
                        display_label = cat_translations.get(cat_en, cat_en)
                        display_value = to_nepali_num(count) if st.session_state.lang == 'ne' else count
                        st.metric(label=display_label, value=display_value)
    with col2:
        st.subheader(txt['profile_summary_header'])
        sectors = content.get("sectors", {})
        
        sector_translations = txt.get('sectors', {})
        tab_titles = [sector_translations.get(s, s) for s in ALL_SECTORS]
        sector_tabs = st.tabs(tab_titles)
        
        for i, sector_name_en in enumerate(ALL_SECTORS):
            with sector_tabs[i]:
                sector_data = sectors.get(sector_name_en)
                if sector_data:
                    # This now calls the new, simplified function
                    display_sector_content(sector_data, txt)
                else:
                    st.info(txt['no_sector_data'])

    display_infographics(content.get("images", []), txt)
