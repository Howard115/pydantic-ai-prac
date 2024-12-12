import folium
import streamlit as st
from geopy.geocoders import Nominatim

from streamlit_folium import st_folium

# Initialize geocoder with a more descriptive user agent
geolocator = Nominatim(user_agent="my_unique_app_name")  # Change to a unique name

# Initialize session state variables if they don't exist
if 'previous_location' not in st.session_state:
    st.session_state.previous_location = ""
if 'latitude' not in st.session_state:
    st.session_state.latitude = 39.949610
if 'longitude' not in st.session_state:
    st.session_state.longitude = -75.150282

# Add a text input for user location
user_location = st.text_input("Enter a location:", "Kaohsiung")  # Default to Kaohsiung

@st.cache_data
def create_map(latitude, longitude, location_name):
    """Create a folium map with a marker for the given coordinates"""
    m = folium.Map(location=[latitude, longitude], zoom_start=16)
    folium.Marker(
        [latitude, longitude], 
        popup=location_name, 
        tooltip=location_name
    ).add_to(m)
    return m

@st.cache_data
def get_location_coordinates(location_name):
    """Get coordinates for a given location name using geocoding"""
    try:
        location = geolocator.geocode(location_name)
        if location:
            return location.latitude, location.longitude
        return None
    except:
        return None

# Only update the map if the location has changed
if user_location != st.session_state.previous_location:
    st.session_state.previous_location = user_location
    
    if user_location:
        coordinates = get_location_coordinates(user_location)
        if coordinates:
            st.session_state.latitude, st.session_state.longitude = coordinates
        else:
            st.error("Location not found. Please try another one.")
            st.session_state.latitude = 39.949610
            st.session_state.longitude = -75.150282
    else:
        st.session_state.latitude = 39.949610
        st.session_state.longitude = -75.150282

# Create and display map using cached function
m = create_map(
    st.session_state.latitude, 
    st.session_state.longitude, 
    user_location
)
st_data = st_folium(m, width=725)