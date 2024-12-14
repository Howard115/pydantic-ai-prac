import folium
import streamlit as st
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim


def create_location_map(location_name="Kaohsiung", default_lat=39.949610, default_lon=-75.150282):
    """
    Creates an interactive map for a given location using Streamlit and Folium.
    
    Args:
        location_name (str): Name of the location to display on map
        default_lat (float): Default latitude if location not found
        default_lon (float): Default longitude if location not found
    
    Returns:
        dict: Map data from st_folium
    """
    # Initialize geocoder
    geolocator = Nominatim(user_agent="my_unique_app_name")

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
        except Exception:
            return None

    # Get coordinates for the location
    coordinates = get_location_coordinates(location_name)
    
    if coordinates:
        latitude, longitude = coordinates
    else:
        st.error("Location not found. Please try another one.")
        latitude, longitude = default_lat, default_lon

    # Create and display map
    m = create_map(latitude, longitude, location_name)
    st.session_state.map = m
create_location_map("Taipei 101")
st.write(st.session_state.map)
st_folium(st.session_state.map, width=725)

