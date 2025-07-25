import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import os
from PIL import Image, ImageFile

# --- 1. FIX FOR DecompressionBombError ---
# This line tells the Pillow library to allow loading of very large image files.
# Place this at the top of your script.
Image.MAX_IMAGE_PIXELS = None

# --- 2. PAGE CONFIGURATION ---
st.set_page_config(
    layout="wide",
    page_title="Ward Information Dashboard"
)

# --- 3. DATA & CONTENT DEFINITION ---
# Updated with all four images for each ward. Make sure your file names in the `assets` folder match exactly.
WARD_CONTENT = {
    4: {
        "title": "Information for Ward 4",
        "images": [
            {
                "path": "assets/ward_4_image_1.jpg",
                "caption": "Description for Ward 4, Image 1. This can be about population demographics or a general overview."
            },
            {
                "path": "assets/ward_4_image_2.jpg",
                "caption": "Description for Ward 4, Image 2. This could detail educational facilities or health services."
            },
            {
                "path": "assets/ward_4_image_3.jpg",
                "caption": "Description for Ward 4, Image 3. This might focus on infrastructure and public utilities."
            },
            {
                "path": "assets/ward_4_image_4.jpg", # The map image
                "caption": "Description for Ward 4, Image 4. This is a detailed map view of the ward showing key points of interest."
            }
        ]
    },
    7: {
        "title": "Information for Ward 7",
        "images": [
            {
                "path": "assets/ward_7_image_1.jpg",
                "caption": "Description for Ward 7, Image 1. General overview and demographics for this ward."
            },
            {
                "path": "assets/ward_7_image_2.jpg",
                "caption": "Description for Ward 7, Image 2. Details on key infrastructure."
            },
            {
                "path": "assets/ward_7_image_3.jpg",
                "caption": "Description for Ward 7, Image 3. Information about local economy or environment."
            },
            {
                "path": "assets/ward_7_image_4.jpg",
                "caption": "Description for Ward 7, Image 4. Map view showing points of interest in Ward 7."
            }
        ]
    }
}

# --- 4. HELPER & LAYOUT FUNCTIONS ---

@st.cache_data
def load_shapefile(ward_number):
    """Loads a shapefile for a given ward number."""
    try:
        shapefile_path = f"data/ward_{ward_number}.shp"
        if os.path.exists(shapefile_path):
            gdf = gpd.read_file(shapefile_path)
            return gdf
        else:
            return None
    except Exception as e:
        st.error(f"Error loading shapefile for Ward {ward_number}: {e}")
        return None

def display_ward_4_layout(content):
    """Custom layout function specifically for Ward 4."""
    st.header(content["title"])

    # Create two main columns: a wider one for the left stack, a narrower one for the right image.
    left_col, right_col = st.columns([2, 1.5]) # Adjust ratio as needed

    with right_col:
        # Display Image 4 on the right
        image_4 = content["images"][3]
        if os.path.exists(image_4["path"]):
            image = Image.open(image_4["path"])
            # FIX: Use use_container_width instead of the deprecated use_column_width
            st.image(image, caption="Ward 4 Map", use_container_width=True)
            st.write(image_4["caption"])
        else:
            st.warning(f"Image not found: {image_4['path']}")

    with left_col:
        # Display Images 1, 2, and 3 stacked on the left
        for i in range(3):
            item = content["images"][i]
            if os.path.exists(item["path"]):
                image = Image.open(item["path"])
                st.image(image, use_container_width=True)
                st.write(item["caption"])
                st.markdown("---")
            else:
                st.warning(f"Image not found: {item['path']}")


def display_default_layout(content):
    """A generic layout for any other ward."""
    st.header(content["title"])
    # Create two columns to display images side-by-side
    cols = st.columns(2)
    col_idx = 0
    for item in content["images"]:
        with cols[col_idx]:
            if os.path.exists(item["path"]):
                image = Image.open(item["path"])
                st.image(image, use_container_width=True)
                st.write(item["caption"])
                st.markdown("---")
            else:
                st.warning(f"Image not found: {item['path']}")
        col_idx = (col_idx + 1) % 2 # Alternate between columns 0 and 1

# --- 5. STATE MANAGEMENT ---
if 'selected_ward' not in st.session_state:
    st.session_state.selected_ward = None

# --- 6. HEADER SECTION (Unchanged) ---
header_cols = st.columns([1, 1, 3, 1.5, 1])

with header_cols[0]:
    if os.path.exists("assets/municipality_logo.jpg"):
        st.image("assets/municipality_logo.jpg", width=100)
    else:
        st.markdown("Municipality Logo")

with header_cols[1]:
    if os.path.exists("assets/herd_logo.jpg"):
        st.image("assets/herd_logo.jpg", width=100)
    else:
        st.markdown("Herd Logo")

with header_cols[2]:
    btn_cols = st.columns(4)
    btn_cols[0].button("Health", use_container_width=True)
    btn_cols[1].button("Education", use_container_width=True)
    btn_cols[2].button("Agriculture", use_container_width=True)
    btn_cols[3].button("Environment", use_container_width=True)

with header_cols[3]:
    st.selectbox("Language", ["English", "Nepali"], label_visibility="collapsed")

st.markdown("---")

# --- 7. MAP & CONTROLS SECTION ---
st.header("Ward Map")

ward_options = [4, 7]
current_selection_index = ward_options.index(st.session_state.selected_ward) if st.session_state.selected_ward in ward_options else None

selected_ward_from_dropdown = st.selectbox(
    "Select Ward (from Drop Down)",
    options=ward_options,
    index=current_selection_index,
    placeholder="Choose a ward...",
    key="ward_selector"
)

if selected_ward_from_dropdown and selected_ward_from_dropdown != st.session_state.selected_ward:
    st.session_state.selected_ward = selected_ward_from_dropdown
    st.rerun()

map_center = [27.78, 85.36]
m = folium.Map(location=map_center, zoom_start=13, tiles="OpenStreetMap")

for ward_num in ward_options:
    gdf = load_shapefile(ward_num)
    if gdf is not None:
        style = {'fillColor': '#ffaf00', 'color': 'black', 'weight': 2, 'fillOpacity': 0.4}
        highlight_style = {'fillColor': '#39e600', 'color': 'black', 'weight': 3, 'fillOpacity': 0.7}
        final_style = highlight_style if ward_num == st.session_state.selected_ward else style
        
        folium.GeoJson(
            gdf,
            style_function=lambda x, style=final_style: style,
            tooltip=f"Click to select Ward {ward_num}",
            name=f"ward_{ward_num}"
        ).add_to(m)

map_data = st_folium(m, width='100%', height=400, returned_objects=['last_object_clicked_tooltip'])

# --- INTERACTION LOGIC FIX ---
# This is the crucial part for making the map click work.
if map_data and map_data.get("last_object_clicked_tooltip"):
    tooltip_text = map_data["last_object_clicked_tooltip"]
    try:
        clicked_ward_num = int(tooltip_text.split()[-1])
        if clicked_ward_num != st.session_state.selected_ward:
            st.session_state.selected_ward = clicked_ward_num
            # st.rerun() forces the entire script to run again from the top.
            # This is how Streamlit updates the page with the new selection.
            st.rerun()
    except (ValueError, IndexError):
        pass

st.markdown("---")

# --- 8. CONDITIONAL CONTENT SECTION ---
if st.session_state.selected_ward:
    selected_ward_num = st.session_state.selected_ward
    content = WARD_CONTENT.get(selected_ward_num)

    if content:
        # Call the appropriate layout function based on the selected ward
        if selected_ward_num == 4:
            display_ward_4_layout(content)
        else:
            # Use a default layout for all other wards (e.g., Ward 7)
            display_default_layout(content)
    else:
        st.warning(f"No content has been defined for Ward {selected_ward_num} yet.")
else:
    st.info("Select a ward from the dropdown or by clicking on the map to see details.")