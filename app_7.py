import streamlit as st
import os
import json
import pandas as pd
from PIL import Image
import geopandas as gpd
import folium
from streamlit_folium import st_folium

Image.MAX_IMAGE_PIXELS = None

def to_nepali_num(number):
    nepali_digits = {'0': '०', '1': '१', '2': '२', '3': '३', '4': '४', '5': '५', '6': '६', '7': '७', '8': '८', '9': '९'}
    return "".join([nepali_digits[char] for char in str(number)])

TEXT = {
    'en': {'dashboard_title': "Municipal Ward Dashboard", 'dashboard_subtitle': "A unified platform for ward-level statistics and social mapping.", 'controls_header': "Dashboard Controls", 'select_ward': "Select a Ward", 'choose_ward': "Choose a ward...", 'view_ward_button': "Update Dashboard", 'map_layers': "Map Layers", 'select_points': "Select points to display on map:", 'choose_options': "Choose options", 'dashboard_info': "Select options and click 'Update Dashboard' to refresh.", 'welcome_message': "## Welcome! Please select a ward and click 'Update Dashboard' to begin.", 'ward_profile_title': "Profile of Ward {ward}", 'social_map_header': "", 'geodata_error': "Geospatial data for Ward {ward} could not be loaded.", 'profile_summary_header': "Ward Profile Summary", 'no_sector_data': "No sector-specific information is available for this sector.", 'infographics_header': "📊 Social Mapping", 'caption_unavailable': "No description available.", 'image_not_found': "Image not found at path: {path}", 'selected_points_header': "Total Counts for Selected Points"},
    'ne': {'dashboard_title': "नगरपालिका वार्ड ड्यासबोर्ड", 'dashboard_subtitle': "वार्ड-स्तरीय तथ्याङ्क र सामाजिक नक्साङ्कनको लागि एक एकीकृत प्लेटफर्म।", 'controls_header': "ड्यासबोर्ड नियन्त्रणहरू", 'select_ward': "वडा छान्नुहोस्", 'choose_ward': "एउटा वडा छान्नुहोस्...", 'view_ward_button': "ड्यासबोर्ड अपडेट गर्नुहोस्", 'map_layers': "नक्सा तहहरू", 'select_points': "नक्सामा देखाउन अंकहरू चयन गर्नुहोस्:", 'choose_options': "विकल्पहरू छान्नुहोस्", 'dashboard_info': "विकल्पहरू चयन गर्नुहोस् र ताजा गर्न 'ड्यासबोर्ड अपडेट गर्नुहोस्' मा क्लिक गर्नुहोस्।", 'welcome_message': "## स्वागत छ! कृपया सुरु गर्न साइडबारबाट एउटा वडा छान्नुहोस् र 'ड्यासबोर्ड अपडेट गर्नुहोस्' मा क्लिक गर्नुहोस्।", 'ward_profile_title': "वडा {ward} को प्रोफाइल", 'social_map_header': "", 'geodata_error': "वडा {ward} को लागि भौगोलिक डाटा लोड गर्न सकिएन।", 'profile_summary_header': "नगरपालिकाको साखा महासखा", 'no_sector_data': "यस क्षेत्रका लागि कुनै क्षेत्र-विशेष जानकारी उपलब्ध छैन।", 'infographics_header': "📊 सामाजिक नक्साङ्कन", 'caption_unavailable': "कुनै विवरण उपलब्ध छैन।", 'image_not_found': "पथमा छवि फेला परेन: {path}", 'selected_points_header': "चयन गरिएका अंकहरूको कुल गणना", 'sectors': {'Health': 'स्वास्थ्य', 'Education': 'शिक्षा', 'Agriculture': 'कृषि', 'Environment': 'वातावरण', 'Infrastructure': 'पूर्वाधार', 'Women & Child': 'महिला र बालबालिका', 'Disaster': 'विपद्', 'Economic Development': 'आर्थिक विकास', 'Urban Development': 'शहरी विकास', 'Civil Registration': 'नागरिक दर्ता', 'Planning & Monitoring': 'योजना र अनुगमन'}, 'map_categories': {'Animal Farm': 'पशु फार्म', 'Apartments/Housing': 'अपार्टमेन्ट/आवास', 'Bank': 'बैंक', 'Blue spaces (rivers, lakes, pond)': 'नीलो क्षेत्र (नदी, ताल, पोखरी)', 'Bridge': 'पुल', 'Business': 'व्यापार', 'Construction Sites': 'निर्माण स्थल', 'Dumping Sites': 'फोहोर फाल्ने ठाउँ', 'Educational Institute': 'शैक्षिक संस्थान', 'Farm for crops': 'खेती फार्म', 'Government Health Facility': 'सरकारी स्वास्थ्य सुविधा', 'Government office': 'सरकारी कार्यालय', 'Green Space': 'हरियो क्षेत्र', 'Industry/Factory': 'उद्योग/कारखाना', 'Liquor Shops': 'रक्सी पसल', 'Mart (eg. BigMart, KKMart, Salesberry)': 'मार्ट (उदाहरण: बिग मार्ट, केके मार्ट)', 'Meat Shops': 'मासु पसल', 'NGO/INGOs/Private Office': 'गैर-सरकारी/निजी कार्यालय', 'Open Space': 'खुला ठाउँ', 'Petrol Pump': 'पेट्रोल पम्प', 'Pharmacy/Private Clinic/NGO Clinic': 'फार्मेसी/निजी क्लिनिक', 'Police Station': 'प्रहरी चौकी', 'Private Hospital/NGO Hospital': 'निजी अस्पताल', 'Public Transporation Stand': 'सार्वजनिक यातायात स्ट्यान्ड', 'Public Water Sources (Tap water, Well, Dhunge dhara, tube wellPub)': 'सार्वजनिक पानीको स्रोत', 'Recreation Center': 'मनोरन्जन केन्द्र', 'Rehabilitation center': 'पुनर्स्थापना केन्द्र', 'Religious Place': 'धार्मिक स्थल', 'Residential': 'आवासीय', 'Residential Institution': 'आवासीय संस्था', 'Risk Zone (Man hole, open wires, accident prone areas': 'जोखिम क्षेत्र (म्यानहोल, खुला तार)', 'Slum areas': 'सुकुम्बासी क्षेत्र'}}
}

st.set_page_config(layout="wide", page_title="Ward Information Dashboard", page_icon="🗺️")

@st.cache_data
def load_content(filepath="dashboard_content.json"):
    with open(filepath, 'r', encoding='utf-8') as f: return json.load(f)

@st.cache_data
def load_geospatial_data(ward_number):
    if ward_number is None: return None, None
    shapefile_path, csv_path = f"data/ward_{ward_number}.shp", f"data/ward_{ward_number}_data.csv"
    if not os.path.exists(shapefile_path) or not os.path.exists(csv_path): return None, None
    try:
        gdf_ward, df_points = gpd.read_file(shapefile_path), pd.read_csv(csv_path)
        df_points.columns = [col.strip().title() for col in df_points.columns]
        df_points[['Latitude', 'Longitude']] = df_points[['Latitude', 'Longitude']].apply(pd.to_numeric, errors='coerce')
        df_points['Category'] = df_points['Category'].str.strip()
        df_points.dropna(subset=['Latitude', 'Longitude', 'Category'], inplace=True)
        return gdf_ward, df_points
    except Exception as e:
        st.error(f"Error loading geospatial data for Ward {ward_number}: {e}")
        return None, None

def display_infographics(images, txt):
    if not images: return
    st.markdown("---"); st.subheader(txt['infographics_header'])
    for item in images:
        if os.path.exists(item["path"]):
            image = Image.open(item["path"])
            caption_text = item.get('caption', {}).get(st.session_state.lang, txt['caption_unavailable'])
            width = item.get("width")
            if width: st.image(image, width=width, caption=f"*{caption_text}*")
            else: st.image(image, use_container_width=True, caption=f"*{caption_text}*")
            st.markdown("---")
        else: st.warning(txt['image_not_found'].format(path=item['path']))

def display_sector_content(sector_data, txt): pass

def create_folium_map(gdf_ward, df_points, selected_categories, txt):
    if gdf_ward is None or gdf_ward.empty: return None
    gdf_ward_projected = gdf_ward.to_crs(epsg=3857)
    center_projected = gdf_ward_projected.geometry.centroid.iloc[0]
    map_center_point = gpd.GeoSeries([center_projected], crs="EPSG:3857").to_crs(epsg=4326).iloc[0]
    m = folium.Map(location=[map_center_point.y, map_center_point.x], zoom_start=15, tiles="OpenStreetMap")
    folium.GeoJson(gdf_ward, style_function=lambda f: {'fillColor': '#fde047', 'color': 'black', 'weight': 2, 'fillOpacity': 0.2}).add_to(m)
    if selected_categories and df_points is not None and not df_points.empty:
        filtered_df = df_points[df_points['Category'].isin(selected_categories)]
        colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue']
        color_map = {cat: colors[i % len(colors)] for i, cat in enumerate(df_points['Category'].unique())}
        for _, row in filtered_df.iterrows():
            cat_en = row['Category']
            display_cat = txt.get('map_categories', {}).get(cat_en, cat_en)
            folium.Marker(location=[row['Latitude'], row['Longitude']], popup=f"<b>{display_cat}</b>", tooltip=display_cat, icon=folium.Icon(color=color_map.get(cat_en, 'gray'), icon='info-sign')).add_to(m)
    return m

# --- SESSION STATE INITIALIZATION FOR THE FORM PATTERN ---
if 'lang' not in st.session_state: st.session_state.lang = 'en'
if 'pending_lang' not in st.session_state: st.session_state.pending_lang = st.session_state.lang
if 'active_ward' not in st.session_state: st.session_state.active_ward = None
if 'pending_ward' not in st.session_state: st.session_state.pending_ward = None
if 'active_map_categories' not in st.session_state: st.session_state.active_map_categories = []
if 'pending_map_categories' not in st.session_state: st.session_state.pending_map_categories = []

WARD_CONTENT = load_content()
ward_options = list(WARD_CONTENT.keys())
ALL_SECTORS = ['Health', 'Education', 'Agriculture', 'Environment', 'Infrastructure', 'Women & Child', 'Disaster', 'Economic Development', 'Urban Development', 'Civil Registration', 'Planning & Monitoring']
txt = TEXT[st.session_state.lang]

# --- TOP HEADER ---
header_cols = st.columns([3, 1])
with header_cols[0]: st.title(txt['dashboard_title']); st.markdown(txt['dashboard_subtitle'])
with header_cols[1]:
    logo_cols = st.columns(3)
    for i, logo_path in enumerate(["assets/municipality_logo.jpg", "assets/herd_logo.jpg", "assets/kioch_logo.jpg"]):
        if os.path.exists(logo_path): logo_cols[i].image(logo_path, width=100 if i != 1 else 120)
st.markdown("---")

# --- SIDEBAR FORM ---
with st.sidebar:
    st.header(txt['controls_header'])
    st.radio("Language / भाषा", ['en', 'ne'], format_func=lambda x: "English" if x == 'en' else "नेपाली", horizontal=True, key='pending_lang')
    
    current_txt = TEXT[st.session_state.pending_lang]
    def format_ward_options(ward): return f"Ward {ward}" if st.session_state.pending_lang == 'en' else f"{current_txt['select_ward']} {to_nepali_num(ward)}"
    st.selectbox(current_txt['select_ward'], options=ward_options, index=None, placeholder=current_txt['choose_ward'], format_func=format_ward_options, key='pending_ward')

    if st.session_state.pending_ward:
        _, df_points = load_geospatial_data(st.session_state.pending_ward)
        if df_points is not None and not df_points.empty:
            with st.expander(current_txt['map_layers'], expanded=True):
                def format_category_labels(cat): return current_txt.get('map_categories', {}).get(cat, cat)
                st.multiselect(current_txt['select_points'], options=sorted(df_points['Category'].unique()), format_func=format_category_labels, key='pending_map_categories', placeholder=current_txt['choose_options'])

    st.markdown("---")
    if st.button(f"{current_txt['view_ward_button']}", use_container_width=True, type="primary"):
        st.session_state.lang = st.session_state.pending_lang
        st.session_state.active_ward = st.session_state.pending_ward
        st.session_state.active_map_categories = st.session_state.pending_map_categories
    
    st.markdown("---"); st.info(txt['dashboard_info'])

# --- MAIN PANEL DISPLAY ---
if not st.session_state.active_ward:
    st.info(txt['welcome_message'])
else:
    active_ward, active_map_categories = st.session_state.active_ward, st.session_state.active_map_categories
    content = WARD_CONTENT.get(active_ward, {})
    gdf_ward, df_points = load_geospatial_data(active_ward)
    display_ward = to_nepali_num(active_ward) if st.session_state.lang == 'ne' else active_ward
    st.header(txt['ward_profile_title'].format(ward=display_ward))
    st.markdown("---")

    col1, col2 = st.columns([3, 2])
    with col1:
        st.subheader(txt['social_map_header'])
        folium_map = create_folium_map(gdf_ward, df_points, active_map_categories, txt)
        if folium_map: st_folium(folium_map, width='100%', height=500, returned_objects=[])
        
        if active_map_categories and df_points is not None:
            st.markdown(f"#### {txt['selected_points_header']}")
            category_counts = df_points[df_points['Category'].isin(active_map_categories)]['Category'].value_counts()
            metric_cols = st.columns(min(len(category_counts), 4))
            for i, (cat_en, count) in enumerate(category_counts.items()):
                with metric_cols[i % 4]:
                    display_label = txt.get('map_categories', {}).get(cat_en, cat_en)
                    display_value = to_nepali_num(count) if st.session_state.lang == 'ne' else count
                    st.metric(label=display_label, value=display_value)
    with col2:
        st.subheader(txt['profile_summary_header'])
        sectors = content.get("sectors", {})
        sector_tabs = st.tabs([txt.get('sectors', {}).get(s, s) for s in ALL_SECTORS])
        for i, sector_name_en in enumerate(ALL_SECTORS):
            with sector_tabs[i]:
                if sector_name_en in sectors: display_sector_content(sectors[sector_name_en], txt)
                else: st.info(txt['no_sector_data'])
    
    display_infographics(content.get("images", []), txt)
